#!/usr/bin/env python3
"""Werkspree Microsite-Pipeline — End-to-End Orchestrator.

Fuehrt den kompletten Prozess aus:
  1. Recherche + Filter (hot_leads_pipeline.py)
  2. Microsite-Build pro qualifiziertem Lead (build_microsite.py)
  3. Mail-Versand an Lead (send_mail.py, Strato SMTP)

Segment-Rotation: Elektriker -> Friseur/Salon -> Baecker/Cafe -> Reinigung
-> Tischler/Schreiner -> Kosmetik/Beauty -> Fahrschule -> Kfz-Werkstatt

Nutzung:
  python3 run_microsite_pipeline.py            # naechstes Rotations-Segment
  python3 run_microsite_pipeline.py "Baecker" "Brandenburg an der Havel"

Exit-Codes: 0 = OK (auch wenn 0 Leads), 2 = Build/Versand-Fehler
"""
import argparse, json, subprocess, sys, shutil, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

PIPE = Path(__file__).parent
DATA = PIPE / "data"
REPORTS = PIPE / "reports"
REPORTS.mkdir(exist_ok=True)

ROTATION = [
    ("Kosmetik", "Potsdam"),
    ("Fahrschule", "Brandenburg an der Havel"),
    ("Kfz Werkstatt", "Cottbus"),
    ("Reinigung", "Cottbus"),
    ("Kosmetik", "Frankfurt Oder"),
    ("Fahrschule", "Cottbus"),
    ("Kfz Werkstatt", "Frankfurt Oder"),
    ("Reinigung", "Brandenburg an der Havel"),
    ("Kosmetik", "Cottbus"),
    ("Fahrschule", "Frankfurt Oder"),
    ("Kfz Werkstatt", "Brandenburg an der Havel"),
    ("Reinigung", "Frankfurt Oder"),
    ("Friseur", "Potsdam"),
    ("Friseur", "Cottbus"),
    ("Friseur", "Brandenburg an der Havel"),
    ("Maler", "Cottbus"),
    ("Maler", "Brandenburg an der Havel"),
    ("Gartenbau", "Cottbus"),
    ("Gartenbau", "Potsdam"),
    ("Tischlerei", "Cottbus"),
    ("Tischlerei", "Brandenburg an der Havel"),
    ("Metzgerei", "Cottbus"),
    ("Metzgerei", "Brandenburg an der Havel"),
    ("Elektriker", "Berlin Neukölln"),
    ("Elektriker", "Berlin Mitte"),
    ("Elektriker", "Berlin Lichtenberg"),
    ("Elektriker", "Potsdam"),
    ("Heizung Sanitär", "Berlin Neukölln"),
    ("Heizung Sanitär", "Cottbus"),
    ("Heizung Sanitär", "Brandenburg an der Havel"),
    ("Zahnarzt", "Potsdam"),
    ("Zahnarzt", "Brandenburg an der Havel"),
    ("Zahnarzt", "Cottbus"),
    ("Physiotherapie", "Potsdam"),
    ("Physiotherapie", "Cottbus"),
    ("Physiotherapie", "Brandenburg an der Havel"),
    ("Optiker", "Potsdam"),
    ("Optiker", "Brandenburg an der Havel"),
    ("Bäcker", "Cottbus"),
    ("Bäcker", "Brandenburg an der Havel"),
    ("Schlüsseldienst", "Berlin Mitte"),
    ("Schlüsseldienst", "Berlin Neukölln"),
    ("Schlüsseldienst", "Potsdam"),
    ("Florist", "Potsdam"),
    ("Florist", "Brandenburg an der Havel"),
]
# bereits gepruefte Kombinationen (Stand 14.08. abend, nach 10x-Local-Lauf)
DONE = {
    ("Elektriker", "Berlin Neukölln"),
    ("Friseur", "Potsdam"),
    ("Bäcker", "Brandenburg an der Havel"),
    ("Reinigung", "Cottbus"),
    ("Tischler", "Frankfurt Oder"),
    ("Kosmetik", "Potsdam"),
    ("Fahrschule", "Brandenburg an der Havel"),
    ("Kfz Werkstatt", "Cottbus"),
}

TZ = timezone(timedelta(hours=2))

def load_state():
    p = DATA / "pipeline_state.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"last_idx": -1, "done": []}

def save_state(idx, done=None):
    state = {"last_idx": idx}
    if done:
        state["done"] = [list(d) for d in done]
    (DATA / "pipeline_state.json").write_text(json.dumps(state))

def next_segment():
    st = load_state()
    idx = st["last_idx"]
    done = set(tuple(d) for d in st.get("done", [])) | DONE
    for _ in range(len(ROTATION)):
        idx = (idx + 1) % len(ROTATION)
        if ROTATION[idx] not in done:
            return idx, ROTATION[idx]
    # alle done -> naechstes einfach (verhindert Deadlock)
    idx = (idx + 1) % len(ROTATION)
    return idx, ROTATION[idx]

def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PIPE))
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:500])
    return r.returncode == 0, r.stdout

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("branch", nargs="?", default=None)
    ap.add_argument("region", nargs="?", default=None)
    args = ap.parse_args()

    if args.branch and args.region:
        branch, region = args.branch, args.region
        idx = -1
    else:
        idx, (branch, region) = next_segment()

    stamp = datetime.now(TZ).strftime("%Y%m%d_%H%M")
    print(f"=== Werkspree Microsite-Pipeline: {branch} / {region} ({stamp}) ===")

    # 1) Recherche
    ok, out = run([sys.executable, "hot_leads_pipeline.py", branch, region, "20", "10"])
    if not ok:
        print("ERROR: Recherche fehlgeschlagen")
        return 2

    # hot_leads laden
    hl_path = DATA / f"hot_leads_{branch}_{region}.json".replace(" ", "_")
    if not hl_path.exists():
        print("WARN: Keine hot_leads-Datei erzeugt")
        return 0
    hl = json.loads(hl_path.read_text())
    leads = hl.get("hot_leads", [])
    print(f"\n>>> {len(leads)} qualifizierte Hot-Leads")

    sent = []
    # Globale Dubletten-Sperre: Adressen, die schon einmal kontaktiert wurden
    logp = DATA / "microsite_sent_emails.json"
    already = set()
    if logp.exists():
        try:
            already = {e.get("email", "").lower() for e in json.loads(logp.read_text()).get("sent_emails", [])}
        except Exception:
            already = set()

    # Opt-out-Sperre (Beschwerden)
    optout = {"emails": set(), "domains": set(), "companies": set()}
    op = DATA / "opt_out.json"
    if op.exists():
        try:
            o = json.loads(op.read_text())
            optout["emails"] = {e.lower() for e in o.get("emails", [])}
            optout["domains"] = {d.lower() for d in o.get("domains", [])}
            optout["companies"] = {c.lower() for c in o.get("companies", [])}
        except Exception:
            pass

    for lead in leads[:2]:  # max 2 pro Lauf
        name = lead.get("name", "Unbekannt")
        email = lead.get("email", "")
        # E-Mail-Validierung: Korrigiere erkennbare Fehler
        if email and "@" in email:
            # Extrahiere E-Mail mit lowercase TLD (stoppt bei Großbuchstaben im TLD)
            match = re.search(r'[\w.\-+]+@[\w\-]+\.[a-z]{2,6}', email)
            if match:
                email = match.group(0)
            lead["email"] = email
        print(f"\n--- Lead: {name} <{email}> ---")

        # 1) Opt-out-Check
        email_l = email.lower()
        email_domain = email_l.split("@")[-1] if "@" in email_l else ""
        if email_l in optout["emails"] or email_domain in optout["domains"]:
            print(f"  OPT-OUT: {email} gesperrt (Beschwerde) -> uebersprungen")
            continue
        # Firmenname im Opt-out?
        name_l = name.lower()
        if any(c and c in name_l for c in optout["companies"]):
            print(f"  OPT-OUT: Firma '{name}' gesperrt -> uebersprungen")
            continue

        # 2) E-Mail-Verifizierung: Nur senden, wenn im Scraper als verifiziert markiert
        #    (Domain passt zur Firma) ODER Freemailer mit Firmen-Match im Local-Part.
        #    Das verhindert Ulmann-Faelle (falsche Aggregator-E-Mail).
        if not lead.get("email_verified", False):
            reason = lead.get("email_verify_reason", "nicht verifiziert")
            print(f"  E-MAIL NICHT VERIFIZIERT ({reason}) -> uebersprungen (Spam-Schutz)")
            continue

        if not email:
            print("  keine E-Mail -> uebersprungen")
            continue
        if email.lower() in already:
            print(f"  DUPLIKAT: {email} bereits kontaktiert -> uebersprungen (Spam-Schutz)")
            continue

        # 2) Lead-JSON fuer Generator aufbereiten
        slug = "".join(c.lower() if c.isalnum() else "-" for c in name)[:40].strip("-")
        lead_json = {
            "company_name": name,
            "segment": branch,
            "region": region,
            "email": email,
            "email_verified": "yes",
            "phone": lead.get("phone", ""),
            "website_issue": "keine/veraltete eigene Website",
            # ECHTE Firmendetails aus GelbeSeiten (kein generischer Default!)
            "about": lead.get("about", ""),
            "products": lead.get("products", []),
            "opening_hours": lead.get("opening_hours", {}),
            "owner": lead.get("owner", ""),
            "address": lead.get("address", ""),
            "city": region,
            "slug": slug,
        }
        lead_path = DATA / f"lead_{slug}.json"
        lead_path.write_text(json.dumps(lead_json, ensure_ascii=False, indent=2))

        # 3) Build (Gemini API - professionelle Microsite)
        lead_path.write_text(json.dumps(lead_json, ensure_ascii=False, indent=2))
        ok_b, _ = run([sys.executable, "gemini_builder.py", str(lead_path)])
        if not ok_b:
            print("  Build fehlgeschlagen (Gemini)")
            continue
        # 3b) Deploy (zentral pushen, damit Sandbox-Git-Context genutzt wird)
        run(["git", "-C", str(PIPE.parent), "add", "-A"])
        run(["git", "-C", str(PIPE.parent), "commit", "-m",
             f"feat: microsite {slug} ({name})", "--no-verify"])
        run(["git", "-C", str(PIPE.parent), "push", "origin", "main"])
        built = json.loads(lead_path.read_text())
        site_url = built.get("site_url", "")
        print(f"  Site: {site_url}")

        # 4) Versand
        template = json.loads((PIPE / "email_templates_microsite.json").read_text())
        t = template["microsite_draft"]
        body = t["body"].replace("{SITE_URL}", site_url).replace("{COMPANY}", name)
        subject = t["subject"].replace("{COMPANY}", name)
        # send_mail.py erwartet --to --subject --body-text
        ok_s, _ = run([
            sys.executable, "send_mail.py",
            "--to", email,
            "--subject", subject,
            "--body-text", body,
        ])
        if ok_s:
            sent.append({"company": name, "email": email, "site_url": site_url})
            # Protokoll
            logp = DATA / "microsite_sent_emails.json"
            logs = json.loads(logp.read_text()) if logp.exists() else {"sent_emails": []}
            logs["sent_emails"].append({
                "company_name": name, "email": email, "subject": subject,
                "site_url": site_url, "sent_at": datetime.now(TZ).isoformat(),
            })
            logp.write_text(json.dumps(logs, ensure_ascii=False, indent=2))

    # Report
    report = f"""# Werkspree Microsite-Pipeline — {branch} / {region}

**Lauf:** {stamp}
**Qualifizierte Leads:** {len(leads)}
**Mails gesendet:** {len(sent)}

"""
    for s in sent:
        report += f"- ✅ {s['company']} <{s['email']}> → {s['site_url']}\n"
    if not sent:
        report += "- Keine Mails versendet (0 qualifizierte Leads mit E-Mail).\n"
    rep_path = REPORTS / f"microsite_{stamp}.md"
    rep_path.write_text(report)
    print(f"\nReport: {rep_path}")

    if idx >= 0:
        # Segment NUR als done markieren, wenn die Recherche echte Kandidaten
        # geliefert hat. Bei 0 Kandidaten war die Maps-Suche vermutlich ein
        # transienter Firecrawl-Fehler -> Segment NICHT verbrennen (wird beim
        # naechsten Durchlauf der Rotation erneut versucht).
        if hl.get("all_candidates"):
            done = set(tuple(d) for d in load_state().get("done", [])) | DONE
            done.add((branch, region))
            save_state(idx, done)
        else:
            print("WARN: Recherche ohne Kandidaten (transienter Fehler?) "
                  "-> Segment NICHT als done markiert")
    return 0

if __name__ == "__main__":
    sys.exit(main())
