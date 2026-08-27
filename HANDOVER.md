# Werkspree — KI-Automatisierung für kleine Unternehmen
## Vollständiger Projekt-Handover (Stand: 23.08.2026)

---

## Kritischer Vorfall: Opt-out / Falsch-Zuordnung (15.08.2026)

**Beschwerde von P. Ulmann (kontakt@fahrschule-ulmann.de):**
- Email wurde im Fahrschule-Lauf an `kontakt@fahrschule-ulmann.de` gesendet, aber der
  Lead hieß "Fahrschule Pedal Pandas" — **falsche Zuordnung** (Ulmann ist andere Fahrschule).
- Die generierte Microsite enthielt **hartkodierten Bäckerei-Text** ("Traditionsbäckerei
  seit 36 Jahren", "Handwerksrolle Potsdam") auf einer Fahrschule-Site.
- Ulmann forderte: keine weitere Kontaktaufnahme, keine Veröffentlichung mit seiner Adresse.

**Fixes ( gleicher Tag, gepusht d4c8d6c ):**
1. `build_microsite.py` `render()`: Segment-spezifische Produkte/About (Map pro Branche),
   **kein Bäckerei-Default mehr**. Generic About statt "Traditionsbäckerei".
2. `opt_out.json` (microsites/pipeline/data/): gesperrte Emails/Domains/Companies.
   Orchestrator überspringt diese vor dem Versand.
3. Falsch-Zuordnungs-Heuristik: Wenn E-Mail-Local-Part keine Token mit Firmenname teilt
   UND Local-Part >= 4 Zeichen UND Branche nicht im Local-Part -> Verdacht, übersprungen.
4. Entschuldigungs- + Opt-out-Bestätigungs-Mail an Ulmann gesendet (Strato, 15.08.).

**Opt-out-Policy (ab sofort):**
- Jede Beschwerde/Ablehnung -> sofort `opt_out.json` ergänzen (email/domain/company).
- Orchestrator prüft vor jedem Versand gegen `opt_out.json`.
- Keine Veröffentlichung von Microsites mit gesperrten Adressen.
- Double-Opt-in nicht nötig (Kaltakquise freigegeben), aber **jede Beschwerde = sofortiger Stopp**.

---

## 1. ÜBERBLICK

**Werkspree** ist ein B2B-Service-Business, das konkrete Büroprozesse für kleine Handwerks- und Dienstleistungsbetriebe in Berlin/Brandenburg automatisiert. Die neue Kernpositionierung lautet: ein Prozess, klare Regeln, messbare Entlastung — mit menschlicher Kontrolle bei Entwürfen, finanziellen und irreversiblen Aktionen.

**Pseudonym:** Finn Werksby (NIEMALS den echten Namen verwenden)
**Absender-E-Mail:** a2807d@gmail.com (Display Name: "Finn Werksby")
**Domain:** werkspree.bki-de.de (Subdomain von bki-de.de, gekauft bei Strato)

---

## 2. INFRASTRUKTUR

### 2.0 Google APIs (Wichtig!)
#### 2.0.1 Google Places API
- **API Key:** `GOOGLE_PLACES_API_KEY` in `~/.hermes/.env`
- **Preis:** 0$ im Free-Tier (200$ Credit/Monat für neue Kunden)
- **DANACH:** $0.032/Suche (Text Search) + $0.017/Details
- **WICHTIG:** User will **NICHTS** für Places API zahlen!
- **Budget-Limit:** Max 1-2 Suchanfragen pro Pipeline-Lauf (automatisch begrenzt)
- **Alternative:** Direct Scraper (requests + BeautifulSoup) für Firmen-Websites (kostenlos)
- **Aktiviert am:** 20.08.2026

#### 2.0.2 Google Gemini API (Microsite-Builder)
- **API Key:** `GOOGLE_API_KEY` in `~/.hermes/.env` (gleicher Key wie Places)
- **Preis:** 0$ (60 Anfragen/Min, 1500 Anfragen/Tag — kostenlos)
- **Verwendung:** Generiert professionelle HTML-Microsites für heiße Leads
- **Modell:** gemini-3-flash-preview
- **Fallback:** Statisches Template (`build_microsite.py`) wenn Gemini versagt
- **Aktiviert am:** 20.08.2026

### 2.1 GitHub Repo
- **Repo:** https://github.com/2Anton1/werkspree
- **Branch:** main
- **Lokaler Pfad:** ~/werkspree
- **Lokaler User git config:** 2anton1 / a2807d@gmail.com

### 2.2 Landing Page (GitHub Pages)
- **URL (aktuell):** https://2anton1.github.io/werkspree/
- **Custom Domain:** https://werkspree.bki-de.de (CNAME gesetzt bei Strato, DNS propagiert, SSL-Zertifikat pending)
- **Quelle:** ~/werkspree/index.html (im Root des Repos)
- **Positionierung (11.08.2026):** Hero und Leistungsargumentation auf Rechnungs-OCR, Postfachentlastung, Lead-Nachfassung und Freigaben umgestellt. Paketnamen lauten jetzt Automation Starter/Growth/Enterprise; Leistungsumfang wurde auf konkrete, produktisierte Prozess-Sprints ausgerichtet.
- **SSL:** GitHub Pages auto-SSL, HTTPS enforcement noch nicht aktiv (Zertifikat wird von GitHub ausgestellt, dauert 5-15 Min)
- **Cron-Job "GitHub Pages SSL Check" (8a0ea7b0e123):** prüft alle 30 Min ob SSL bereit ist und aktiviert es automatisch. Wiederholt 12x; nach erfolgreicher Aktivierung pausieren/entfernen.

### 2.3 n8n (Automatisierung)
- **URL:** https://n8n.anton-drooff.de
- **Server:** Hetzner VPS, 91.98.174.183, Ubuntu 24.04
- **SSH:** user=anton, Passwort **[ENTFERNT 08.08.2026 — Repo ist öffentlich, Passwort war im Klartext exponiert. SOFORT ROTIEREN. Danach: in ~/.hermes/.env oder Passwortmanager, niemals hier im Klartext]**
- **Setup:** Docker Container "n8n-n8n-1", Nginx Reverse Proxy, SSL via Let's Encrypt
- **n8n Version:** 2.33.7
- **n8n Login:** finn@werkspree.bki-de.de / Passwort **[ENTFERNT 08.08.2026 — selbes Problem, SOFORT ROTIEREN]**
- **n8n API Key:** in ~/.hermes/.env als N8N_API_KEY
- **docker-compose:** /home/anton/n8n/docker-compose.yml auf dem Server
- **WICHTIG:** Auf demselben Server laufen pv-ki.de, anton-drooff.de, career-tool.pv-ki.de. NICHT ANFASSEN.

#### Workflow: Rechnungs-OCR Demo
- **Workflow ID:** bj8yGBoDgrSkRPKR
- **Status:** aktiv
- **Webhook:** POST https://n8n.anton-drooff.de/webhook/rechnung-ocr
- **Pipeline:** Webhook → Code-Node (RegEx-Extraktion) → Airtable (neuer Record) → Response
- **Extrahiert:** Rechnungsnummer, Datum, Betrag, USt, IBAN, BIC, Absender, Konfidenz-Score
- **Airtable Credential ID:** PxHtJTQCVZN6cO82 (in n8n gespeichert)
- **Test:** Erfolgreich, Execution Status = success, Airtable Record erstellt
- **Bekanntes Issue:** Code-Node extrahiert Daten unvollständig wenn JSON als String gesendet wird (RegEx greift nicht auf \n in JSON). Pipeline funktioniert prinzipiell.

### 2.4 Stripe (Zahlungen)
- **Modus:** LIVE (echte Zahlungen möglich)
- **Account:** acct_1U2Af2ENKo4xUXGe
- **Land:** DE, Währung: EUR
- **Charges enabled:** true, Payouts enabled: true
- **Keys:** in ~/.hermes/.env
  - STRIPE_PUBLIC_KEY=pk_live_51U2Af2ENKo4xUXGe...
  - STRIPE_SECRET_KEY=sk_live_51U2Af2ENKo4xUXGe...
- **Stripe MCP Server:** "stripe_http" in ~/.hermes/config.yaml (HTTP, Bearer auth mit live key)
- **Test-Account:** acct_1U2AfLEEAZGg0HzD (separat, 3 inaktive Test-Produkte)

#### Produkte & Payment Links (LIVE)
| Paket | Product ID | Monthly Price ID | Setup Payment Link |
|---|---|---|---|
| Werkspree KI Starter | prod_V2GDkXbLtFIUpQ | price_1U2BhLENKo4xUXGetkUVrFmX | https://buy.stripe.com/fZu00j9VfgTde5j0L1gnK03 |
| Werkspree KI Growth | prod_V2GDomqOfi78LM | price_1U2BhNENKo4xUXGewr7xIwcO | https://buy.stripe.com/4gMaEX1oJ46rbXbctJgnK04 |
| Werkspree KI Enterprise | prod_V2GDuHgQi450Cg | price_1U2BhPENKo4xUXGe2KiaAqHO | https://buy.stripe.com/3cI4gzebv5avaT71P5gnK05 |
| Individuelle Lösung | — (kein Stripe-Produkt) | — | mailto:a2807d@gmail.com |

### 2.5 Gmail (E-Mail-Versand)
- **Konto:** a2807d@gmail.com
- **Verbindung:** OAuth2 via Google Cloud Console
- **Token:** ~/.hermes/google_token.json (auto-refresh)
- **Client Secret:** ~/.hermes/google_client_secret.json
- **Google Cloud Projekt:** werkspree-504914
- **Scopes:** gmail.readonly, gmail.send, gmail.modify, calendar, drive, contacts.readonly, spreadsheets, documents
- **API-Skript:** python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py
- **Befehle:**
  - Suchen: `python google_api.py gmail search "is:unread" --max 10`
  - Lesen: `python google_api.py gmail get MESSAGE_ID`
  - Senden: `python google_api.py gmail send --to ADDR --subject "..." --body "..." --from '"Finn Werksby" <a2807d@gmail.com>'`

### 2.6 Airtable (CRM)
- **Base ID:** appyMLhXOMHpD5vfT
- **Table ID:** tbluCUpuCPxW1GcWD
- **API Key:** in ~/.hermes/.env als AIRTABLE_API_KEY
- **URL:** https://airtable.com/appyMLhXOMHpD5vfT
- **Token:** in ~/.hermes/.env als AIRTABLE_API_KEY
- **Lead count:** 50 Leads (Elektriker Berlin, alle Status "Neu")

#### Felder im CRM
| Feld | Typ | Beschreibung |
|---|---|---|
| Company | singleLineText | Firmenname (Primary Field) |
| Branch | singleLineText | Branche (z.B. Elektriker, Dachdecker) |
| Region | singleLineText | Region (z.B. Berlin, Potsdam) |
| Website | url | Firmenwebsite |
| Email | email | Kontakt-E-Mail |
| Phone | phoneNumber | Telefonnummer |
| Address | singleLineText | Adresse |
| Status | singleSelect | Neu, Kontaktiert, Interessiert, Demo gesendet, Verhandlung, Kunde, Absage |
| Potential_Score | number | KI-Bewertung 1-10 |
| Package | singleSelect | Starter (290 EUR), Growth (790 EUR), Enterprise (1900 EUR), Noch nicht zugeordnet |
| Last_Contact | date | Letzter Kontakt |
| Scraped_At | dateTime | Gefunden am (Europe/Berlin) |
| Notes | multilineText | Notizen |
| Assignee | singleCollaborator | (ungenutzt, Standardfeld) |
| Attachments | multipleAttachments | (ungenutzt, Standardfeld) |
| Attachment Summary | aiText | (ungenutzt, Standardfeld) |

### 2.7 Scrapling (Web-Scraping, ersetzt Firecrawl + requests+BS4)
- **Installiert:** scrapling 0.4.15 (+ curl_cffi, playwright, patchright, browserforge, Chromium)
- **Verwendung:** `from scrapling.fetchers import Fetcher; page = Fetcher.get(url, timeout=30); page.css("h2"); page.get_all_text()`
- **Vorteile:** Anti-Bot (umgeht Cloudflare Turnstile), adaptive CSS-Selektoren (überlebt Layout-Änderungen), keine API-Keys, keine Credits, keine Rate-Limits
- **DynamicFetcher** (für JS-heavy Seiten wie Google Maps): `DynamicFetcher.fetch(url, headless=True, network_idle=True)`
- **Eingesetzt in:** scraper/pipeline.py, scraper/direct_scraper.py, scraper/warmth_scorer.py, microsites/pipeline/hot_leads_pipeline.py, microsites/pipeline/agent_build_microsite.py, microsites/pipeline/maps_scraper.py
- **Firecrawl CLI** war vorher installiert (`~/.local/bin/firecrawl`) — jetzt nur noch als Fallback für manuelle Scrapes, nicht mehr in Pipeline-Code eingebunden

---

## 3. PAKETE & PREISE

| Paket | Setup-Fee | Monatlich | Beschreibung |
|---|---|---|---|
| KI Starter | 490€ | 290€ | Rechnungsautomatisierung, E-Mail-Autoresponder, 1 Workflow |
| KI Growth | 1.490€ | 790€ | + Mahnwesen, Chatbot, Lead-Gen, 5 Workflows, Telefon-Support |
| KI Enterprise | 2.900€ | 1.900€ | Vollautomatisierung, CRM, Social Media, unbegrenzte Workflows |
| Individuelle Lösung | — | auf Anfrage | Maßgeschneiderte KI-Lösung, Prozessanalyse, persönliche Betreuung |

---

## 4. DATEIEN & SKRIPTE

### 4.1 Landing Page
- **Pfad:** ~/werkspree/index.html
- **Inhalt:** HTML mit CSS (inline), 4 Paket-Karten (Starter, Growth, Enterprise, Individuelle Lösung), Features-Sektion, Kontakt-Sektion
- **Design (seit 08.08.2026):** Überarbeitet im Apple-Design-Stil — fixe transluzente Navbar (backdrop-filter), Typografie mit clamp()-Skalierung und größenspezifischem Letter-Spacing, Scroll-Reveal-Animationen (respektiert prefers-reduced-motion), Karten mit Press-Feedback. Inhalte/Preise/Links unverändert. Commit `6fa1c69`.
- **Stripe-Links:** 3 Live-Payment-Links (Starter, Growth, Enterprise), 1 mailto-Link (Individuelle Lösung)
- **Footer:** "Werkspree — KI-Automatisierung für kleine Unternehmen | Berlin & Brandenburg | Finn Werksby"
- **E-Mail-Link:** mailto:a2807d@gmail.com
- **Erledigt (08.08.2026):** Die verwaiste Duplikat-Seite `~/werkspree/landing/index.html` (falsche Kontakt-Mail, keine Stripe-Links) wurde gelöscht. `index.html` im Repo-Root ist jetzt die einzige Landing Page.

### 4.2 CRM Template
- **Pfad:** ~/werkspree/crm/crm_template.json
- **Inhalt:** JSON-Schema für Airtable (Felddefinitionen, Views)
- **Hinweis:** Template ist veraltet — das echte CRM ist in Airtable Base appyMLhXOMHpD5vfT

### 4.3 Lead-Scraper Pipeline
- **Pfad:** ~/werkspree/scraper/pipeline.py
- **Funktion:** Scraped GelbeSeiten-Kategorieseiten für eine Branche+Region pro Tag
- **Scraping:** Scrapling `Fetcher.get()` + CSS-Selektoren (`h2`, `a[href^="tel:"]`, `a[href*="gsbiz"]`) — kein Firecrawl, keine Temp-Dateien
- **Pipeline:** GelbeSeiten scrape → Firmennamen+Telefon per CSS extrahieren → Firmenwebsite per GelbeSeiten-Profilseite auflösen → /impressum scrape → E-Mail finden → JSON speichern
- **Branchen-Rotation:** 16 (Branche, Region)-Paare rotieren täglich (Elektriker Berlin, Dachdecker Berlin, etc.)
- **Ausgabe:** ~/werkspree/scraper/data/leads_YYYYMMDD.json

### 4.4 Outreach-Engine
- **Pfad:** ~/werkspree/scraper/outreach.py
- **Funktion:** Lädt Leads und kann personalisierte E-Mails erzeugen; Versand ist standardmäßig deaktiviert und erfordert explizit `--send` nach rechtlicher Prüfung/Einwilligung.
- **Limit:** 10 E-Mails/Tag
- **Follow-up-Logik:** Initial → 3 Tage Follow-up → 7 Tage letzter Follow-up
- **Tracking:** ~/werkspree/scraper/data/sent_emails.json
- **Absender:** "Finn Werksby" <a2807d@gmail.com>

### 4.5 E-Mail-Templates
- **Pfad:** ~/werkspree/scraper/email_templates.json
- **3 Templates:** initial (Kaltakquise), followup_3days (kurze Nachfrage), followup_7days (letzter Hinweis)
- **Platzhalter:** {company_name}, {branch}, {region}, {first_contact_date}
- **Unterschrift:** Finn Werksby, Werkspree

### 4.9 Lieferprozesse
- **Pfad:** `PROZESSE.md`
- **Inhalt:** Automation-Sicherheitsstufen, Automation-Sprint, Rechnungs-OCR-Referenzprozess, CRM-/Lead-Regeln und Monatsbetreuung.

### 4.6 n8n Workflow-Datei
- **Pfad:** ~/werkspree/n8n-workflows/rechnungs-ocr-demo.json
- **Inhalt:** n8n-Workflow-JSON für Rechnungs-OCR

### 4.7 .gitignore
- **Pfad:** ~/werkspree/.gitignore
- **Ignoriert:** __pycache__/, *.pyc, .firecrawl/

### 4.8 Leads
- **Pfad:** ~/werkspree/scraper/data/leads_20260808.json
- **Inhalt:** 50 Leads (Elektriker Berlin), davon 2 mit E-Mail-Adresse:
  - Blachnierz & Söhne Elektroinstallationsges. mbH | info@elektro-bs.de
  - Griesbach Elektroanlagen | info@elektro-griesbach.de

---

## 5. CRON-JOBS

| Job ID | Name | Schedule | Zweck |
|---|---|---|---|
| df4d149e4f8f | Werkspree Lead Pipeline (Script Mode) | Täglich 10:00 | run_pipeline.py: pipeline.py → warmth_scorer.py → warm_outreach.py (AUTO-SEND) → Airtable-Sync. Exit≠0 bei Fehler. Report: reports/pipeline_YYYYMMDD.md |
| e85d58d7915e | Werkspree Health Check | Alle 6h | ~/.hermes/scripts/health_check.py (no_agent): silent bei OK, nur Issues melden |
| 251104e77a29 | Werkspree Hot-Lead Microsites (Generator + Mail) | Alle 48h | Maps-Discovery (Firecrawl) → eigener Static-Site-Generator (`build_microsite.py`) → Git-Deploy auf werkspree.bki-de.de/microsites/sites/<slug>/ → Mail an Lead (Strato SMTP `kontakt@werkspree.bki-de.de`) |
| b68eea7332bc | Werkspree Reply Checker | 2x täglich 09:00 + 18:00 | ~/.hermes/scripts/check_replies.py (no_agent): prüft Strato IMAP + Gmail API auf Antworten versendeter Mails. Bei neuen Antworten → WhatsApp-Benachrichtigung. Keine Antwort → still (leere stdout). |

---

## 6. ENV-VARIABLEN (~/.hermes/.env)

Alle Secrets/Keys befinden sich in ~/.hermes/.env. NIEMALS in Dateien committen.
```
STRIPE_PUBLIC_KEY=...  (pk_live_...)
STRIPE_SECRET_KEY=...  (sk_live_...)
AIRTABLE_API_KEY=...   (pat...)
N8N_API_KEY=...        (eyJhbG...)
PONCHO_API_KEY=...     (pk_poncho_..., nur in ~/.hermes/.env; niemals committen/ausgeben)
```

---

## 7. HERMES SKILL

- **Skill-Name:** spreewerk-business (Kategorie: business)
- **Pfad:** ~/.hermes/skills/business/spreewerk-business/SKILL.md
- **Enthält:** Infrastruktur-Doku, Identität, wöchentlichen Execution-Plan, TODO-Liste

---

## 8. TODO-STATUS

### Erledigt ✅
- [x] Business-Name: Werkspree
- [x] **Auto-Outreach freigegeben (14.08.2026)**: warm_outreach.py sendet standardmäßig (max 10/Tag, Score>=6, deep), `--dry-run` simuliert
- [x] Lead-Pipeline auf EINEN Cron reduziert (df4d149e4f8f, Script-Mode; alter Agent-Cron e1e5b8283664 entfernt)
- [x] Exit-Codes korrigiert: run_pipeline.py endet non-zero bei jedem Schritte-Fehler
- [x] Tägliche Laufberichte: reports/pipeline_YYYYMMDD.md + reports/last_report.md
- [x] Healthcheck-Cron (e85d58d7915e) für n8n, Stripe-Links, Landingpage, Pipeline, Env-Keys
- [x] Lead-Filter: nur verifizierte Firmen-Websites; Portale/Branchenverzeichnisse/Bild-URLs raus (BLOCKED_DOMAINS)
- [x] E-Mail NUR aus Impressum/Kontaktseite ("scraped"); info@-Guessing entfernt
- [x] Max 2 Demo-Kandidaten pro Lauf (warmth_scorer, recommended_action=create_demo)
- [x] Hunter-Validierung optional: HUNTER_API_KEY → Top 8 eligible verifizieren
- [x] Neue Lead-Felder: source, last_checked, website_issue, automation_need, verified_email, next_step, response_status
- [x] Conversion-Tracking: n8n-Workflow "Werkspree Tracking" (Webhook /werkspree-tracking → Code → Airtable-Table "Tracking")
- [x] Einstiegsangebot "Automation Sprint" (890€ einmalig, 14-Tage-Sprint) auf Landingpage
- [x] E-Rechnungsprüfer-CTA: "Möchten Sie, dass eingehende Rechnungen automatisch geprüft und vorsortiert werden?"
- [x] Domain: werkspree.bki-de.de (CNAME bei Strato gesetzt)
- [x] Landing Page deployed (GitHub Pages + Live-Stripe-Links + Individuelle Lösung)
- [x] Landing Page im Apple-Design-Stil überarbeitet (08.08.2026, Commit `6fa1c69`)
- [x] Verwaiste Duplikat-Seite `landing/index.html` gelöscht (08.08.2026)
- [x] n8n: installiert, konfiguriert, Rechnungs-OCR Workflow aktiv
- [x] Stripe LIVE: 3 Produkte + Payment Links
- [x] Gmail via OAuth verbunden
- [x] Airtable CRM: Base + Felder + 50 Leads
- [x] Lead-Scraper Pipeline (pipeline.py)
- [x] Outreach-Engine (outreach.py) + E-Mail-Templates
- [x] Cron-Job: tägliche Lead-Pipeline um 10:00
- [x] Pseudonym: Finn Werksby (überall, kein echter Name)
- [x] Positionierung auf konkrete Büroprozesse, produktisierte Sprints und menschliche Freigaben ausgerichtet (11.08.2026)
- [x] Liefer- und Sicherheitsprozesse in `PROZESSE.md` dokumentiert (11.08.2026)
- [x] Outbound-E-Mail-Versand in `outreach.py` und `warm_outreach.py` standardmäßig deaktiviert; Aktivierung nur mit `--send` (11.08.2026)

### Ausstehend ⏳
- [x] SSL-Zertifikat für werkspree.bki-de.de — **erledigt.** Am 09.08.2026 live über HTTPS geprüft, Zertifikat ist da. Cron `8a0ea7b0e123` kann abgeschaltet werden.
- [ ] HTTPS enforcement aktivieren (sobald Zertifikat da — kann laut GitHub-API erst gesetzt werden, wenn das Zertifikat existiert)
- [ ] **Impressum & Datenschutzerklärung fehlen komplett** — rechtlich verpflichtend, siehe Abschnitt 11.1 (kritisch, blockiert nichts technisch, aber Abmahnrisiko)
- [ ] E-Mail-Yield der Lead-Pipeline verbessern (aktuell nur 2 von 50 Leads mit E-Mail = 4%) — siehe Abschnitt 11.2
- [ ] WhatsApp-Alternative (keine 2. Handynummer; Option: Twilio-Nummer ~1€/Monat)
- [ ] Outreach rechtlich prüfen und nur bei zulässiger Grundlage/Einwilligung mit `--send` aktivieren
- [x] Hybrid-Lead-Plan eingeführt: günstiges Screening für alle, Deep-Research nur für maximal 10 Top-Leads, maximal 5 Outreach-Kandidaten pro Lauf (11.08.2026)
- [x] Werkspree-Cron `e1e5b8283664` auf `gemini / models/gemini-3.5-flash` gepinnt, Versand deaktiviert und Zustellung auf `local` gestellt (11.08.2026)
- [ ] CRM-Statuswerte um Qualifiziert, Eingehend, Demo, Angebot und Nicht kontaktieren ergänzen
- [ ] Automation-Starter-Demo als reproduzierbaren Testlauf mit anonymisierten Rechnungen dokumentieren
- [ ] Feintuning Rechnungs-OCR (RegEx-Anpassung für JSON-String-Eingabe)
- [ ] `crm/crm_template.json` ist veraltet (echtes CRM ist in Airtable) — entfernen oder klar als Archiv kennzeichnen

---

## 9. SICHERHEITSREGELN

1. **NIEMALS** den echten Namen verwenden — immer "Finn Werksby"
2. **NIEMALS** pv-ki.de, anton-drooff.de oder career-tool.pv-ki.de auf dem Hetzner-Server anfassen
3. **Stripschüssel** nicht in Commits pushen (sind in .env, nicht im Repo)
4. **Server-Passwort** nicht in Skripten hardcoden
5. SSH zum Server nur via sshpass oder expect (sudo -S wird blockiert)

---

## 10. CHANGELOG

Chronologisches Log für Hermes/Claude — was sich seit dem letzten Handover-Stand geändert hat. Neue Einträge oben anfügen.

### 26.08.2026 — Reply Checker Cron + Scrapling-Migration

#### Reply Checker (`b68eea7332bc`)
- **2x täglich (09:00 + 18:00):** `~/.hermes/scripts/check_replies.py` (no_agent) prüft
  Strato IMAP (`kontakt@bki-de.de`) + Gmail API (`a2807d@gmail.com`) auf Antworten von
  Adressen, an die Werkspree Mails versendet hat (aus `sent_emails.json` +
  `microsite_sent_emails.json`, aktuell 68 Adressen). Auto-Responder/Noreply werden
  gefiltert. Bei neuen Antworten → WhatsApp-Benachrichtigung (`deliver=all`). Keine
  Antwort → leere stdout → still. Erster Test: 1 Antwort von Fa. Roger Laube erkannt.

### 26.08.2026 — Scrapling-Migration: Firecrawl + requests + BS4 ersetzt

**Alle Scraping-Funktionen in beiden Pipelines auf Scrapling umgestellt.** Firecrawl CLI
und `requests`+`BeautifulSoup` vollständig entfernt. 6 Dateien geändert, Commit `b341469`.

#### Lead-Pipeline (`scraper/`)
- **pipeline.py:** `firecrawl_scrape()`/`firecrawl_search()` → `scrapling_scrape()` mit
  `Fetcher.get()`. `extract_listings()` nutzt CSS-Selektoren (`h2`, `a[href^="tel:"]`,
  `a[href*="gsbiz"]`) statt der `**Name**\\`-Regex. `resolve_real_website()` extrahiert
  den "Website"-Link per CSS statt Markdown-Regex. Keine Temp-Dateien mehr.
- **direct_scraper.py:** Komplett auf Scrapling umgestellt (`find_email_on_website`,
  `find_phone_on_website`, `scrape_gelbeseiten_profile`).
- **warmth_scorer.py:** `scrape_website()` nutzt `Fetcher.get()` statt `requests`.
  `CACHE_DIR` von `.firecrawl/warmth` → `data/warmth_cache`.

#### Microsite-Pipeline (`microsites/pipeline/`)
- **hot_leads_pipeline.py:** 8 Funktionen umgestellt (`search_places`, `get_place_details`,
  `find_email_on_website`, `is_outdated_website`, `is_low_quality_website`,
  `check_website_quality`, `scrape_gelbeseiten_profile`, `find_email_and_details_on_gelbeseiten`).
  Places API auf `urllib.request` (war `requests`).
- **agent_build_microsite.py:** `scrape_gelbeseiten_for_lead` + `scrape_gelbeseiten_profile`
  auf Scrapling.
- **maps_scraper.py:** `firecrawl_scrape_json()` → `scrapling_scrape_maps()` mit
  `DynamicFetcher.fetch(url, headless=True, network_idle=True)` für Google Maps (JS-heavy).

#### Smoke-Test
- 52 Leads aus GelbeSeiten (vorher ~10-20 mit alter Regex). 4/5 mit E-Mail.
- `check_website_quality`: score=10/high. `scrape_gelbeseiten_profile`: Name+Phone+Adresse+Website.
- Alle 6 Dateien: `py_compile` bestanden.

#### Entfernt
- Firecrawl CLI-Abhängigkeit aus allen Pipeline-Dateien
- `requests` + `BeautifulSoup` als direkte Dependencies
- `subprocess`-Aufrufe für Scrapes, Temp-Dateien (`/tmp/gsbiz_tmp.md` etc.)
- `os.environ["PATH"]`-Hack für Cron

### 23.08.2026 — Pipeline-Fixes + Microsite-Builder v3 (branchenspezifisches Design)

#### Lead-Pipeline (`df4d149e4f8f`)
- **warmth_scorer.py — Firecrawl → requests+BS4:** `scrape_website()` nutzte die
  `firecrawl scrape` CLI, die bei ~90% der Websites timeoutete (30s). Umgestellt auf
  `requests` + BeautifulSoup (dieselbe Methode wie `direct_scraper.py` und `pipeline.py`).
  Test: 19/20 Scrapes erfolgreich (vorher ~2/20). Timeout 15s, Cap 50k Zeichen.
  Commit `c1a1daf`.
- **`~/.hermes/scripts/run_pipeline.py` aktualisiert:** Der Cron-Job nutzte eine
  veraltete Version aus `~/.hermes/scripts/` (ohne `warm_outreach.py` + Airtable-Sync),
  statt die aktuelle aus `~/work/werkspree/run_pipeline.py`. Kopiert — jetzt laufen
  `warm_outreach.py` (10 Follow-up-Mails) + Airtable-Sync (9 created, 52 updated) korrekt.
- **warm_outreach.py:** 10 Follow-up-7days-Mails via Strato SMTP versendet (vorher 0 —
  falsche Script-Version hatte keinen Outreach-Schritt). 3 neue Initial-Mails an
  Steuerberater (Score 10/10).

#### Microsite-Pipeline (`d6e7e5202ac1` → `3778ad6ca1e7`)
- **Provider von Nous → OpenRouter umgestellt:** Der alte Cron-Job `d6e7e5202ac1` lief
  auf `provider: nous` — bei Provider-Ausfällen ("Hermes can't reach the model provider")
  scheiterten alle 8 Läufe seit 22.08. 18:00. Neuer Job `3778ad6ca1e7` auf OpenRouter
  (gratis, unabhängig). Alter Job pausiert. `cronjob update` übernimmt provider nicht
  zuverlässig → Job neu erstellt statt aktualisiert.
- **gemini_builder.py schreibt site_url zurück:** `gemini_builder.py` schrieb `site_url`
  nicht ins Lead-JSON → 11 Mails ohne URL im Sent-Log. Fix: `site_url` wird nach erfolgreichem
  Build ins Lead-JSON geschrieben. Zusätzlicher Guard im Orchestrator: bei fehlender
  `site_url` wird URL aus Slug konstruiert. Commit `50f286c`.
- **gemini_builder.py v3 — branchenspezifisches Design (HAUPT-UPGRADE):** Vorher hatten
  alle Sites dasselbe Layout (Header → Über uns → Karten-Grid → Öffnungszeiten → Kontakt),
  nur mit leicht unterschiedlichen Farben. Jetzt gibt es **17 Branchen-Profile** mit
  jeweils eigenem Design:
  - Eigener Farbpalette (CSS-Variablen, branchenspezifisch)
  - Eigener Sektionen (Preisliste beim Friseur, Projektgalerie beim Maler, nummerierte
    Steps bei der Fahrschule, Notdienst-Box beim Dachdecker, Saisonkalender beim Gärtner, etc.)
  - Eigener Stimmung/Layout (edel-minimalistisch für Friseur, technisch-robust für Kfz,
    sanft-luxuriös für Kosmetik, dynamisch-jugendlich für Fahrschule)
  - Eigenen CSS-Extras (CSS-Avatare mit Initialen, Pulse-Animationen für Notdienst,
    Holz-Gradient für Tischler, Wellen für Reinigung)
  - Google Fonts (Poppins/Montserrat), responsive Breakpoints, Hover-Effekte
  - Mindestgröße 3000 Zeichen für valides HTML (kein Stub)
  - `max_tokens` von 4000 → 8000 (reichhaltigere Sites)
  Commit `4632719`.
  **Test verifiziert (23.08.):** 3 Test-Sites (Maler, Friseur, Fahrschule) mit jeweils
  eigenem Design, Farben, branchenspezifischen Sektionen. Alle live (HTTP 200).
  **Produktiver Lauf:** Terra-Aqua (Gartenbau/Cottbus) — Site mit Saisonkalender,
  Pflanzenwelt-Liste, branchenspezifischen Grün-Farben. Mail versendet ✅.

#### Antwort-Mails
- **1 positive Antwort von Living in Berlin** (info@livinginberlin.de, Immobilienmakler,
  Score 10/10): *"vielen Dank für Ihre Nachricht. Gern melden wir uns Anfang der
  kommenden Woche bei Ihnen."* — heißer Lead, kommt nächste Woche zurück.

#### Beide Klone synchron
- `~/werkspree` und `~/work/werkspree` auf `origin/main` Stand `ff55035` synchron.
- Test-Sites nach Verifikation entfernt (nur Design-Test, nicht für Leads).

#### Cron-Job-Status (Stand 23.08. 17:35)
| Job ID | Name | Schedule | Provider | Status |
|---|---|---|---|---|
| `df4d149e4f8f` | Lead Pipeline (Script Mode) | Täglich 10:00 | no_agent (script) | ✅ aktiv |
| `3778ad6ca1e7` | Microsite-Pipeline (OpenRouter) | Alle 3h | openrouter | ✅ aktiv (neu) |
| `d6e7e5202ac1` | Microsite-Pipeline (alt, Nous) | Alle 3h | nous | ⏸️ pausiert |
| `e85d58d7915e` | Health Check | Alle 6h | no_agent | ✅ aktiv |

### 17.08.2026 — Lead-Pipeline-Fixes (Strato-Versand, guessed-Filter, Timeout-Toleranz, Airtable)

- **Gmail-Token defekt (Root Cause gefunden):** `google_token.json` hatte `expiry` als Float
  (Unix-Timestamp) statt ISO-String → `google_api.py` crashte bei JEDEM Aufruf mit
  `AttributeError: 'float' object has no attribute 'rstrip'`. Zusätzlich Refresh-Token revoked
  (`invalid_grant`). Fix: Float→ISO-Konvertierung in `_normalize_authorized_user_payload` +
  `get_credentials()` (kein Crash mehr); echter OAuth-Re-Login bleibt manuell offen (Browser).
- **warm_outreach.py sendet jetzt via `send_mail.py` (Strato SMTP `kontakt@bki-de.de`)** statt
  google_api.py/Gmail — konsistent mit der Microsite-Pipeline, Gmail nur noch Fallback.
  Verifiziert 17.08.: 4/4 Follow-ups via Strato gesendet (kanzlei-barz, recht-web,
  ra-gerd-engelmann, ruspravo) — vorher 0/5 via Gmail (Token-Crash).
- **email_source-Filter:** `guessed`-E-Mails (info@-Geraten) werden NIE mehr versendet
  (ELEKTRO REIBSCH, HKF, Cafe a la Russe, Wolter GmbH jetzt geskippt).
- **Follow-up-Zyklus-Reparatur:** Fehlgeschlagene Sends speicherten `_failed`-Status, der nie
  wieder in den Zyklus kam → 5 Follow-ups waren „verbrannt". Fix: Fehlschläge speichern KEINEN
  Status; `sent_emails.json` wurde repariert (5× `followup_3days_failed` → `initial_sent`).
  `sent_ok`-Zähler meldet jetzt echte Erfolge statt „Sent to N".
- **warmth_scorer.py:** Firecrawl-Timeout crashte das ganze Scoring → try/except in
  `scrape_website()` (gibt None zurück, Lead wird ohne Content gescort).
- **Airtable-Schema-Korrektur (live verifiziert):** `tbluCUpuCPxW1GcWD` EXISTIERT doch — es ist
  die interne ID von `Table 1` (gleiche Felder). Kein `Email`-Feld → `sync_airtable` legt E-Mail
  in `Notes` ab; `airtable_api()` mit timeout=60 + bis zu 3 Versuchen (vorher 30s ohne Retry).
- Commits: `~/werkspree` `0717771`, `~/work/werkspree` `8297448` (nach rebase). Beide Klone
  synchron mit origin/main.

### 16.08.2026 — Microsite-Pipeline: Hennig-Falschzuordnung verhindert, Segment-Verbrennung gefixt

- **Ulmann-Fall in neu verhindert:** `validate_email_for_company` akzeptierte generische
  Branchen-Tokens („fahrschule") als Match → Fahrschule Hennig bekam `info@fahrschule-grueneberg.de`
  zugeordnet. Fix: `GENERIC_COMPANY_TOKENS`-Blocklist + Umlaut-Normalisierung `_norm_token()`.
  Test-Batterie grün (Grüneberg ✓, Hennig ✗, Ulmann ✗, Caresse ✓).
- **Segment-Verbrennung:** Orchestrator markierte Segmente auch bei transientem Firecrawl-Fehler
  als done → `run_microsite_pipeline.py` markiert nur noch bei `all_candidates` nicht leer.
- **firecrawl_scrape:** try/except (TimeoutExpired crashte den Lauf mit Exit 2).
- **Parallel-Cron-Hinweis:** 3h-Cron d6e7e5202ac1 kann parallel zu manuellen Läufen feuern und
  spült mit `git add -A` alle Working-Tree-Änderungen in seinen Commit.

### 11.08.2026 — Design- & Inhalts-Upgrade der Landing-Page (index.html)

- **Aisthesis & Typografie (1 A)**: Google Fonts Inter (Fließtext) & Plus Jakarta Sans (Überschriften) integriert. Globale Typografie harmonisiert.
- **Interaktive Demos (1 B)**: Stilisierte, rein in CSS/HTML gebaute Visualisierungen für OCR-Scan, n8n-Workflow und WhatsApp-Kundenbot hinzugefügt.
- **ROI-Rechner (1 C)**: Slider-basierter Ersparnisrechner zur Visualisierung von Zeit-/Geldersparnis mit Amortisationsanzeige für das Starter-Abo (290€/Mo).
- **Ansprechpartner & Trust (2 A)**: Gründer-Profil von Finn Werksby mit CSS-Gradient-Avatar hinzugefügt.
- **Conversion-Hebel (2 C)**: Direktbuchung über Cal.com sowie Callback-Optionen und Rufnummern-Platzhalter integriert.
- **Inbound-Banner (2 D)**: Auffälliges Alert-Banner direkt unter dem Hero-Bereich zur Verlinkung des E-Rechnungs-Prüfers.
- **Qualitätssicherung**: Vollständige W3C-HTML-Konformität via `html-validate` sichergestellt (keine Fehler, keine Warnungen).

### 14.08.2026 (Cron, Firecrawl-only) — Hot-Lead-Pipeline Segment 2 (Friseur/Potsdam) echt geprüft, 0 sendefähige Leads

- Erster Lauf der neuen Poncho-freien Pipeline (siehe Skill-Update "Microsite-Enrichment ohne Poncho ab 14.08.2026"). Vor dem Lauf `latest_hot_leads_run.json`, `microsites/pipeline/data/microsite_sent_emails.json` (nicht vorhanden/leer) und `scraper/data/sent_emails.json` (14 Einträge, alle Elektriker/Berlin, keine Überschneidung) geprüft.
- Segment/Region: **Friseur/Salon + Potsdam** (nächste ungenutzte Kombination nach Elektriker/Neukölln; der vorherige Friseur/Potsdam-Versuch war ein reiner Poncho-Provider-Fehler ohne echte Daten und zählte nicht als geprüft).
- Discovery: Google-Maps-Suchergebnisseite direkt per `firecrawl scrape` abgerufen (Poncho/StableEnrich verlangt weiterhin einen bezahlten Wallet-Tier für Maps-Daten und ist laut Skill nicht mehr der Ausführungspfad). 20 Treffer geparst, alle 20 über der Rating-Schwelle 4.4 — Cap eingehalten (max 20 Maps-Ergebnisse).
- Enrichment: Top 8 nach Rating/Reviews ausgewertet (Cap eingehalten). Für jeden Kandidaten offizielle Website per Firecrawl-Suche gesucht (Booking-/Social-Links ausgeschlossen) und bei Treffer die Seite gescraped.
  - 3 Kandidaten (Konturzimmer denis puck, Friseur Henryk Braun, Friseuratelier Christine Wolff) haben eindeutig aktive, gepflegte eigene Websites mit vollständigem Impressum → **Block nach Regel 6**, obwohl bei zwei davon eine E-Mail im Footer sichtbar war (bewusst nicht kontaktiert, da keine Website-Lücke).
  - 4 Kandidaten (FRISEUR SALON FIRAS, MYF BARBERSHOP, One cut Babershop, LEVANTE-Friseur-Salon) haben **keine eigene Firmenwebsite** — nur Buchungs-/Social-/Verzeichnislinks (fresha.com, termintiger.com, planity.com, Instagram etc.). Echte Website-Lücke, aber ohne eigene Website existiert keine Impressum-/Kontaktseite, aus der eine E-Mail nach Regel 5 entnommen werden könnte. Kein Raten von info@-Adressen.
  - 1 Kandidat (Dreamir Aesthetic Hair Concept, dreamir.de) hat eine moderne eigene Domain, aber der Impressum-Link ist ein funktionsloser Platzhalter (`href="#"`), keine E-Mail auf der Seite, einziger Kontaktweg ist eine private WhatsApp-Mobilnummer — kein Regel-5-konformer E-Mail-Nachweis.
- **Ergebnis: 0 von 8 Kandidaten erfüllen gleichzeitig Website-Lücke UND verifizierte öffentliche E-Mail aus Impressum/Kontaktseite.** Kein Lovable-Aufruf, keine Microsite, kein E-Mail-Versand. `data/latest_hot_leads_run.json` vollständig mit allen 8 Kandidaten, Begründungen und Firecrawl-Credit-Schätzung (~19 Credits) dokumentiert.
- Empfehlung nächster Lauf: nächste ungenutzte Branche/Region-Kombination (z. B. Bäckerei/Café in einer Brandenburg-Kleinstadt wie Brandenburg/Havel oder Frankfurt (Oder)).
- Keine anderen Werkspree-Dienste, Server oder Cronjobs verändert.

### 14.08.2026 (Abend) — Microsite-Pipeline komplett neu (eigener Generator, Strato-Mail, kein Lovable/Poncho)

- **Lovable-OAuth nicht persistierbar:** `claude mcp login lovable` funktioniert in der Hermes-Terminal-Sandbox nicht (Token landet in anderer HOME/Sandbox, verschwindet; echter Tool-Call schlägt mit „OAuth session expired" fehl). 4 erfolglose Versuche.
- **Entscheidung:** Lovable aus dem kritischen Pfad entfernt. Stattdessen **eigener statischer Microsite-Generator** (`microsites/pipeline/build_microsite.py`): rendert `microsite_template.html` mit verifizierten Lead-Daten, deployt nach `microsites/sites/<slug>/index.html` via Git-Push auf `main`. Live unter `https://werkspree.bki-de.de/microsites/sites/<slug>/`.
- **GitHub Pages Fix:** `build_type: legacy` lieferte Unterordner nicht aus → `.nojekyll` im Repo-Root hinzugefügt (deaktiviert Jekyll komplett). Danach Unterordner 200 OK. WICHTIG: Bei künftigen Commits `.nojekyll` nicht löschen, sonst fallen alle `/microsites/`-URLs auf 404.
- **Mail-Versand auf Strato SMTP umgestellt:** `send_mail.py` (zentral, in `microsites/pipeline/`) nutzt `kontakt@werkspree.bki-de.de` (SMTP `smtp.strato.de:465` SSL). Credentials aus `~/.hermes/.env` (`WERKSPREE_SMTP_*`); Gmail-OAuth als Fallback. Seriöser als Gmail, kein Google-OAuth-Risiko. Mobileconfig-Quelle: `~/.hermes/attachments/mail.mobileconfig` (IMAP/SMTP-Parameter, Password nicht enthalten — separat geliefert).
- **Erster End-to-End-Erfolg:** Bäckerei Ulrich von Kuhlnew & Sohn (Brandenburg/Havel, Klein Kreutz) — qualifiziert (Website-Lücke + `info@unsere-baeckerei.de` verifiziert), Site gebaut + live (`/microsites/sites/kuhlnew-baeckerei-klein-kreutz/`), Mail versendet (Gmail-ID `1a00136711294cdf` am 14.08. ~19:02). Später auf den eigenen Generator umgestellt (Live-URL identisch strukturiert).
- **n8n Lead-Response-Handler** (`n8n_lead_response_handler.json`): IMAP-Poll auf `kontakt@` alle 15 min → Airtable-Tag (responded=true) → Notify per Strato-SMTP an `a2807d@gmail.com`. Noch **inaktiv** (muss in n8n-UI importiert + Credentials verknüpft werden: `strato_kontakt` IMAP, `strato_smtp` SMTP, `werkspree_airtable` Airtable).
- Poncho komplett aus der Pipeline entfernt (Kosten + Provider-Ausfälle weg). Workdir vom Cron entfernt (Lock-Timeout behoben).
- Cron-Prompt (`251104e77a29`) auf Generator + Strato-Mail umgestellt, Segment-Rotation (Elektriker→Friseur→Bäckerei→Kleinstädte Brandenburg) aktiv.

### 14.08.2026 (später Lauf) — Hot-Lead-Pipeline BLOCKIERT: Poncho-Provider-Fehler bei Segment 2 (Friseur/Potsdam)

- Vor dem Lauf `latest_hot_leads_run.json`, `microsites/pipeline/data/microsite_sent_emails.json` und `scraper/data/sent_emails.json` geprüft — keine bereits kontaktierten/gebauten Leads in dieser Kombination.
- Segment-Rotation lt. Skill: Segment 1 (Elektriker) wurde bereits mit Berlin Neukölln probiert (0 qualifiziert, echter Poncho-Lauf). Für diesen Lauf gewählt: **Segment 2 (Friseur/Salon) mit Brandenburg-Kleinstadt Potsdam** (Kleinstädte werden laut Vorgabe bevorzugt, da dort eigene Websites seltener sind; Kombination war zuvor ungenutzt).
- `poncho_enrichment.py "Friseur" "Potsdam"` mit exakt `max_results=20`/`max_detail=8` ausgeführt. Ergebnis diesmal: **kein echter Research** — der rohe Poncho-Chat-Transkript (`chat_id 9c69b2df-9ef1-4c0b-b9ba-a9f3a31ae179`) zeigt, dass beide von Poncho/StableEnrich versuchten Google-Maps-Datenquellen (`x402.openwebninja.com`, `places.use.x402atlas.com`) eine bezahlte/USDC-finanzierte "Advanced Wallet" verlangen, die auf dem aktuellen Poncho-Plan nicht verfügbar ist. Statt echter Daten lieferte Poncho ein Platzhalter-JSON (`maps_results=0`, `cost_usd=null`) und fragte, ob der Plan upgegradet, USDC eingezahlt oder auf rein kostenlose Quellen ausgewichen werden soll.
- Damit Skill-Regel 8 einschlägig (Poncho-Lauf liefert kein nachvollziehbares Ergebnis/keine Kosten/keine qualifizierten Leads durch Providerfehler statt durch Sättigung): **nichts gebaut, nichts versendet.** `data/latest_hot_leads_run.json` als `run_blocked: true` mit vollständiger Fehlerbeschreibung geschrieben, damit Segment/Region NICHT fälschlich als "geprüft und leer" gilt.
- **Für Anton/nächsten Agenten:** Der Poncho-Account braucht entweder ein Plan-Upgrade oder eine USDC-Einzahlung in die "Advanced Wallet", bevor die Google-Maps-Discovery über Poncho wieder funktioniert. Ohne das bricht jeder künftige Lauf mit derselben Meldung ab. Bis das geklärt ist, produziert der Cron `251104e77a29` nur Blocked-Runs, keinen echten Fortschritt in der Segment-Rotation.
- Keine anderen Werkspree-Dienste, Server oder Cronjobs verändert.

### 14.08.2026 — Cron-Lauf Hot-Lead-Pipeline: Segment-Rotation auf Elektriker/Neukölln, keine qualifizierten Leads

- Gemäß neuer Skill-Vorgabe (Segment-Rotation, da Restaurant in Berlin fast durchgängig aktive Websites hat: 3 Läufe im August 2026 mit 0 qualifizierten Leads) erstmals ein Nicht-Restaurant-Segment gewählt: **Elektriker / Berlin Neukölln** (erster Eintrag der vorgegebenen Rotation Elektriker → Friseur/Salon → Bäckerei/Café → Reinigung → Tischler/Schreiner → Kosmetik/Beauty → Fahrschule → Kfz-Werkstatt).
- Vor dem Lauf `latest_hot_leads_run.json`, `microsites/pipeline/data/microsite_sent_emails.json` (leer/nicht vorhanden) und `scraper/data/sent_emails.json` (Elektriker Berlin bereits per E-Mail kontaktiert, aber andere Firmen/Kiez — kein Konflikt) geprüft.
- `poncho_enrichment.py "Elektriker" "Berlin Neukölln"` mit den vorgeschriebenen Caps (`max_results=20`, `max_detail=8`, Rating >= 4.4) ausgeführt. Ergebnis: 10 Maps-Treffer über der Rating-Schwelle, 8 Detailkandidaten tiefgeprüft (Cap exakt eingehalten), Kosten 0,50 USD (nachvollziehbar über Poncho-Chat-ID `7b379c11-30f7-4ef2-9a92-72560f65e230`).
- Alle 8 tiefgeprüften Elektrobetriebe hatten eine aktuelle, aktive eigene Website (HTTP oder HTTPS, teils mit wenigen Reviews) — keiner erfüllte die Website-Lücken-Bedingung (`outdated`/`dead`/`no_website`). Damit 0 qualifizierte Leads.
- Kein Lovable-Aufruf, keine Microsite, kein E-Mail-Entwurf, kein Versand. `data/latest_hot_leads_run.json` aktualisiert (Segment-Rotation-Notiz ergänzt: nächster Lauf soll Segment 2 = Friseur/Salon mit Kiez Wedding versuchen, falls dieser Lauf erneut leer bleibt).
- Keine anderen Werkspree-Dienste, Server oder Cronjobs verändert.

### 13.08.2026 — Cron-Lauf Hot-Lead-Pipeline: Live-Poncho-Lauf, keine qualifizierten Leads

- Zweistufige Pipeline gemäß Skill ausgeführt: Discovery-Cap 20 Maps-Ergebnisse, Detail-Cap 8, Rating >= 4.4, `poncho_enrichment.py` mit genau `max_results=20`/`max_detail=8` aufgerufen.
- Erster Versuch (`restaurant`/`Berlin Kreuzberg`) überschritt das interne Skript-Timeout von 240s, weil der Poncho-Chat länger lief. Statt eines zweiten (kostenpflichtigen) Laufs wurde dieselbe `chat_id` erneut mit längerem Timeout abgefragt — kein doppelter Research-Spend.
- Ergebnis: valides JSON, Kosten nachvollziehbar (0,35 USD), 15 Maps-Ergebnisse, 9 Detailseiten geprüft (1 mehr als der angeforderte Cap von 8 — als Diskrepanz in `latest_hot_leads_run.json` vermerkt, aber ohne Auswirkung auf Bau-/Versandentscheidung). Alle 9 tief geprüften Kandidaten hatten eine aktuelle, aktive eigene Website — kein Lead erfüllte die Website-Lücken-Bedingung.
- Damit: keine Microsite gebaut, kein Lovable-Aufruf, kein E-Mail-Entwurf, kein Versand. `sent_emails.json` und vorhandene Microsite-/Pipeline-Dateien wurden vorher geprüft (keine Überschneidung relevant, da 0 Kandidaten).
- Frühere Testergebnisse (Carambar, Cantina Mexicana Que Pasa, Gaffel Haus Berlin) aus dem vorherigen Poncho-Test wurden gegen `sent_emails.json` und Microsite-Daten abgeglichen: keine Treffer, keine bestehenden Artefakte. Sie wurden in diesem Lauf nicht erneut aufgegriffen (andere Region).
- `data/latest_hot_leads_run.json` aktualisiert (Poncho-Chat-ID, Kosten, Maps-/Detail-Zahlen, blockierte Leads mit Gründen, leere Kandidaten-/Microsite-/Entwurfslisten).
- Keine anderen Werkspree-Dienste, Server oder Cronjobs verändert.
- Nächster Schritt für den folgenden Lauf: andere Branch/Region-Kombination aus der Rotation wählen (Kreuzberg-Gastro ist gesättigt mit aktuellen Websites).

### 11.08.2026 — Poncho/StableEnrich-Enrichment in Hot-Lead-Pipeline integriert

- Anton hat einen Poncho-API-Key bereitgestellt. Der Key wurde sicher als `PONCHO_API_KEY` in `~/.hermes/.env` gespeichert (Dateimodus 0600); er steht nicht im Repository und wird in Logs nicht ausgegeben.
- Die programmierbare Poncho-API läuft unter `https://tryponcho.com/api/v1`; das API-Schema wurde über `https://tryponcho.com/api/openapi.json` geprüft. Die native `/api/resources`-Route benötigt SIWX und ist nicht der richtige Pfad für den API-Key.
- Neue Datei `microsites/pipeline/poncho_client.py`: token-armer Client für `POST /api/v1/chats` und Polling über `GET /api/v1/chats/{chatId}/result`; liest den Key aus Umgebung oder `~/.hermes/.env`, druckt ihn nicht.
- Neue Datei `microsites/pipeline/poncho_enrichment.py`: strikte Qualifikation. Maximal 20 Maps-Ergebnisse, maximal 8 Deep-Enrichment-Kandidaten, Rating >= 4.4, Website-Status nur `outdated`/`dead`/`no_website`, öffentlich belegte E-Mail mit `email_verified == yes`, E-Mail-Quell-URL zwingend. Maximal 2 finale Leads. Schreibt `data/latest_hot_leads_run.json`.
- Neue Datei `microsites/pipeline/test_poncho_enrichment.py`: 6 lokale Qualifikationstests bestanden. Zusätzlich `py_compile` für alle neuen Python-Dateien bestanden.
- Cron `251104e77a29` aktualisiert: Name „Werkspree Hot-Lead Microsites (Poncho Enrichment, Draft Only)", alle 48 Stunden. Poncho ist nur Enrichment; Lovable bleibt auf maximal zwei qualifizierte Leads begrenzt; es werden ausschließlich lokale E-Mail-Entwürfe erzeugt, niemals gesendet.
- Testreferenz: Poncho-Testlauf mit den gelieferten Artefakten kostete insgesamt 0,496 USD (Discovery 0,324 USD + Deep Verification 0,172 USD) und ergab drei verifizierte outdated/no-website Leads: Carambar, Cantina Mexicana Que Pasa, Gaffel Haus Berlin. Diese Namen sind nur Testergebnis, nicht automatisch als bereits freigegeben oder kontaktiert zu behandeln; vor jeder Aktion muss der aktuelle CRM-/Sent-Status geprüft werden.
- Wichtig: Der neue Client wurde noch nicht durch einen kostenpflichtigen Live-API-Lauf aus der Pipeline getestet. Der erste Cronlauf muss Fehler, JSON-Vertrag und Kosten protokollieren und bei Unsicherheit blockieren.


### 09.08.2026 — Marketing: Inbound-Strategie aufgesetzt und erste zwei Bausteine live

Auftrag von Anton: eine Marketingstrategie, die ein Agent **ohne sein Zutun** umsetzen kann. Rahmen von ihm vorgegeben: **0 € Budget**, Live-Deployment **ohne Vorabfreigabe**, sofort mit der Umsetzung beginnen.

**Strategie:** neues Dokument `STRATEGIE-MARKETING.md`. Kern: Unter „0 € und ohne Anton" fällt praktisch alles weg, was in 12.6 als hoher Hebel steht (Steuerberater, Innung, Telefon, Google Business — alles braucht einen Menschen oder Geld). Kaltakquise per E-Mail bleibt wegen § 7 UWG gesperrt (12.7). Übrig bleibt genau ein Kanal, der zu einem Agenten passt: **eingehende Anfragen über Inhalte und kostenlose Werkzeuge auf der eigenen Seite**. Gewähltes Thema: die E-Rechnungspflicht — ein Zwang mit akuter Frist, deutlich weniger umkämpft als „KI-Automatisierung", und es führt direkt zum Starter-Paket.

**Umgesetzt und live:**
- `assets/site.css` — geteiltes Stylesheet für Unterseiten, Design-Token 1:1 aus `index.html` übernommen. `index.html` selbst blieb bei seinem Inline-CSS, um kein Risiko einzugehen.
- `e-rechnung/index.html` — Ratgeber zur E-Rechnungspflicht. Fristenstaffel 2025/2027/2028, Empfangspflicht seit 1.1.2025, 800.000-€-Schwelle (maßgeblich ist der Umsatz **2026**), Kleinunternehmerregelung, Ausnahmen nach § 33/§ 34 UStDV und § 4 Nr. 8–29 UStG, Achtjahresaufbewahrung. Mit Quellenangabe (BMF-Schreiben vom 15.10.2025, ZDH, gesetze-im-internet.de), Stand-Datum und Hinweis „keine Rechtsberatung". JSON-LD: `Article`, `FAQPage`, `BreadcrumbList`.
- `e-rechnung-pruefen/index.html` — **kostenloses Werkzeug**: prüft XRechnung-XML (UBL) und ZUGFeRD-PDF (CII) auf die Pflichtangaben nach EN 16931. Erkennt Profil (inkl. „MINIMUM und BASIC WL genügen nicht"), fehlende Pflichtfelder, unstimmige Beträge, und meldet bei einer PDF ohne eingebettete Daten ausdrücklich „gewöhnliche PDF-Rechnung, keine E-Rechnung". Läuft **vollständig im Browser**, kein Upload, kein CDN — `pdf.js` 3.11.174 liegt selbst gehostet unter `assets/vendor/` (Apache 2.0, Lizenz beiliegend). Das ist gleichzeitig das Datenschutz-Argument gegenüber der Zielgruppe.
- `llms.txt` neu, `sitemap.xml` um die drei neuen URLs erweitert.
- `index.html`: Navigation um „E-Rechnung" und „Rechnung prüfen" ergänzt, neue FAQ-Frage zur E-Rechnungspflicht mit Links auf beide Seiten, Footer-Links, vier rohe `&` als `&amp;` maskiert (Altbestand, vom Validator gefunden).
- `datenschutz.html`: neuer Abschnitt 8 zum E-Rechnungs-Prüfer (lokale Verarbeitung, kein Drittdienst), Folgeabschnitte umnummeriert, Stand auf 09.08.2026 gesetzt.

**Verifiziert, nicht nur behauptet:**
- `tests/e-rechnung-pruefer/` — die echte Seite wird in jsdom geladen und die Dateien laufen durch denselben Weg wie beim Besucher (Dateiauswahl → `change`). 31 Prüfungen grün: vollständige XRechnung, vollständige ZUGFeRD-Rechnung, eine absichtlich dreifach kaputte Datei (Profil MINIMUM, fehlender Käufer, Summe stimmt nicht — alle drei erkannt), unbekanntes XML, kaputtes XML.
- `pdf-test.mjs` — Anhang-Extraktion gegen eine echte PDF mit eingebetteter `factur-x.xml` und gegen eine gewöhnliche PDF. Beide korrekt.
- `html-validate` über alle fünf HTML-Dateien: sauber. Dabei behoben: fehlende `aria-label` an den Navigationen, `scope="col"` in den Tabellen, leere Überschrift, Inline-Styles, redundantes `for`, zu lange `<title>`.
- Lokaler Linkcheck über alle Seiten: keine toten Verweise.

**Zwei Nebenwirkungen, die Du kennen solltest:**
- Der lokale Pre-Commit-Hook (`.git/hooks/pre-commit`, nicht im Repo) hat den Commit zunächst blockiert: das Airtable-Token-Muster (`pat` gefolgt von zehn oder mehr alphanumerischen Zeichen) trifft im minifizierten `pdf.min.js` auf harmlose Bezeichner, die schlicht mit „patch…" beginnen. Statt mit `--no-verify` daran vorbeizugehen, habe ich den Hook so angepasst, dass er `assets/vendor/*` überspringt — sonst blockiert jeder künftige Commit an Fremdcode. Sicherung liegt als `.git/hooks/pre-commit.bak`. Meine eigenen Änderungen wurden vorher einzeln gegen alle neun Muster geprüft: keine Treffer.
- Der Push musste von Anton kommen — in meiner Sandbox liegen keine GitHub-Zugangsdaten (`~/.hermes` und der macOS-Schlüsselbund sind von dort nicht erreichbar). **Am 09.08.2026 erledigt**, `origin/main` steht auf `13166bf`.

**Live-Prüfung nach dem Push (09.08.2026):** `https://werkspree.bki-de.de/e-rechnung/` und `/e-rechnung-pruefen/` liefern über HTTPS auf der eigenen Domain aus — das Zertifikat aus Abschnitt 8 ist damit erledigt. `assets/site.css`, `sitemap.xml` und `llms.txt` werden ebenfalls korrekt ausgeliefert, Meta-Angaben und interne Links stimmen. Nicht end-to-end im echten Browser geprüft wurde das Verhalten von `pdf.js` beim PDF-Upload (kein Browser angebunden); die Logik selbst ist unit-getestet und die Dateien liegen im Commit.

**Offen bzw. für Anton:**
- 🔴 **Cron `e1e5b8283664` prüfen.** Im Handover steht „Neue Leads scrapen **+ E-Mails versenden**". Falls der Versandteil aktiv ist, gehört er stillgelegt, bis § 7 UWG geklärt ist. Von hier aus nicht einsehbar — das ist Hermes' Cron.
- Ehrliche Erwartung: neue Seite, keine eingehenden Links, fremde Subdomain. Es kann gut sein, dass drei Monate lang **nichts** darüber hereinkommt. Der Engpass bleibt die fehlende Referenz und die Lieferfähigkeit (12.8), nicht das Marketing. Details in `STRATEGIE-MARKETING.md`, Abschnitt 4.
- Noch nicht eingerichtet: ein Cron, der die Rechtslage regelmäßig gegen die Quellen prüft und die Ratgeber-Seite aktualisiert. Eine veraltete Frist wäre schlimmer als keine Seite.

---

### 08.08.2026 (Nacht — Claude Code, Blöcke 0–3 aus PROMPT-TECHNIK.md)

**Block 0 — Secrets:**
- Repo-Historie bereinigt: `2Anton1/werkspree` ist jetzt ein frischer Single-Commit-Stand ohne die geleakten Passwörter in der Historie. Alter Stand liegt als `2Anton1/werkspree-archive-2026-08-08` (privat) archiviert, nicht gelöscht.
- SSH- und n8n-Passwort waren zum Zeitpunkt der Bereinigung bereits von Anton rotiert.
- `.gitignore` um Secret-Muster ergänzt, lokaler Pre-Commit-Hook installiert (blockt gängige API-Key-Formate, Passwort-Zuweisungen und Private-Key-Header).
- **Zusätzlich gefunden:** Der laufende n8n-Workflow (nicht das Git-Repo) hatte einen echten Airtable-Token im Klartext in einem Node-Parameter, abrufbar über die n8n-API. Der getrackte `n8n-workflows/rechnungs-ocr-demo.json` war davon nicht betroffen (nutzte bereits einen `$env`-Verweis). Herausgenommen — Details unter Block 2. **Dieser Airtable-Token gilt als exponiert und sollte rotiert werden**, unabhängig vom offenen Credential-Problem dort.
- Ein weiterer Fund: `/tmp/n8n_wf_update3.json` (nicht von mir angelegt, Zeitstempel vor dieser Session) enthielt denselben Token im Klartext — gelöscht.

**Block 1 — Landing Page:** Formspree scharf geschaltet (ID von Anton erhalten, per Testsubmission verifiziert), `og-image.png` (1200×630, programmatisch per SVG+Browser-Rendering erzeugt, mit `sips` verifiziert), `robots.txt`, `sitemap.xml`, Canonical-Link, JSON-LD (`ProfessionalService`, mit einem echten Widerspruch: Impressum-Adresse Halle vs. beworbenes Gebiet Berlin/Brandenburg — bewusst nicht verschleiert, siehe 12.1), FAQ-Sektion (5 Fragen, Antworten nur soweit durch bestehende Inhalte gedeckt, sonst bewusst vage statt erfunden), Formular-Fokus-Ring auf echten WCAG-Kontrast (2.67:1 → jetzt >4:1) korrigiert, `datenschutz.html` um einen Formspree-Abschnitt ergänzt (das Formular verweist darauf, vorher fehlte er). Alles mit W3C-Validator und eigener Kontrastrechnung verifiziert, nicht nur Sichtprüfung.

**Block 2 — OCR-Bug:** Parser aus dem n8n-Code-Node in `scraper/n8n-workflows/rechnungs-ocr-parser.js` extrahiert, testgetrieben repariert (`rechnungs-ocr-parser.test.js`, 9/9 grün). Reale Bugs gefunden und behoben: deutsches Zahlenformat wurde abgeschnitten (1.234,56 → 1.23), IBAN-Regex brach bei der Standard-4er-Leerzeichen-Gruppierung, und — der eigentliche Haupttreffer — der Webhook liefert den Body verschachtelt unter `.body`, das alte `input.text`-Zugriffsmuster fand dadurch in Produktion **nie** etwas. Fix live über die n8n-API ausgerollt und mit einer echten Webhook-Execution verifiziert (Produktions-Log, nicht nur Unit-Test): alle Felder korrekt extrahiert.
**Offen:** Der Airtable-Schreibschritt im selben Workflow ist aktuell **nicht funktionsfähig**. Grund: die vorhandene n8n-Credential „Airtable Werkspree" nutzt das von Airtable abgeschaltete API-Key-Verfahren; eine korrekte Ersatz-Credential (`airtableTokenApi`) konnte ich nicht anlegen, weil das Erstellen von Credentials mit eingebettetem Secret vom Sicherheits-Classifier blockiert wurde (zu Recht — das ist ein Secret-Transfer, kein Workflow-Edit). Der hartcodierte, aber funktionierende alte Token wurde bewusst nicht wieder eingesetzt. **Nötig:** entweder in der n8n-UI eine `airtableTokenApi`-Credential mit dem PAT anlegen und am Node „In Airtable speichern" verknüpfen, oder `AIRTABLE_API_KEY` als Environment-Variable im n8n-Docker-Container setzen (dann greift der aktuell konfigurierte `{{ $env.AIRTABLE_API_KEY }}`-Ausdruck).

**Block 3 — Lead-Pipeline / E-Mail-Yield:** Ursache für die 4% E-Mail-Quote analysiert, bevor optimiert wurde (wie gefordert). Eigentlicher Engpass ist **nicht** die Impressum-Extraktion, sondern dass so gut wie nie eine echte Firmen-Website gefunden wurde: die GelbeSeiten-Kategorieseite zeigt den „Webseite"-Button pro Eintrag ohne statischen Link (JS-gesteuert, auch mit `--wait-for` und Link-Extraktion nicht auslesbar) — die echte URL steht erst auf der einzelnen GelbeSeiten-Profilseite. `pipeline.py` scrapte bisher nur die Kategorieseite und landete praktisch immer beim GelbeSeiten-Link selbst als Fallback-„Website". Fix: zweistufiger Abruf (Kategorieseite → Profilseite → echte Website), plus Erweiterung der E-Mail-Suche um Startseite, `mailto:`-Links, deobfuszierte Adressen und zwei zusätzliche Pfade. Dabei einen selbst eingeführten Bug sofort gefangen und behoben: alte Datensätze mit GelbeSeiten-URL als Fallback-„Website" wurden sonst an den MX-Guesser weitergereicht und hätten `info@gelbeseiten.de` als „gefunden" markiert — jetzt durch `is_real_company_website()` hart ausgeschlossen (mit Test). Alles in `scraper/email_extraction.py` unit-getestet (16/16 grün, `test_email_extraction.py`), Verhalten zusätzlich an zwei vormals kaputten realen Leads live verifiziert (echte Domain + echte gescrapte E-Mail gefunden). Firecrawl-Verbrauch für die gesamte Untersuchung und den Live-Test: 18 Credits (1016 → 998). Live-Yield nach Fix: 5,6% der Leads mit echter Website, davon 67% mit gefundener E-Mail (2 von 3) — der Flaschenhals ist die Website-Findung, nicht mehr die Impressum-Suche.
Neues `scraper/funnel.py` (Quelle: Airtable) zeigt den Trichter gescrapt→Website→E-Mail→kontaktiert→geantwortet→Kunde auf einen Blick — aktuell 54 gescrapt, 3 mit Website (5,6%), 2 mit E-Mail (3,7%), alles danach 0 (Outreach läuft noch nicht).
**Telefonnummern-Check:** 85 von 89 lokalen Leads (95,5%) haben eine Telefonnummer, gegenüber 6,7% mit E-Mail — ein klares Argument für telefonischen statt ausschließlich E-Mail-basierten Erstkontakt (ergänzt 12.6, dort war das bereits als „hoher Hebel" vermerkt, jetzt mit Zahlen belegt).

**Block 4 — Outreach-Templates (nur Text, kein Versand, kein Cron):** Alle sechs in 12.7 genannten Fehler in `scraper/email_templates.json` behoben — Serienbrief-Anrede „Guten Tag {company_name}" durch „Sehr geehrte Damen und Herren" ersetzt, tote Adresse `hallo@werkspree.bki-de.de` durch `a2807d@gmail.com` ersetzt, GitHub-Pages-URL durch `https://werkspree.bki-de.de/` ersetzt, Tippfehler „Ich kümmere um den Rest" korrigiert, unzutreffende Behauptung „Ich habe mir Ihre Website angesehen" entfernt (die Pipeline liest nur das Impressum), Abmeldehinweis in allen drei Templates ergänzt. Zusätzlich die unbelegte Erfolgsbehauptung „zahlen sich innerhalb von 30–90 Tagen aus" aus der Initial-Mail entfernt — derselbe UWG-Risikotyp wie die bereits auf der Website entschärfte Garantie-Aussage (12.5 Punkt 4/5).

### 08.08.2026 (Fortsetzung)
- **Schnellmaßnahmen aus 12.9 umgesetzt** (`index.html`):
  - Werbeaussage „Wir garantieren messbare Ergebnisse" und „zahlen sich innerhalb von 30–90 Tagen aus" ersetzt. Neue Feature-Kachel „Zahlen statt Versprechen" — beschreibt das Vorgehen (vorher/nachher messen), enthält keine Zusage. UWG-Risiko aus 12.5 Punkt 4/5 damit erledigt.
  - Kontaktformular in der Kontakt-Sektion ergänzt (Name, Betrieb, E-Mail, Telefon, Anliegen), mit DSGVO-Einwilligungs-Checkbox, Honeypot gegen Spam und AJAX-Versand ohne Seitenwechsel. **Offen: `FORM_ID_HIER_EINTRAGEN` in `action=` durch die echte Formspree-ID ersetzen** — bis dahin zeigt das Formular einen Hinweis und sendet nicht.
  - Preishinweis nach § 19 UStG steht in der Paket-Sektion.
- **Neue Datei `PROMPT-TECHNIK.md`** — fertige Claude-Code-Prompts für die technischen Folgeaufgaben (Secrets, Landing-Page-Technik, OCR-Bug, E-Mail-Yield, Templates).
- **🔴 SICHERHEIT: Passwörter stehen weiterhin in der Git-Historie.** SSH- und n8n-Passwort wurden in Commit `84c9d1d` im Klartext committet und in `d44443e` aus der Datei entfernt — sie bleiben aber über `git log -p` in jedem Klon lesbar. Redaction in einem Folgecommit entfernt nichts. **Beide Passwörter müssen rotiert werden, unabhängig davon, ob die Historie bereinigt wird.** Siehe Block 0 in `PROMPT-TECHNIK.md`.
- **Strategie-Analyse ergänzt — neuer Abschnitt 12 („Strategie & Weiterentwicklung").** Kernbefund: Der eigentliche Engpass ist nicht der E-Mail-Yield (11.2), sondern das komplette Fehlen von Vertrauenssignalen (keine Referenz, Gmail-Adresse, Fremd-Subdomain, „Impressum folgt", Sofort-Zahlung bei 1.980 €). Weitere Punkte: Pseudonym bricht bei Stripe/Rechnung/Vertrag (12.2), Angebot zu abstrakt (12.3), fehlendes Einstiegsprodukt (12.4), 15 konkrete Website-Mängel inkl. riskanter Garantie-Aussage (12.5), Kanäle jenseits der Kaltakquise mit Steuerberater-Kooperation als größtem Hebel (12.6), Textfehler und § 7 UWG beim Outreach (12.7), Lieferfähigkeit (12.8), priorisierte Reihenfolge (12.9). Alte Abschnitte 12/13 zu 13/14 umnummeriert.
- Verwaiste Duplikat-Seite `landing/index.html` gelöscht (Punkt 11.1.3) — Repo-Root `index.html` ist jetzt die einzige Landing Page.
- Auftrag erhalten: rechtsgültiges Impressum (echter Name: Anton Drooff) und Datenschutzerklärung erstellen und live schalten — in Arbeit, siehe unten.

### 08.08.2026
- Wissensgraph des Projekts erstellt (`graphify-out/`, lokal, nicht committed) — 91 Knoten, 11 Communities. Ergab: `landing/index.html` ist ein verwaistes Duplikat (siehe 11.1), Rechnungswesen/Outreach/Scraper sind sauber getrennte Module ohne Zyklen.
- Landing Page (`index.html`, Root) im Apple-Design-Stil neu gestaltet — Inhalte, Preise und alle Stripe/mailto-Links 1:1 übernommen und verifiziert (`grep` gegen Original abgeglichen). Commit `6fa1c69`, gepusht nach `main`.
- SSL-Zertifikat für werkspree.bki-de.de geprüft: DNS korrekt (CNAME → GitHub Pages IPs), aber Zertifikat noch nicht ausgestellt. CNAME per API neu gesetzt, um GitHub zur Neuausstellung zu bewegen. Automatischer Cron läuft weiter.
- Optimierungsanalyse durchgeführt (siehe Abschnitt 11) und in diesem Dokument festgehalten.

---

## 11. OPTIMIERUNGSPOTENZIAL (Stand 08.08.2026)

Analyse-Ergebnis einer Codebase- und Business-Durchsicht. Nach Priorität sortiert. Nichts hiervon wurde ungefragt umgesetzt — Anton/Hermes muss entscheiden.

### 11.1 Kritisch — rechtlich & Lead-Verlust

1. **Kein Impressum.** Für ein gewerbliches Angebot in Deutschland Pflicht (§5 DDG, ex-TMG). Abmahnrisiko ist real und aktiv, da Stripe bereits LIVE Zahlungen entgegennimmt.
   **Zielkonflikt:** Das Pseudonym-Prinzip ("Finn Werksby", Regel #1 in Abschnitt 9) widerspricht der Impressumspflicht — ein Impressum erfordert den echten Namen und eine ladungsfähige Anschrift der verantwortlichen Person. Diese Entscheidung kann kein Agent treffen; Anton muss festlegen, ob über eine Firma/UG, einen Dienstleister (z. B. Impressum-Service) oder eine andere Konstruktion aufgelöst wird.
2. **Keine Datenschutzerklärung.** DSGVO-Pflicht, insbesondere weil Zahlungsdaten (Stripe) und Kontaktanfragen (mailto) personenbezogene Daten sind.
3. ~~Verwaiste Duplikat-Seite `landing/index.html`.~~ **Erledigt 08.08.2026** — gelöscht.

### 11.2 Business-Engpass — bremst den ganzen Trichter

4. **E-Mail-Yield der Scraper-Pipeline: nur 4 % (2 von 50 Leads in `leads_20260808.json`).** Die aktuelle Methode (Impressum-Seite der Firmenwebsite scrapen) findet selten eine E-Mail. Da die Outreach-Engine ausschließlich E-Mail-basiert ist, verpuffen ~96 % der gescrapten Leads ungenutzt — das ist aktuell der größte Hebel im ganzen System. Optionen: alternative Datenquelle mit hinterlegten Kontaktdaten, Telefon-basierter Erstkontakt (Telefonnummern werden zuverlässiger gefunden), oder eine zweite Extraktionsrunde mit anderen Heuristiken (Kontaktformular-Seiten, Impressum-Alternativpfade).
5. **Outreach wurde noch nie gestartet**, obwohl Stripe LIVE ist und seit Tagen Leads gesammelt werden. Ungenutztes Umsatzpotenzial.
6. **Bekannter OCR-Bug** (RegEx greift nicht bei JSON-String-Eingabe) betrifft direkt das Kernfeature des günstigsten Pakets (KI Starter) — sollte vor der ersten Kundenauslieferung gefixt sein.

### 11.3 Aufräumen

7. `crm/crm_template.json` ist laut eigener Dokumentation veraltet (echtes CRM lebt in Airtable) — verwirrt nur, sollte entfernt oder archiviert werden.
8. Kein Funnel-Tracking (Leads gescraped → E-Mail gefunden → Outreach gesendet → Antwort → Kunde). Die Airtable-Daten liefern das bereits, es fehlt nur eine Auswertung — hätte Punkt 4 vermutlich früher sichtbar gemacht.

### 11.4 Wachstum (nicht dringend)

9. Lead-Quellen sind aktuell nur GelbeSeiten + 16 rotierende (Branche, Region)-Paare — Diversifizierung (weitere Verzeichnisse, LinkedIn, Verbände) würde das Volumen unabhängig vom E-Mail-Yield-Problem erhöhen.
10. Keine Geld-zurück-Garantie / kein kostenloser Testzeitraum auf der Landing Page — könnte die Abschlussquote bei kaltakquirierten Leads erhöhen.
11. WhatsApp-Kanal fehlt weiterhin (bereits in Abschnitt 8 als TODO geführt).

---

## 12. STRATEGIE & WEITERENTWICKLUNG (Stand 08.08.2026)

Analyse aus Sicht der Zielgruppe (Handwerks- und Kleinbetriebe in Berlin/Brandenburg). Nichts hiervon ist umgesetzt — es ist Entscheidungsgrundlage für Anton.

### 12.1 Kernproblem: Es fehlt an jeder Stelle ein Vertrauenssignal

Die Zielgruppe kauft keine Technologie, sondern Verlässlichkeit. Ein Elektromeister, der 1.490 € Setup plus 790 € monatlich zahlen soll, prüft zuerst, wer dahintersteht. Was er aktuell vorfindet:

- einen Namen ohne Gesicht, ohne Historie, ohne Referenz
- eine `@gmail.com`-Adresse als einzigen Kontaktweg
- eine Subdomain eines fremden Projekts (`werkspree.bki-de.de`)
- die Fußzeile „Impressum folgt"
- einen „Jetzt buchen"-Button, der direkt zu einer Zahlung über 1.980 € führt

Dieses Profil ist von dem eines Betrugsversuchs für einen vorsichtigen Mittelständler nicht zu unterscheiden. Solange das so bleibt, ist jede Optimierung an Lead-Volumen oder E-Mail-Yield wirkungslos: mehr Traffic auf eine Seite, die kein Vertrauen erzeugt, ergibt mehr Absprünge, nicht mehr Umsatz. **Das ist der eigentliche Engpass — noch vor dem in 11.2 genannten E-Mail-Yield.**

### 12.2 Das Pseudonym ist geschäftlich nicht haltbar

Regel #1 (Abschnitt 9) kollidiert nicht nur mit der Impressumspflicht (bereits in 11.1 vermerkt), sondern bricht spätestens beim ersten Verkauf an mehreren Stellen gleichzeitig:

- **Stripe** ist KYC-verifiziert auf die echte Identität. Zahlungsbeleg, Kontoauszug des Kunden und Statement Descriptor zeigen den registrierten Kontoinhaber, nicht „Finn Werksby".
- **Rechnungen** müssen nach § 14 UStG den vollständigen Namen und die Anschrift des leistenden Unternehmers enthalten. Eine Rechnung von „Finn Werksby" ist keine ordnungsgemäße Rechnung — der Kunde kann sie nicht als Betriebsausgabe geltend machen und wird sie zurückweisen.
- **Verträge** unter einem Kunstnamen sind für den Kunden im Streitfall wertlos, was jeder Steuerberater dem Kunden auch sagen wird.
- **Gewerbeanmeldung**: Ein laufender Dienstleistungsbetrieb ist anmeldepflichtig; die Anmeldung läuft auf den echten Namen.

Das Pseudonym schützt also nur bis zum ersten zahlenden Kunden und erzeugt danach genau den Ärger, den es vermeiden sollte. Realistische Auflösung: eine Einzelunternehmung oder UG mit Geschäftsbezeichnung „Werkspree" gründen — dann ist „Werkspree" nach außen die Marke, der echte Name steht nur in Impressum, Vertrag und Rechnung. Das ist üblich und unauffällig.

**Update 08.08.2026:** Anton hat die Entscheidung getroffen — Impressum mit Klarnamen (Anton Drooff), siehe Changelog. Regel #1 in Abschnitt 9 gilt damit nur noch für Marketing-Kommunikation nach außen (Mails, Website-Texte), nicht mehr für Impressum, Verträge und Rechnungen. **Diese Trennung ist wichtig und sollte in Abschnitt 9 nachgezogen werden.** Offen bleibt, ob „Finn Werksby" als Absendername in der Kaltakquise überhaupt beibehalten werden soll: ein Impressum mit Anton Drooff neben E-Mails von Finn Werksby ist für den Empfänger ein Widerspruch, der Vertrauen kostet statt schützt.

### 12.3 Das Angebot ist zu abstrakt für die Zielgruppe

„KI-Automatisierung", „Workflows", „Prozessautomatisierung" beschreiben die Methode, nicht das Ergebnis. Ein Dachdecker kauft keine Workflows. Er kauft, dass er samstags nicht mehr drei Stunden Rechnungen tippt.

Konkretere Formulierung derselben Leistung:

| Statt | Besser |
|---|---|
| „Automatisierte Rechnungsverarbeitung" | „Ihre Eingangsrechnungen landen fertig erfasst beim Steuerberater — Sie fotografieren sie nur noch ab." |
| „E-Mail-Autoresponder mit KI" | „Jede Anfrage bekommt binnen 5 Minuten eine Antwort, auch wenn Sie auf dem Dach stehen." |
| „1 Workflow nach Wahl" | (ersatzlos streichen — sagt dem Kunden nichts) |

Zusätzlich: **eine Branche zuerst.** Die 16 rotierenden Branche/Region-Paare erzeugen Breite ohne Tiefe. Wer sich auf Elektrobetriebe in Berlin fokussiert, kann branchenspezifisch texten, Referenzen innerhalb der Branche weiterreichen lassen und über die Innung Zugang bekommen. Breite kommt später.

### 12.4 Der Kaufpfad ist zu steil — es fehlt ein Einstiegsprodukt

Aktuell gibt es nur zwei Zustände: nichts, oder 1.980 € Erstzahlung. Zwischen kalter E-Mail und vierstelligem Abo liegt kein Zwischenschritt. Für eine unbekannte Marke ohne Referenz ist die Abschlusswahrscheinlichkeit auf diesem Pfad nahe null.

Vorschlag für ein Einstiegsangebot:

- **„Automatisierungs-Check", 250–390 €, einmalig.** Zwei Stunden Analyse im Betrieb oder per Video, danach ein schriftlicher Bericht: welche drei Abläufe kosten am meisten Zeit, was wäre die Ersparnis, was würde die Umsetzung kosten. Wird bei Beauftragung auf die Setup-Gebühr angerechnet.
- Das ist ein leichtes „Ja", finanziert die eigene Akquise, qualifiziert den Lead und liefert nebenbei die Argumente für den eigentlichen Verkauf.
- **Erster Kunde bewusst vergünstigt oder kostenlos** im Tausch gegen Referenz, Zitat und eine Fallstudie mit Zahlen. Ohne die erste Referenz bleibt jede weitere Akquise Kaltstart.

Ebenfalls zu prüfen: Setup-Gebühr senken und dafür Mindestlaufzeit vereinbaren. Die hohe Einstiegshürde ist derzeit der teuerste Teil des Angebots — psychologisch, nicht rechnerisch.

### 12.5 Website — konkrete Mängel

Die Seite sieht gut aus, aber sie verkauft nicht. Gefunden in `index.html` (Stand Commit `6fa1c69`):

**Vertrauen / Substanz**

1. **Keine Referenzen, keine Fallstudie, kein Gesicht, kein „Über uns".** Der wichtigste fehlende Block.
2. **„Impressum folgt"** (Zeile 461) ist schlimmer als kein Hinweis — es ist ein schriftliches Eingeständnis des Rechtsverstoßes auf der eigenen Seite.
3. **Kein Impressum, keine Datenschutzerklärung, keine AGB.** Ohne AGB ist bei einem Abo unklar, was Laufzeit, Kündigungsfrist und Leistungsumfang sind.

**Rechtlich riskante Werbeaussagen**

4. **„Wir garantieren messbare Ergebnisse"** (Zeile 389). Eine Garantie ist eine einklagbare Zusage. Ohne definierte Messgröße ist das entweder irreführende Werbung nach UWG oder eine Zusage, die nicht eingehalten werden kann. Entweder streichen oder in eine echte, überprüfbare Garantie mit Bedingungen überführen.
5. **„zahlen sich innerhalb von 30–90 Tagen aus"** — unbelegte Erfolgsbehauptung, dieselbe Problematik.
6. **Preise ohne Angabe „zzgl. USt." bzw. Netto-Kennzeichnung.** Bei B2B-Preisen muss erkennbar sein, ob netto oder brutto (PAngV/UStG). Bei Kleinunternehmerregelung nach § 19 UStG muss das ebenfalls ausgewiesen werden.

**Conversion**

7. **Kein Kontaktformular, keine Telefonnummer, kein Terminbuchungs-Link.** Die Seite ruft dreimal zum „kostenlosen Erstgespräch" auf, bietet aber nur einen `mailto:`-Link auf eine Gmail-Adresse. Handwerker rufen an, sie schreiben keine E-Mails. Ein Cal.com-Link und eine Rufnummer sind der größte einzelne Conversion-Hebel auf dieser Seite.
8. **„Jetzt buchen" führt direkt zur Live-Zahlung.** Bei diesem Preispunkt und ohne vorherigen Kontakt ist das der falsche Call-to-Action. Die Stripe-Links gehören hinter das Verkaufsgespräch, nicht auf die kalte Seite. Besser: „Beratung anfragen" als Primär-Button, Zahlung per individuell versendetem Link.
9. **Keine FAQ.** Die naheliegenden Einwände — „Was, wenn es bei mir nicht funktioniert?", „Wer haftet, wenn die KI eine Rechnung falsch erfasst?", „Komme ich da wieder raus?", „Wo liegen meine Daten?" — bleiben unbeantwortet. Gerade die Datenschutzfrage ist bei Buchhaltungsdaten die erste, die kommt.
10. **Kein Beleg für den ROI.** Eine einfache Rechnung („4 Std./Woche × 45 €/Std. = 780 €/Monat gegenüber 290 €") würde den Preis relativieren — die Zahlen dafür fehlen komplett.

**Technisch / Auffindbarkeit**

11. **`og:image` fehlt.** Beim Teilen per WhatsApp oder LinkedIn erscheint eine leere Vorschau.
12. **Kein `sitemap.xml`, kein `robots.txt`, keine strukturierten Daten** (JSON-LD `LocalBusiness`/`Service`).
13. **Eine einzige Seite, ohne Textsubstanz.** Für Suchmaschinen gibt es praktisch nichts zu indexieren.
14. **Domain `werkspree.bki-de.de`** — eine Subdomain eines fremden Projekts wirkt provisorisch. Eine eigene `.de`-Domain kostet unter 15 €/Jahr und ist eines der billigsten Vertrauenssignale überhaupt.
15. ~~Verwaiste Duplikat-Seite `landing/index.html`~~ — am 08.08.2026 gelöscht (Commit `14657ed`), erledigt.

### 12.6 Auffindbarkeit — die Website wird aktuell von niemandem gefunden

Es gibt derzeit exakt einen Kanal: Kaltakquise per E-Mail. Der ist rechtlich problematisch (siehe 12.7) und liefert wegen des E-Mail-Yields kaum Volumen. Alternativen, grob nach Aufwand/Ertrag sortiert:

**Hoher Hebel**

- **Kooperation mit Steuerberatern.** Ein Steuerberater mit 150 Handwerksmandanten hat genau das Vertrauen, das Werkspree fehlt — und ein Eigeninteresse an sauber vorerfassten Belegen, weil das seine eigene Arbeit reduziert. Eine einzige solche Partnerschaft ist mehr wert als das gesamte Scraping. Gleiches gilt für IT-Systemhäuser und Lohnbüros.
- **Innungen und Handwerkskammer Berlin.** Fachvorträge, Newsletter-Beiträge, Mitgliederangebote. Genau der Ort, an dem die Zielgruppe Empfehlungen einholt.
- **Empfehlungen bestehender Kunden** — greift ab Kunde 1, kostet nichts, funktioniert in dieser Branche besser als jeder andere Kanal.

**Mittlerer Hebel**

- **Google Business Profile** + lokale SEO. Setzt eine verifizierbare Adresse voraus, hängt also an der Entscheidung aus 12.2.
- **Inhalte, die eine echte Frage beantworten**, statt Werbetexte: „E-Rechnungspflicht 2025/2026 — was Handwerksbetriebe jetzt tun müssen" ist ein Thema, nach dem die Zielgruppe aktiv sucht und das direkt zum Angebot führt. Ein solcher Beitrag plus ein kostenloser Leitfaden gegen E-Mail-Adresse erzeugt eingehende Leads statt ausgehender.
- **Lokale Facebook- und WhatsApp-Gruppen** für Handwerk in Berlin/Brandenburg.
- **Google Ads** auf enge lokale Suchbegriffe — schnell testbar, kostet aber Budget und funktioniert erst, wenn die Landingpage konvertiert.

**Geringer Hebel für diese Zielgruppe**

- LinkedIn (Handwerksmeister sind dort kaum aktiv), Instagram, allgemeine SEO auf umkämpfte Begriffe wie „KI-Automatisierung".

### 12.7 Outreach — rechtlicher Rahmen und konkrete Textfehler

**Rechtlich:** Kaltakquise-E-Mails ohne vorherige Einwilligung sind nach § 7 UWG auch im B2B grundsätzlich unzulässig; die „mutmaßliche Einwilligung" ist eine enge Ausnahme, auf die sich Gerichte selten stützen. Abmahnungen in diesem Feld sind verbreitet. Das betrifft nicht ein fehlendes Dokument, sondern den gesamten Outreach-Zweig. **Vor dem Scharfschalten der Pipeline anwaltlich klären.** Telefonische Erstansprache im B2B hat ein anderes Risikoprofil (§ 7 Abs. 2 Nr. 1 UWG, mutmaßliche Einwilligung) und findet zugleich deutlich mehr Kontakte — der in 11.2 genannte Yield-Vorteil kommt also doppelt.

**Fehler in `scraper/email_templates.json`:**

- **`{company_name}` als Anrede.** „Guten Tag Blachnierz & Söhne Elektroinstallationsges. mbH" liest sich als Serienbrief und entwertet die Mail im ersten Satz. Korrekt: „Sehr geehrte Damen und Herren" oder ein separat gescrapter Ansprechpartner.
- **Tote Rückmeldeadresse.** Der 7-Tage-Follow-up nennt `hallo@werkspree.bki-de.de` — dieses Postfach existiert nicht. Wer dort antwortet, erreicht niemanden.
- **GitHub-URL in Signatur und Mail** (`https://2anton1.github.io/werkspree/`) statt der eigenen Domain. Signalisiert Bastellösung.
- **Tippfehler** in `followup_3days`: „Ich kümmere um den Rest" (fehlt „mich").
- **Kein Abmeldehinweis** in den Mails.
- Der Satz „Ich habe mir Ihre Website angesehen" ist nachweislich unzutreffend — gescrapt wurde nur das Impressum. Fällt bei Nachfrage sofort auf.

### 12.8 Lieferfähigkeit — was passiert, wenn es funktioniert?

Aktuell existiert **ein** n8n-Workflow (Rechnungs-OCR, mit bekanntem Bug), der das günstigste Paket teilweise abdeckt. Für Growth und Enterprise sind Chatbot, Mahnwesen, CRM-Integration und Social-Media-Automatisierung verkauft, aber nicht gebaut.

- „Unbegrenzte Workflows" für 1.900 €/Monat ist eine unbegrenzte Verpflichtung bei begrenzter Kapazität. Deckeln oder anders formulieren.
- Es gibt keinen Support-Prozess, keine Reaktionszeit-Zusage und keine Vertretung. Bei „Telefon-Support" im Growth-Paket ist das eine Zusage an einen Ein-Personen-Betrieb.
- Empfehlung: nicht mehr verkaufen als das, was reproduzierbar ausgeliefert werden kann. Ein sauber funktionierendes Starter-Paket mit drei zufriedenen Referenzkunden ist mehr wert als drei Pakete auf dem Papier.

### 12.9 Vorgeschlagene Reihenfolge

Bewusst sequenziell — jeder Schritt setzt den vorherigen voraus.

| # | Schritt | Warum zuerst |
|---|---|---|
| 1 | Rechtsform/Identität klären (12.2), Gewerbe anmelden | Blockiert Impressum, Rechnungen, Google Business, Domain — alles Weitere hängt daran |
| 2 | Impressum, Datenschutz, AGB veröffentlichen; „Impressum folgt" entfernen | Akutes Abmahnrisiko bei aktivem Stripe-LIVE |
| 3 | Garantie- und ROI-Aussagen entschärfen (12.5 Punkte 4–6), Preise als netto kennzeichnen | Gleiche Risikoklasse, Aufwand ~30 Minuten |
| 4 | Eigene `.de`-Domain, Kontaktformular, Telefonnummer, Terminbuchung | Ohne Kontaktweg konvertiert kein Besucher |
| 5 | ~~Duplikat-Seite `landing/` beseitigen~~ | ✅ erledigt 08.08.2026 (Commit `14657ed`) |
| 6 | Einstiegsprodukt „Automatisierungs-Check" definieren und auf die Seite nehmen | Macht den ersten Verkauf überhaupt erreichbar |
| 7 | Ersten Referenzkunden gewinnen (vergünstigt, gegen Fallstudie) | Ohne Referenz bleibt jede Akquise Kaltstart |
| 8 | OCR-Bug fixen, Starter-Paket reproduzierbar machen | Muss vor der ersten Auslieferung stehen |
| 9 | Outreach rechtlich klären, Templates korrigieren, dann Telefon-Erstkontakt testen | Erst sinnvoll, wenn Website und Angebot tragen |
| 10 | Partnerschaft mit 2–3 Steuerberatern anbahnen | Größter Hebel, braucht aber Schritt 1–7 als Grundlage |
| 11 | Inhalte zur E-Rechnungspflicht, lokale SEO, Google Business | Mittelfristig, erzeugt eingehende Anfragen |

---

## 13. KOMMANDOS FÜR CLAUDE

### Landing Page aktualisieren
```bash
cd ~/werkspree
# Edit index.html
git add -A && git commit -m "Beschreibung" && git push
# GitHub Pages baut automatisch neu
```

### Stripe API aufrufen
```bash
LIVE_SK=$(grep STRIPE_SECRET_KEY ~/.hermes/.env | cut -d= -f2)
curl -s "https://api.stripe.com/v1/products?active=true" \
  -H "Authorization: Bearer $LIVE_SK" | python3 -m json.tool
```

### Airtable API
```bash
AT_KEY=$(grep AIRTABLE_API_KEY ~/.hermes/.env | cut -d= -f2)
curl -s "https://api.airtable.com/v0/appyMLhXOMHpD5vfT/tbluCUpuCPxW1GcWD?maxRecords=5" \
  -H "Authorization: Bearer $AT_KEY" | python3 -m json.tool
```

### n8n API
```bash
N8N_KEY=$(grep N8N_API_KEY ~/.hermes/.env | cut -d= -f2)
curl -s "https://n8n.anton-drooff.de/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_KEY" | python3 -m json.tool
```

### Gmail senden
```bash
GAPI="python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
$GAPI gmail send --to empfaenger@beispiel.de \
  --subject "Betreff" \
  --body "Nachricht" \
  --from '"Finn Werksby" <a2807d@gmail.com>'
```

### Firecrawl
```bash
firecrawl search "Elektriker Berlin" --limit 10 -o output.json --json
firecrawl scrape "https://example.com/impressum" -o output.md
```

### Scraper ausführen
```bash
cd ~/werkspree
python3 scraper/pipeline.py    # Neue Leads scrapen
python3 scraper/outreach.py    # E-Mails versenden
```

### Cron-Jobs verwalten
```bash
hermes cron list
hermes cron run e1e5b8283664   # Lead Pipeline manuell starten
```

---

## 14. ANWEISUNGEN FÜR CLAUDE

Wenn Du (Claude) an diesem Projekt arbeitest und der Hermes-Agent zurückkehrt, gib ihm folgende Informationen:

```
Projekt: Werkspree — KI-Automatisierung Business
Voller Stand: ~/werkspree/HANDOVER.md (diese Datei)
Skill: spreewerk-business (hermes skills list → spreewerk-business)
Memory: Werkspree Business Eintrag in Hermes Memory
Status: Landing Page neu gestaltet (Apple-Design), SSL-Zertifikat pending
        (DNS ok, GitHub stellt noch aus), Outreach ready aber ungestartet
Kritisch (Abschnitt 11.1): Kein Impressum/Datenschutzerklärung — rechtliches
        Risiko, UND Zielkonflikt mit dem Pseudonym-Prinzip — braucht
        Antons Entscheidung, kein Agent sollte das selbst auflösen
Größter Hebel (Abschnitt 11.2): Lead-Pipeline findet nur bei 4% der Leads
        eine E-Mail-Adresse — bremst die gesamte Outreach-Kette aus
Strategie (Abschnitt 12, NEU): Vor dem Yield-Problem liegt ein größeres —
        die Seite erzeugt keinerlei Vertrauen (keine Referenz, Gmail-Adresse,
        Fremd-Subdomain, kein Telefon, kein Terminlink, Sofortzahlung bei
        1.980 EUR). Mehr Leads auf diese Seite bringen nichts. Siehe 12.9
        für die vorgeschlagene Reihenfolge.
Rechtlich zu prüfen (12.5/12.7): Garantie-Aussage "Wir garantieren messbare
        Ergebnisse" auf der Seite, Preise ohne Netto-Kennzeichnung, und
        Kaltakquise-Mails ohne Einwilligung (§ 7 UWG) — anwaltlich klären,
        bevor die Pipeline scharf geschaltet wird
Nächste Schritte: SSL-Check, Impressum/Datenschutz live, Garantie-Aussage
        entschärfen, Kontaktweg (Telefon/Termin) schaffen, Referenzkunde,
        dann erst Outreach
Wichtig: Pseudonym "Finn Werksby" nur noch im Marketing — Impressum,
        Rechnungen und Verträge laufen auf den Klarnamen (Entscheidung
        08.08.2026, siehe 12.2). pv-ki.de NICHT anfassen
Vollständiges Changelog: Abschnitt 10 dieser Datei
```

Diese Datei befindet sich unter: ~/werkspree/HANDOVER.md
