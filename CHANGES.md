# CHANGES.md — ChatGPT Task Briefing

**Status:** WICHTIG — Lies das vor ALLEN weiteren Tasks.

---

## ✅ ERLEDIGT

### DNS & Hosting
- ✅ CNAME `werkspree.bki-de.de → 2anton1.github.io.` aktiviert (Strato A-Record gelöscht)
- ✅ Alle Seiten erreichbar via GitHub Pages SSL (HTTP 200)
- ✅ Website-URLs live:
  - https://werkspree.bki-de.de/
  - https://werkspree.bki-de.de/website-bau/
  - https://werkspree.bki-de.de/e-rechnung-pruefen/
  - https://werkspree.bki-de.de/rechnungs-ocr/
  - https://werkspree.bki-de.de/blog/e-rechnungspflicht-2027/
  - https://werkspree.bki-de.de/blog/e-rechnung-kleinunternehmer/
  - https://werkspree.bki-de.de/blog/website-fuer-handwerker/

### SaaS-Produkte
- ✅ E-Rechnungs-Prüfer Pro: `prod_VAn4FUwSclDBJ0`, Link `8x214n3wR0UfaT70L1gnK06` (29€/Monat)
- ✅ Microsite-Generator: `prod_VAn4ivWl8zOFM7`, Link `bje3cv6J30Uf1ix65lgnK07` (19€/Monat)
- ✅ Rechnungs-OCR Mail-Service: `prod_VAnHo9GckzBcPl`, Link `5kQ9AT3wR7iD0et9hxgnK08` (39€/Monat)

### Landingpages & Blog
- ✅ 5 Branchen-Landingpages in `/website-bau/`: Elektriker, Dachdecker, Maler, Friseur, Kfz
- ✅ 3 Blog-Artikel: e-rechnungspflicht-2027, e-rechnung-kleinunternehmer, website-fuer-handwerker
- ✅ Sitemap aktualisiert (8 neue URLs)

### Technical Infrastructure
- ✅ `werkspree@bki-de.de` in allen Scripts/Configs aktualisiert
- ✅ `.gitignore`: `website-bau/config.js`, `.env.local`

---

## 🔧 NOCH IN ARBEIT (n8n-Bug)

### n8n Microsite-Generator Webhook
- **Problem:** Respond-Node per API erstellt hat keine Antwort zurückgegeben (leerer Output)
- **Aktiver Workflow:** `tZOlY46EecN1BRsd` (v4)
- **Pfad:** `werkspree-microsite-generator`
- **Status:** Website nutzt clientseitigen Fallback (Vorschau mit Wasserzeichen)
- **Lösung für ChatGPT:** Siehe Abschnitt "KI-Generierte Inhalte" in HANDOVER.md

---

## 🎯 NÄCHSTE TASKS (priorisiert)

### PRIORITY 1: n8n Webhook fixen
Siehe HANDOVER.md § "KI-Generierte Inhalte (ChatGPT-Workflow)"

1. **n8n Respond-Node konfigurieren:**
   - Öffne `tZOlY46EecN1BRsd` im n8n-UI
   - Webhook-Node → Respond = "Using Respond to Webhook Node"
   - Respond-Node:
     - "Respond With" = JSON
     - "Response Body" = `{{ JSON.stringify({html: $json.html, success: $json.success}) }}`
     - Status Code = 200
     - Headers: `Content-Type: application/json`, `Access-Control-Allow-Origin: *`
   - Save + Active

### PRIORITY 2: 12 weitere Branchen-Landingpages
Template: siehe `/website-bau/index.html` und `/website-bau/maler/`

| Nr | Branche | Template-Ort |
|---|---|---|
| 1 | Tischlerei | `/website-bau/tischlerei/` |
| 2 | Kosmetik | `/website-bau/kosmetik/` |
| 3 | Physiotherapie | `/website-bau/physio/` |
| 4 | Gartenbau | `/website-bau/gartenbau/` |
| 5 | Sanitär | `/website-bau/sanitaer/` |
| 6 | Reinigung | `/website-bau/reinigung/` |
| 7 | Steuerberater | `/website-bau/steuerberater/` |
| 8 | Immobilien | `/website-bau/immobilien/` |
| 9 | Zahnarzt | `/website-bau/zahnarzt/` |
| 10 | Fahrschule | `/website-bau/fahrschule/` |
| 11 | Bäckerei | `/website-bau/baeckerei/` |
| 12 | Allgemein | `/website-bau/allgemein/` |

### PRIORITY 3: Blog-Artikel schreiben
Template: siehe `/blog/e-rechnungspflicht-2027/`

---

## 📁 WICHTIGE PFADE

- Projekt: `/Users/anton/werkspree/`
- Landingpage: `website-bau/index.html`
- Templates: `website-bau/<branche>/index.html`
- Blog: `blog/<slug>/index.html`
- n8n Workflows: `n8n-workflows/`
- HANDOVER.md: Vollständige Dokumentation

---

## ⚠️ WICHTIGE HINWEISE

- **Keine Secrets committen!** API-Key in `n8n-workflows/microsite_generator.json` ist nur `$env.GOOGLE_API_KEY`
- **n8n-API-Bug:** Respond-Node per API erstellt keine Ausgabe. muss manuell im UI konfigurieren
- **Pseudonym:** "Finn Werksby" — niemals echter Name verwenden
- **E-Mail:** `werkspree@bki-de.de` (Strato SMTP/IMAP)