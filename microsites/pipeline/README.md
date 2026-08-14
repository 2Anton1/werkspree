# Werkspree Hot-Lead-Microsite-Pipeline

## Aktueller Status

**Funktioniert:** Google-Maps-Scraping, Rating-Filter, Detailseiten-Website-Erkennung, Ausschluss von Buchungs-/Aggregator-Links, Ausgabe von `hot_leads_*.json`, Lovable-Zugang via Claude Code MCP verifiziert.

**Noch nicht produktionsbereit:** E-Mail-Auflösung aus Google-Maps/GelbeSeiten ist wegen fehlender/uneindeutiger GelbeSeiten-Suchergebnisse noch nicht stabil genug für automatischen Versand. Es gibt deshalb bewusst noch keinen automatischen Lovable-Bau und keinen Mailversand.

## Ausführen

```bash
cd ~/werkspree/microsites/pipeline
python3 hot_leads_pipeline.py "restaurant" "Berlin Mitte" 20 10
```

- `20`: maximal ausgewertete Maps-Ergebnisse
- `10`: maximal besuchte Detailseiten (Kostenbremse)
- nur Rating >= 4.4 wird weiterverfolgt
- aktuell wird die Pipeline nur bis zu einem Lead mit verifizierter E-Mail weitergehen, sobald die E-Mail-Quelle stabil ist

## Sicherheits-/Qualitätsregeln

- Keine guessed E-Mail-Adressen für Kaltakquise.
- Nur öffentlich angezeigte Geschäftsadressen; keine privaten Adressen.
- Nur eine einzelne initiale Nachricht pro Unternehmen; Opt-out wird respektiert.
- Keine Website wird aus Review-/Social-/Buchungsplattform-Inhalten kopiert.
- Für Microsites nur öffentliche, verifizierbare Geschäftsinformationen nutzen; Bilder nur mit Nutzungsrecht oder Platzhalter.
- Vor jeder Lovable-Erstellung: Hot Lead muss Rating-Schwelle, Website-Lücke und E-Mail-Nachweis erfüllen.
- Vor jedem Versand: Microsite-URL, E-Mail, Firmenname und Angebotstext werden lokal protokolliert.

## Nächster technischer Schritt

GelbeSeiten-Suche als Primärquelle für die E-Mail-Auflösung durch Suche der exakten Profilseite auf der Branchen-Ergebnisseite ersetzen. Danach 1 Lead in einen Dry-Run überführen: Profil + E-Mail verifizieren, Lovable-Microsite erstellen/deployen, E-Mail zunächst als Entwurf speichern; erst nach Nutzerfreigabe senden.

Angebot: 189 EUR einmalig, inklusive 3 Monate Hosting/Wartung.
Absender: Finn Werksby / Werkspree.

## Lovable-Aufruf

Lovable ist im Workspace `/Users/anton` für Claude Code konfiguriert, nicht im Unterverzeichnis `/Users/anton/werkspree`. Beispiel:

```bash
cd /Users/anton
claude -p "Use lovable MCP ..." --allowedTools "mcp__lovable__..." --max-turns 15
```

Erst `list_workspaces`, dann `create_project`; nach Fertigstellung `get_project` prüfen und erst danach `deploy_project`.

## Bekannter Stolperstein

`claude -p` im Projektverzeichnis `/Users/anton/werkspree` kann den Lovable-Server als nicht verbunden melden, obwohl er in `/Users/anton/.claude.json` unter `/Users/anton` konfiguriert ist. Lovable-Aufrufe daher mit `workdir=/Users/anton` ausführen.

Die Pipeline darf erst nach stabiler E-Mail-Auflösung und expliziter Bestätigung der ersten Testmails in einen Cronjob übernommen werden.

Nicht anfassen: fremde Serverdienste auf 91.98.174.183.

Nicht den echten Namen in Kundenkommunikation verwenden; ausschließlich Finn Werksby.

Keine hartcodierten Secrets ins Repository schreiben.
Die README dient nur zur Kontrolle von Änderungen und ist kein Versand- oder Deployment-Trigger.

Weitere geplante Dateien:
- `hot_leads_pipeline.py` — Discovery und strikte Qualifikation
- `lovable_builder.py` — geplant, erst nach stabilem Hot-Lead-Datensatz
- `outreach_dry_run.py` — geplant, Entwürfe statt Versand
- `data/` — Laufdaten, nicht committen
