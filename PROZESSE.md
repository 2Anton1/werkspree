# Werkspree – Liefer- und Sicherheitsprozesse

## Produktversprechen

Werkspree automatisiert einen konkreten Büroprozess für kleine Handwerks- und
Dienstleistungsbetriebe. Automatisierung bedeutet hier nicht, dass Entscheidungen
blind an eine KI abgegeben werden. Jeder Prozess hat einen definierten Besitzer,
Freigabepunkte und einen dokumentierten Fehlerweg.

## Automation-Sicherheitsstufen

1. **Lesen:** Dokumente, E-Mails und Datensätze werden eingelesen und klassifiziert.
2. **Entwurf:** Die Automation erstellt Vorschläge, Entwürfe oder Buchungsvorschläge.
3. **Kontrollierte Aktion:** Eine Aktion darf nur nach definierter Kundenfreigabe erfolgen.
4. **Finanziell/irreversibel:** Zahlungen, Löschungen, Vertragsänderungen und
   verbindliche externe Kommunikation bleiben grundsätzlich manuell freizugeben.

## Automation Sprint

### Vor dem Termin

- Prozessfragebogen ausfüllen lassen
- ein Kernproblem und ein messbares Ziel festlegen
- verwendete Tools und Rollen dokumentieren
- Beispieldokumente anonymisieren lassen
- Zugriffsrechte und Freigabeperson bestimmen

### Einrichtung

- Quelle und Ziel verbinden
- Lese- und Schreibrechte getrennt prüfen
- drei normale Fälle und mindestens einen Fehlerfall testen
- Freigabeprozess gemeinsam durchspielen
- keine Kundenpasswörter speichern; der Kunde gibt sie selbst ein

### Übergabe

- einseitiges Prozessblatt hinterlassen
- verbundene Systeme und Datenflüsse dokumentieren
- Verhalten bei Fehlern und Ausfällen festlegen
- Testprotokoll und offene Punkte übergeben
- nach 14 Tagen Ergebnis und Zeitersparnis prüfen

## Rechnungs-OCR als Referenzprozess

Eingang → OCR/Extraktion → Pflichtfeldprüfung → Dublettenprüfung →
Freigabe bei Unsicherheit → Übergabe an Zielsystem → Protokollierung.

Die Automation ersetzt keine steuerliche oder buchhalterische Prüfung. Sie liefert
strukturierte Vorschläge und macht unklare Fälle sichtbar.

## CRM- und Lead-Prozess

- Leads dürfen gesammelt, dedupliziert und qualifiziert werden.
- Jeder Lead erhält Quelle, Datum, Branche, Region und Qualifizierungsnotiz.
- Statuswerte: Neu, Qualifiziert, Eingehend, Demo, Angebot, Kunde, Absage,
  Nicht kontaktieren.
- Kaltakquise per E-Mail ist standardmäßig deaktiviert.
- Die Skripte `outreach.py` und `warm_outreach.py` versenden nur mit dem expliziten
  Flag `--send`, nachdem Einwilligung bzw. rechtliche Zulässigkeit geprüft wurde.
- Abmeldungen und Widersprüche werden dauerhaft respektiert.

## Monatsbetreuung

- Funktionsprüfung der aktiven Workflows
- Prüfung fehlgeschlagener oder ungewöhnlicher Läufe
- Anpassung bei Änderungen an Kunden-Tools
- ein kleiner, nachvollziehbarer Optimierungsvorschlag
- kurze Zusammenfassung: verarbeitet, freigegeben, abgefangen, fehlgeschlagen

## Grenzen der Kommunikation

Werkspree ist kein Anthropic-Partner und verspricht keine vollständige
Automatisierung. Aussagen zu DSGVO, Steuerrecht oder Haftung werden als
prüfbedürftig markiert und nicht pauschal zugesichert.