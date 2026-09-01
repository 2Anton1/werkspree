# Automation-Starter-Demo: reproduzierbarer Testlauf

Die Demo prüft die Kernstrecke der Lead-Pipeline lokal und sicher: Ein
Beispiel-Lead wird mit Website-Inhalt bewertet. Es werden keine Websites
aufgerufen, keine E-Mail gesendet und keine Airtable-Daten geschrieben.

## Ausführen

Im Projektverzeichnis:

```bash
python3 -m unittest tests/automation_starter_demo.py -v
```

Erwartete Ausgabe:

```text
test_contact_form_lead_is_actionable ... ok
Ran 1 test ... OK
```

## Demo-Eingabe

- Betrieb: `Demo Elektro Berlin`
- Branche/Region: `Elektriker` / `Berlin`
- Website: `https://demo-elektro.example`
- Verifizierte E-Mail: `kontakt@demo-elektro.example`
- Signale: Kontaktformular, Installation/Wartung/Photovoltaik, keine Online-Buchung

## Erwartetes Ergebnis

Der Lead erhält mindestens den Outreach-Schwellenwert 6, enthält das Signal
`has_email` sowie den branchenspezifischen Bewertungsbonus. Der
Automatisierungsbedarf `Termin- und Angebotsanfragen` wird anschließend von
der Scoring-/Research-Stufe für den Outreach-Kontext ergänzt.

Für einen echten Pipeline-Lauf bleiben die bestehenden Sicherheitsgrenzen
aktiv: Nur verifizierte E-Mails werden verwendet, der Outreach-Lauf ist auf
seine Tagesgrenze begrenzt und ein Versand erfolgt nur über den ausdrücklich
aktivierten Outreach-Modus.
