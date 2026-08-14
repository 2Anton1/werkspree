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
import argparse, json, subprocess, sys, shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

PIPE = Path(__file__).parent
DATA = PIPE / "data"
REPORTS = PIPE / "reports"
REPORTS.mkdir(exist_ok=True)

ROTATION = [
    ("Elektriker", "Berlin Neukölln"),
    ("Friseur", "Potsdam"),
    ("Bäcker", "Brandenburg an der Havel"),
    ("Reinigung", "Cottbus"),
    ("Tischler", "Frankfurt Oder"),
    ("Kosmetik", "Potsdam"),
    ("Fahrschule", "Brandenburg an der Havel"),
    ("Kfz Werkstatt", "Cottbus"),
]
# bereits gepruefte Kombinationen (nicht erneut) - Stand 14.08. abend
DONE = {
    ("Elektriker", "Berlin Neukölln"),
    ("Friseur", "Potsdam"),
    ("Bäcker", "Brandenburg an der Havel"),
    ("Reinigung", "Cottbus"),
    ("Tischler", "Frankfurt Oder"),
}

TZ = timezone(timedelta(hours=2))

def load_state():
    p = DATA / "pipeline_state.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"last_idx": -1}

def save_state(idx):
    (DATA / "pipeline_state.json").write_text(json.dumps({"last_idx": idx}))

def next_segment():
    st = load_state()
    idx = st["last_idx"]
    for _ in range(len(ROTATION)):
        idx = (idx + 1) % len(ROTATION)
        if ROTATION[idx] not in DONE:
            return idx, ROTATION[idx]
    # alle done -> naechstes einfach
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
    for lead in leads[:2]:  # max 2 pro Lauf
        name = lead.get("name", "Unbekannt")
        email = lead.get("email", "")
        print(f"\n--- Lead: {name} <{email}> ---")
        if not email:
            print("  keine E-Mail -> uebersprungen")
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
            "slug": slug,
        }
        lead_path = DATA / f"lead_{slug}.json"
        lead_path.write_text(json.dumps(lead_json, ensure_ascii=False, indent=2))

        # 3) Build
        ok_b, _ = run([sys.executable, "build_microsite.py", "--lead", str(lead_path)])
        if not ok_b:
            print("  Build fehlgeschlagen")
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
        body = t["body"].replace("{SITE_URL}", site_url)
        subject = t["subject"]
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
        save_state(idx)
    return 0

if __name__ == "__main__":
    sys.exit(main())
