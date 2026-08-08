#!/usr/bin/env python3
"""Funnel-Reporting für die Lead-Pipeline: gescrapt -> Website gefunden ->
E-Mail gefunden -> kontaktiert -> geantwortet -> Kunde.

Quelle: Airtable (Base appyMLhXOMHpD5vfT, Table tbluCUpuCPxW1GcWD).
Zeigt auf einen Blick, an welcher Stufe die meisten Leads verloren gehen --
genau das haette den 4%-E-Mail-Yield sichtbar gemacht, bevor er zum
Flaschenhals der gesamten Outreach-Kette wurde.
"""

import json
import os
import sys
import urllib.request
import urllib.error

BASE_ID = "appyMLhXOMHpD5vfT"
TABLE_ID = "tbluCUpuCPxW1GcWD"
ENV_PATH = os.path.expanduser("~/.hermes/.env")

# Airtable "Status"-Werte, die als "kontaktiert"/"geantwortet"/"Kunde" zaehlen.
# Aktuell nutzt die Base nur "Neu" -- sobald Outreach faktisch startet, hier
# die echten Statuswerte ergaenzen, die dafuer verwendet werden.
CONTACTED_STATUSES = {"Kontaktiert", "Outreach gesendet", "Nachfassen"}
REPLIED_STATUSES = {"Geantwortet", "Interessiert", "Termin vereinbart"}
CUSTOMER_STATUSES = {"Kunde", "Abgeschlossen"}


def load_api_key():
    if not os.path.exists(ENV_PATH):
        sys.exit(f"Nicht gefunden: {ENV_PATH}")
    with open(ENV_PATH) as f:
        for line in f:
            if line.startswith("AIRTABLE_API_KEY="):
                return line.strip().split("=", 1)[1]
    sys.exit("AIRTABLE_API_KEY nicht in ~/.hermes/.env gefunden")


def fetch_all_records(api_key):
    records = []
    offset = None
    while True:
        url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}?pageSize=100"
        if offset:
            url += f"&offset={offset}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as e:
            sys.exit(f"Airtable-Fehler {e.code}: {e.read().decode()}")
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records


def is_real_website(website):
    return bool(website) and "gelbeseiten.de" not in website.lower()


def build_funnel(records):
    total = len(records)
    with_website = sum(1 for r in records if is_real_website(r["fields"].get("Website", "")))
    with_email = sum(1 for r in records if r["fields"].get("Email"))
    contacted = sum(1 for r in records if r["fields"].get("Status") in CONTACTED_STATUSES)
    replied = sum(1 for r in records if r["fields"].get("Status") in REPLIED_STATUSES)
    customer = sum(1 for r in records if r["fields"].get("Status") in CUSTOMER_STATUSES)

    return [
        ("Gescrapt", total, total),
        ("Website gefunden", with_website, total),
        ("E-Mail gefunden", with_email, total),
        ("Kontaktiert", contacted, total),
        ("Geantwortet", replied, total),
        ("Kunde", customer, total),
    ]


def print_funnel(rows):
    label_width = max(len(r[0]) for r in rows) + 2
    print(f"{'Stufe':<{label_width}}{'Anzahl':>8}  {'% von gescrapt':>15}  {'% vom Vorschritt':>17}")
    print("-" * (label_width + 8 + 2 + 15 + 2 + 17))
    prev = None
    for label, count, base in rows:
        pct_of_total = (count / base * 100) if base else 0
        pct_of_prev = (count / prev * 100) if prev else (100 if prev is None else 0)
        prev_str = f"{pct_of_prev:.0f}%" if prev is not None else "-"
        print(f"{label:<{label_width}}{count:>8}  {pct_of_total:>14.1f}%  {prev_str:>17}")
        prev = count


def main():
    api_key = load_api_key()
    records = fetch_all_records(api_key)
    if not records:
        print("Keine Airtable-Records gefunden.")
        return
    rows = build_funnel(records)
    print(f"Werkspree Lead-Funnel (Quelle: Airtable, {len(records)} Records)\n")
    print_funnel(rows)

    statuses = set(r["fields"].get("Status", "") for r in records)
    unmapped = statuses - CONTACTED_STATUSES - REPLIED_STATUSES - CUSTOMER_STATUSES - {"Neu", ""}
    if unmapped:
        print(f"\nHinweis: unbekannte Status-Werte in Airtable, nicht in der Funnel-Zuordnung erfasst: {sorted(unmapped)}")


if __name__ == "__main__":
    main()
