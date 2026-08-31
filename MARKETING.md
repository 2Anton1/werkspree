# Werkspree — Marketing-Strategie für 3 SaaS-Produkte

Stand: 31.08.2026

## Die 3 Produkte im Überblick

| Produkt | URL | Free | Pro | Zielgruppe |
|---|---|---|---|---|
| E-Rechnungs-Prüfer | /e-rechnung-pruefen/ | Einzelprüfung im Browser | 29€/Monat: Auto-Mail-Forward | Alle Betriebe mit E-Rechnungspflicht |
| Microsite-Generator | /website-bau/ | Vorschau mit Wasserzeichen | 19€/Monat: Eigene Domain, Hosting | Handwerker ohne/wenig Website |
| Rechnungs-OCR Mail-Service | /rechnungs-ocr/ | → Free-Prüfer | 39€/Monat: Mail-Forward + CSV | Betriebe mit vielen Eingangsrechnungen |

---

## 1. SEO-Strategie

### 1.1 Suchvolumen & Keywords (pro Produkt)

**E-Rechnungs-Prüfer** (höchstes Volumen — Trend-Thema 2025-2028):
- `e-rechnung prüfen` (~3.000/Monat geschätzt)
- `e-rechnung kostenlos` (~1.500)
- `zugferd prüfen` (~800)
- `xrechnung prüfen` (~600)
- `e-rechnung pflicht kleinunternehmer` (~1.200)
- **Long-Tail:** `e-rechnung prüfen kostenlos browser`, `xrechnung xml prüfen online`
- **Content-Hebel:** /e-rechnung/ informiert über Fristen → Free-Prüfer als Lead-Magnet → Pro-Upgrade

**Microsite-Generator:**
- `website erstellen handwerker` (~500)
- `branchen-website` (~300)
- `microsite generator` (~200)
- `website für handwerker kostenlos` (~400)
- **Long-Tail:** `website erstellen malerbetrieb`, `website für elektriker kostenlos`
- **Content-Hebel:** 17 Branchen-Pages (jede mit eigenem Keyword)

**Rechnungs-OCR Mail-Service:**
- `rechnungen automatisch erfassen` (~800)
- `rechnungs-ocr` (~500)
- `belegscan` (~1.000, hoher Wettbewerb)
- `rechnung scannen excel` (~600)
- **Long-Tail:** `eingangsrechnungen automatisch erfassen kleinunternehmen`

### 1.2 On-Page SEO (umgesetzt)

- ✅ Meta description, keywords, author auf allen Seiten
- ✅ Canonical URLs
- ✅ Open Graph + Twitter Card Tags
- ✅ JSON-LD Schema.org: `WebApplication`, `FAQPage`, `ProfessionalService`, `BreadcrumbList`
- ✅ Sitemap.xml mit allen Seiten + lastmod
- ✅ robots.txt erlaubt alle Crawler
- ✅ Mobile-responsive (Hamburger-Menü)
- ✅ Semantisches HTML (section, nav, header, footer, main)

### 1.3 Content-Strategie (noch aufbauen)

**Blog / Ratgeber-Content** (nächster Schritt):
- `/blog/e-rechnung-pflicht-2027/` — Detail-Artikel zur Frist
- `/blog/e-rechnung-kleinunternehmer/` — Was Kleinunternehmer wissen müssen
- `/blog/website-fuer-handwerker/` — Warum eine Website wichtig ist
- `/blog/rechnung-automatisieren/` — Wie Mail-Forward funktioniert

**Branchen-Landingpages** (für Microsite-Generator):
- `/website-bau/elektriker/` — "Website für Elektriker"
- `/website-bau/dachdecker/` — "Website für Dachdecker"
- `/website-bau/maler/` — etc. (17 Stück)

### 1.4 Technisches SEO

- ⚠️ HTTPS-Enforcement aktivieren (GitHub Pages Setting — sobald Zertifikat bereit)
- ✅ SSL-Zertifikat: aktiv (seit 09.08.2026)
- ⚠️ Page Speed:_inline CSS ist groß (~75KB), aber keine render-blockierenden externen Ressourcen außer Google Fonts
- ✅ Kein Tracking-Cookie (nur fire-and-forget n8n-Webhook)

---

## 2. Lead-Pipeline-Strategie

### 2.1 Bestehende Pipeline (Lead-Scraper → Outreach)

Die Lead-Pipeline scrapet GelbeSeiten nach Branchen+Region, scored Leads nach Warmth, und sendet personalisierte E-Mails. Für die neuen Produkte:

**Anpassung der Warmth-Scoring-Parameter:**
- `no_website` → Microsite-Generator Lead (hat keine Website → braucht eine)
- `has_website` + `mentions_accounting` → Rechnungs-OCR Lead
- `has_website` + `no_e-rechnung` → E-Rechnungs-Prüfer Lead

**Outreach-Templates pro Produkt:**

```
Microsite-Generator:
"Wir haben für {company_name} eine kostenlose Demo-Website erstellt —
in 5 Minuten generiert, branchenspezifisch gestaltet.
Ansehen: {url}
Bei Interesse: Anpassung für 19€/Monat mit eigener Domain."

Rechnungs-OCR:
"Wussten Sie, dass Sie eingehende Rechnungen ab 2025 als E-Rechnung
entgegennehmen müssen? Unser Mail-Service erfasst und prüft sie
automatisch — 14 Tage kostenlos testen.

E-Rechnungs-Prüfer:
"Kostenlose E-Rechnungs-Prüfung direkt im Browser — ohne Upload,
ohne Anmeldung: {url}
Gefällt es? Wir automatisieren den gesamten Prozess für 29€/Monat."
```

### 2.2 Microsite-Pipeline als Lead-Magnet

Die bestehende Microsite-Pipeline baut bereits Demo-Websites für Heißleads und verschickt sie per Mail. Das ist der perfekte Lead-Magnet:

1. **Kostenlose Demo-Website** → Lead sieht Wert
2. **Follow-up-Mail** → "Gefällt die Website? Für 19€/Monat mit eigener Domain."
3. **Upsell-Pfad:** Website → Rechnungs-OCR → KI-Paket (Starter/Growth/Enterprise)

### 2.3 Cross-Selling-Strategie

```
E-Rechnungs-Prüfer (Free) 
  → Pro (29€): Automatische Prüfung
  → Upsell: Rechnungs-OCR Mail-Service (39€): Vollständige Erfassung
  → Upsell: KI Starter (290€): Komplette Automatisierung

Microsite-Generator (Free)
  → Pro (19€): Eigene Domain
  → Upsell: KI Starter (290€): Website + Rechnungs-OCR + Chatbot

Rechnungs-OCR (Free → Prüfer)
  → Pro (39€): Mail-Forward
  → Upsell: KI Growth (790€): + Mahnwesen + Chatbot
```

**Kunde kommt über ein günstiges Produkt (19-39€) rein, wird dann zum
teureren Paket (290-1900€) upsolded.** Das günstige Produkt ist der
Fuß-in-der-Tür.

---

## 3. Automatisierungs-Pipeline für neues SaaS

### 3.1 Inbound: Formular-Eingang → CRM

1. Besucher füllt Formular auf /website-bau/ aus
2. n8n-Webhook empfängt Daten → generiert Microsite → sendet Vorschau
3. Lead wird in Airtable-CRM gespeichert (Tabelle: "SaaS-Leads")
4. Follow-up-Mails nach 3 und 7 Tagen (automatisiert)

### 3.2 Inbound: Stripe-Webhook

1. Kunde zahlt für Pro (Stripe Payment Link)
2. Stripe-Webhook → n8n → Airtable-Update (Status: "Kunde")
3. Automatisierte Onboarding-Mail mit Einrichtungs-Anleitung

### 3.3 Inbound: E-Rechnungs-Prüfer → Mail-Service

1. Besucher prüft Rechnung kostenlos
2. "Möchten Sie das automatisch für alle Rechnungen?" → CTA
3. Klick → /rechnungs-ocr/ → Stripe-Checkout
4. Nach Zahlung: Onboarding-Mail mit Weiterleitungs-Adresse

---

## 4. Paid-Ads (optional, später)

- **Google Ads:** Targeting auf "E-Rechnung prüfen", "Rechnungs-OCR" — 
  hohe Intent-Suchanfragen, direkte Conversion
- **Budget:** 50-100€/Monat für Testphase
- **Landingpage:** /e-rechnung-pruefen/ (bereits konversionsoptimiert mit Free/Pro)

---

## 5. E-Mail-Marketing (Bestand)

- **Outreach-Pipeline:** 10 Mails/Tag an warme Leads (bestehend)
- **Follow-up-Zyklus:** 3 Tage, 7 Tage, 14 Tage (erweiterbar)
- **Pro-Tipp:** Microsite-Demo-Mail = 3x höhere Response-Rate als normale Outreach-Mail

---

## 6. Partnerschaften (langfristig)

- **Steuerberater & Buchhalter:** Empfehlen Rechnungs-OCR an ihre Mandanten
  → Provision (10% monatlich, solange Kunde aktiv)
- **Web-Agenturen:** Empfehlen Microsite-Generator → Whitelabel möglich
- **Handwerkskammern:** Vorträge über E-Rechnungspflicht → Lead-Generierung

---

## 7. KPIs & Tracking

| Metrik | Ziel (Monat 1-3) | Quelle |
|---|---|---|
| Besucher /e-rechnung-pruefen/ | 200/Monat | n8n-Tracking |
| Free-Prüfungen | 50/Monat | n8n-Tracking |
| Pro-Abos (E-Rechnung) | 3/Monat | Stripe |
| Microsite-Generierungen | 30/Monat | n8n-Tracking |
| Microsite-Pro-Abos | 2/Monat | Stripe |
| Rechnungs-OCR Pro | 2/Monat | Stripe |
| Conversion Free→Paid | 5-10% | berechnet |

**Tracking-Events (n8n-Webhook):**
- `page_view` (alle Seiten)
- `checker_used` (E-Rechnungs-Prüfer)
- `gen_form_submit` (Microsite-Generator)
- `stripe_click` (alle Stripe-Links)
- `form_submit` (Kontaktformular)

---

## 8. Nächste Schritte (Priorität)

1. **n8n-Workflow importieren:** `/n8n-workflows/microsite_generator.json` in n8n-UI importieren und aktivieren (per API erstellter Workflow hat Respond-Node-Problem)
2. **Branchen-Landingpages:** 17 Unterseiten für Microsite-Generator SEO
3. **Blog-Artikel:** E-Rechnungspflicht 2027, Kleinunternehmer-Leitfaden
4. **A/B-Test:** Free vs Pro CTA-Positionierung auf E-Rechnungs-Prüfer
5. **Google Search Console:** Sitemap einreichen
6. **Stripe-Webhook:** n8n → Airtable-Update bei Zahlung
