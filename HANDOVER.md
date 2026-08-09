# Werkspree — KI-Automatisierung für kleine Unternehmen
## Vollständiger Projekt-Handover (Stand: 08.08.2026)

---

## 1. ÜBERBLICK

**Werkspree** ist ein B2B-Service-Business, das KI-Automatisierung an kleine Unternehmen in Berlin/Brandenburg verkauft. Ziel: minimaler manueller Aufwand, Agent-gesteuert (Lead-Generierung, Outreach, CRM, Zahlungsabwicklung).

**Pseudonym:** Finn Werksby (NIEMALS den echten Namen verwenden)
**Absender-E-Mail:** a2807d@gmail.com (Display Name: "Finn Werksby")
**Domain:** werkspree.bki-de.de (Subdomain von bki-de.de, gekauft bei Strato)

---

## 2. INFRASTRUKTUR

### 2.1 GitHub Repo
- **Repo:** https://github.com/2Anton1/werkspree
- **Branch:** main
- **Lokaler Pfad:** ~/werkspree
- **Lokaler User git config:** 2anton1 / a2807d@gmail.com

### 2.2 Landing Page (GitHub Pages)
- **URL (aktuell):** https://2anton1.github.io/werkspree/
- **Custom Domain:** https://werkspree.bki-de.de (CNAME gesetzt bei Strato, DNS propagiert, SSL-Zertifikat pending)
- **Quelle:** ~/werkspree/index.html (im Root des Repos)
- **SSL:** GitHub Pages auto-SSL, HTTPS enforcement noch nicht aktiv (Zertifikat wird von GitHub ausgestellt, dauert 5-15 Min)
- **Cron-Job "GitHub Pages SSL Check" (8a0ea7b0e123):** prüft alle 30 Min ob SSL bereit ist und aktiviert es automatisch. Wiederholt 12x.

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

### 2.7 Firecrawl (Web-Scraping)
- **CLI:** firecrawl (installiert, authentifiziert)
- **Credits:** ~1.024 remaining
- **Verwendung:** `firecrawl scrape URL -o output.md` / `firecrawl search "query" --limit N -o output.json --json`

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
- **Pipeline:** GelbeSeiten scrape → Firmennamen+Telefon extrahieren → Firmenwebsite /impressum scrape → E-Mail finden → JSON speichern
- **Branchen-Rotation:** 16 (Branche, Region)-Paare rotieren täglich (Elektriker Berlin, Dachdecker Berlin, etc.)
- **Ausgabe:** ~/werkspree/scraper/data/leads_YYYYMMDD.json

### 4.4 Outreach-Engine
- **Pfad:** ~/werkspree/scraper/outreach.py
- **Funktion:** Lädt Leads, generiert personalisierte E-Mails, sendet via Gmail API
- **Limit:** 10 E-Mails/Tag
- **Follow-up-Logik:** Initial → 3 Tage Follow-up → 7 Tage letzter Follow-up
- **Tracking:** ~/werkspree/scraper/data/sent_emails.json
- **Absender:** "Finn Werksby" <a2807d@gmail.com>

### 4.5 E-Mail-Templates
- **Pfad:** ~/werkspree/scraper/email_templates.json
- **3 Templates:** initial (Kaltakquise), followup_3days (kurze Nachfrage), followup_7days (letzter Hinweis)
- **Platzhalter:** {company_name}, {branch}, {region}, {first_contact_date}
- **Unterschrift:** Finn Werksby, Werkspree

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
| e1e5b8283664 | Werkspree Lead Pipeline | Täglich 10:00 | Neue Leads scrapen + E-Mails versenden |
| 8a0ea7b0e123 | GitHub Pages SSL Check | Alle 30 Min | SSL-Zertifikat prüfen + HTTPS aktivieren (12x wiederholend) |

---

## 6. ENV-VARIABLEN (~/.hermes/.env)

Alle Secrets/Keys befinden sich in ~/.hermes/.env. NIEMALS in Dateien committen.
```
STRIPE_PUBLIC_KEY=...  (pk_live_...)
STRIPE_SECRET_KEY=...  (sk_live_...)
AIRTABLE_API_KEY=...   (pat...)
N8N_API_KEY=...        (eyJhbG...)
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

### Ausstehend ⏳
- [ ] SSL-Zertifikat für werkspree.bki-de.de — DNS korrekt propagiert, aber GitHub hat das Zertifikat noch nicht ausgestellt (API: "The certificate does not exist yet", Stand 08.08.2026). CNAME wurde erneut gespeichert, um die Ausstellung anzustoßen. Cron `8a0ea7b0e123` prüft automatisch weiter.
- [ ] HTTPS enforcement aktivieren (sobald Zertifikat da — kann laut GitHub-API erst gesetzt werden, wenn das Zertifikat existiert)
- [ ] **Impressum & Datenschutzerklärung fehlen komplett** — rechtlich verpflichtend, siehe Abschnitt 11.1 (kritisch, blockiert nichts technisch, aber Abmahnrisiko)
- [ ] E-Mail-Yield der Lead-Pipeline verbessern (aktuell nur 2 von 50 Leads mit E-Mail = 4%) — siehe Abschnitt 11.2
- [ ] WhatsApp-Alternative (keine 2. Handynummer; Option: Twilio-Nummer ~1€/Monat)
- [ ] Outreach starten (sobald mehr Leads mit E-Mail-Adressen gescraped sind)
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
