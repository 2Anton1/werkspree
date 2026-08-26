## Imported Claude Cowork project instructions

## Projektgedächtnis: HANDOVER.md

**HANDOVER.md ist das zentrale Projektgedächtnis für Werkspree.** Jede neue Session in diesem Projektordner muss HANDOVER.md zu Beginn lesen, bevor Entscheidungen getroffen oder Änderungen vorgenommen werden.

### Was darin steht
- Komplette Infrastruktur-Doku (Pfade, Cron-Jobs, Env-Variablen, Airtable-Setup)
- Beide Pipelines (Lead-Pipeline + Microsite-Pipeline) mit allen Abhängigkeiten
- Changelog (chronologisch, neueste Einträge oben)
- TODO-Status (erledigt + ausstehend)
- Sicherheitsregeln (Pseudonym Finn Werksby, keine Secrets committen)

### Verhalten
- **Vor jeder Änderung:** HANDOVER.md lesen, um den aktuellen Stand zu verstehen
- **Nach jeder Änderung:** Relevanten Abschnitt in HANDOVER.md aktualisieren (sparsam aber verständlich)
- **Neue Cron-Jobs, Skripte, Abhängigkeiten:** In Abschnitt 5 (Cron-Jobs) bzw. Abschnitt 4 (Dateien) eintragen
- **Changelog:** Neuen Eintrag oben in Abschnitt 10 anfügen, mit Datum und kurzer Beschreibung
- **Abschnitt 2.7 (Scrapling):** Dokumentation der aktuellen Scraping-Lösung pflegen
