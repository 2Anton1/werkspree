# Claude-Code-Prompt — Technische Aufgaben Werkspree

Erstellt 08.08.2026. Kopiere den Block unten in Claude Code (im Verzeichnis `~/werkspree`).
Die Aufgaben sind bewusst nach Dringlichkeit sortiert; Block 0 zuerst und einzeln.

---

## Block 0 — SOFORT, separat ausführen (Sicherheit)

```
Kontext: ~/werkspree ist ein Git-Repo, das nach GitHub gepusht wird und über
GitHub Pages öffentlich ausgeliefert wird. In HANDOVER.md standen bis Commit
d44443e ein SSH-Passwort und ein n8n-Passwort im Klartext. Sie wurden in einem
Folgecommit entfernt — stehen aber weiterhin in der Git-Historie und sind damit
für jeden lesbar, der das Repo klont.

Aufgabe:
1. Prüfe, ob das Repo 2Anton1/werkspree öffentlich ist (gh repo view --json visibility).
2. Liste mir alle Commits, die Secrets enthalten:
   git log --all -p -S"3266" -- HANDOVER.md
   Prüfe zusätzlich auf: API-Keys (pat, sk_live, pk_live, eyJhbG), weitere Passwörter.
3. Erkläre mir die Optionen, ohne eine davon eigenmächtig auszuführen:
   a) Repo auf privat stellen (GitHub Pages braucht dann Pro)
   b) Historie mit git-filter-repo bereinigen und force-pushen
   c) Repo neu anlegen ohne Historie
4. WICHTIG, unabhängig von der gewählten Option: Die Passwörter gelten als
   kompromittiert und müssen rotiert werden. Erstelle mir eine Checkliste:
   SSH-Passwort des Hetzner-Servers (91.98.174.183, user anton), n8n-Login,
   und prüfe ob Stripe-/Airtable-/n8n-Keys ebenfalls je im Repo lagen.
5. Ergänze .gitignore und lege einen Pre-Commit-Hook an, der Commits mit
   typischen Secret-Mustern (sk_live_, pk_live_, pat[A-Za-z0-9], BEGIN PRIVATE KEY,
   "SSH: user=", "pw=") blockiert.

Führe Schritt 1, 2 und 5 aus. Für 3 und 4 gib mir nur die Analyse und
Empfehlung — ich entscheide, bevor irgendetwas an der Historie passiert.
```

---

## Block 1 — Landing Page technisch fertigstellen

```
Kontext: ~/werkspree, statische Seite auf GitHub Pages, index.html mit inline
CSS/JS, dazu impressum.html und datenschutz.html. Zielgruppe sind Handwerks-
und Kleinbetriebe in Berlin/Brandenburg. Strategische Begründung der Aufgaben
steht in HANDOVER.md Abschnitt 12 — lies den zuerst.

Aufgaben:

1. Formspree scharf schalten
   In index.html steht im Kontaktformular der Platzhalter
   action="https://formspree.io/f/FORM_ID_HIER_EINTRAGEN".
   Frage mich nach der echten Form-ID und trage sie ein. Prüfe danach, dass der
   Fallback-Zweig in der Submit-Logik (Platzhalter-Erkennung) nicht mehr greift.

2. og:image ergänzen
   Beim Teilen per WhatsApp oder LinkedIn erscheint aktuell eine leere Vorschau.
   Erzeuge ein 1200x630-Bild im Stil der Seite (Farben: --primary #122c4d,
   --accent #1f9d74; Text "Werkspree — KI-Automatisierung für kleine Unternehmen",
   darunter "Berlin & Brandenburg"). Erzeuge es programmatisch, z.B. als SVG und
   per rsvg-convert/ImageMagick nach PNG, und lege es als og-image.png ab.
   Ergänze og:image, og:url, og:site_name, twitter:card=summary_large_image.
   Verifiziere die Bildgröße mit `identify` oder Python/PIL.

3. SEO-Grundlagen
   - robots.txt (Impressum und Datenschutz auf noindex belassen)
   - sitemap.xml mit index.html
   - canonical-Link
   - JSON-LD, Typ ProfessionalService: Name, Beschreibung, areaServed
     (Berlin, Brandenburg), Anbieter, E-Mail, angebotene Leistungen mit Preisen.
     ACHTUNG: Die Adresse im Impressum (Halle/Saale) weicht vom beworbenen
     Einsatzgebiet (Berlin/Brandenburg) ab. Trage im JSON-LD als address die
     echte Impressumsadresse ein und als areaServed Berlin/Brandenburg —
     erfinde keine Berliner Adresse. Weise mich auf den Widerspruch hin.
   - Validiere das JSON-LD mit einem lokalen JSON-Parser (nicht raten).

4. FAQ-Sektion
   Neue Sektion vor dem Kontaktbereich, gleiche Designsprache (Karten, data-reveal,
   Accordion mit <details>/<summary>, tastaturbedienbar). Fünf Fragen, Antworten
   ehrlich und ohne Marketingsprache:
   - Was passiert mit meinen Daten? Wo werden sie verarbeitet?
   - Wer haftet, wenn die KI eine Rechnung falsch erfasst?
   - Wie lange binde ich mich? Wie kündige ich?
   - Was, wenn es bei meinem Betrieb nicht funktioniert?
   - Wie lange dauert die Einrichtung?
   Wenn du eine Antwort inhaltlich nicht aus HANDOVER.md belegen kannst, schreib
   sie nicht — frag mich. Erfinde keine Zusagen zu Laufzeit, Haftung oder Fristen.

5. Zugänglichkeit und Qualität prüfen
   - Kontrastverhältnisse der neuen Formularelemente auf dem dunklen Verlauf
     rechnerisch prüfen (WCAG AA, 4.5:1 für Text)
   - Formular komplett per Tastatur bedienbar, sichtbarer Fokus-Ring
   - HTML-Struktur validieren (Parser, nicht Augenmaß)
   - Seite mit einem lokalen Server öffnen und bei 375px und 1440px Breite
     prüfen, dass nichts überläuft

Arbeite die Punkte einzeln ab und zeig mir nach jedem den Diff. Ändere keine
Preise, keine Stripe-Links und keine Rechtstexte ohne Rückfrage.
```

---

## Block 2 — Rechnungs-OCR reparieren

```
Kontext: n8n läuft auf https://n8n.anton-drooff.de (API-Key in ~/.hermes/.env
als N8N_API_KEY). Workflow "Rechnungs-OCR Demo", ID bj8yGBoDgrSkRPKR, lokal
gespiegelt in ~/werkspree/n8n-workflows/rechnungs-ocr-demo.json.

Bekannter Bug (HANDOVER.md 2.3): Der Code-Node extrahiert unvollständig, wenn
das JSON als String ankommt — die RegEx greifen nicht über \n hinweg.

Wichtig: Auf demselben Server laufen pv-ki.de, anton-drooff.de und
career-tool.pv-ki.de. Diese NICHT anfassen.

Vorgehen — bitte testgetrieben, nicht raten:
1. Hol den aktuellen Workflow über die n8n-API und zeig mir den Code-Node.
2. Extrahiere die Parser-Logik in eine eigenständige JS- oder Python-Datei
   unter ~/werkspree/n8n-workflows/, sodass sie lokal ohne n8n läuft.
3. Schreib ZUERST Testfälle, die den Bug reproduzieren. Mindestens:
   - Eingabe als echtes JSON-Objekt
   - Eingabe als JSON-String mit \n
   - Eingabe mit fehlender USt-Zeile
   - Eingabe mit deutschem Zahlenformat (1.234,56)
   - Eingabe mit IBAN mit und ohne Leerzeichen
   - leere/unlesbare Eingabe (muss sauber scheitern, nicht crashen)
   Zeig mir, dass die Tests mit dem alten Code fehlschlagen, BEVOR du fixt.
4. Fixe, bis alle Tests grün sind. Zeig mir die Testausgabe.
5. Spiel den Fix über die n8n-API zurück und lös eine echte Test-Execution
   über den Webhook aus. Prüf über die API, dass der Execution-Status success
   ist UND dass alle erwarteten Felder im Airtable-Record gefüllt sind —
   "hat nicht gecrasht" reicht nicht als Beleg.
6. Committe die Testdatei mit.
```

---

## Block 3 — E-Mail-Yield der Lead-Pipeline

```
Kontext: ~/werkspree/scraper/pipeline.py scrapet GelbeSeiten und sucht danach
auf der Firmenwebsite unter /impressum nach einer E-Mail-Adresse. Ergebnis
laut ~/werkspree/scraper/data/leads_20260808.json: 2 von 50 Leads haben eine
E-Mail (4%). Firecrawl-Credits sind begrenzt (~1024).

WICHTIG vorab: Bevor du irgendetwas am Outreach änderst — der E-Mail-Versand
selbst ist rechtlich ungeklärt (§ 7 UWG, siehe HANDOVER.md 12.7). Diese Aufgabe
betrifft ausschließlich die Datenqualität, nicht das Versenden. Starte keinen
Versand und aktiviere keine Cron-Jobs.

Aufgaben:
1. Analysiere zuerst, WARUM der Yield so niedrig ist. Nimm die 48 Leads ohne
   E-Mail und finde heraus, woran es scheitert — keine Website im Datensatz,
   /impressum existiert nicht unter dem Pfad, E-Mail als Bild, Kontaktformular
   statt Adresse, Scrape fehlgeschlagen? Gib mir eine Aufschlüsselung mit Zahlen.
   Erst danach optimieren.
2. Verbessere die Extraktion auf Basis dieser Analyse. Naheliegend:
   alternative Pfade (/kontakt, /impressum.html, /ueber-uns), Suche auf der
   Startseite, mailto:-Links im HTML, obfuskierte Adressen ("info [at] firma.de").
   Miss den Yield vorher/nachher am selben Datensatz und zeig mir beide Zahlen.
3. Bau ein Funnel-Reporting (~/werkspree/scraper/funnel.py): gescrapt →
   Website gefunden → E-Mail gefunden → kontaktiert → geantwortet → Kunde.
   Quelle sind die Airtable-Daten (Base appyMLhXOMHpD5vfT, Table tbluCUpuCPxW1GcWD,
   Key in ~/.hermes/.env). Ausgabe als Tabelle auf der Konsole. Dieses Reporting
   hätte das 4%-Problem früher sichtbar gemacht.
4. Telefonnummern: Prüfe, bei wie vielen Leads eine Telefonnummer vorliegt.
   Falls das deutlich mehr sind als E-Mails, schreib mir eine kurze Notiz mit
   den Zahlen ins HANDOVER.md — das ist ein Argument für telefonischen
   Erstkontakt.

Achte auf die Firecrawl-Credits: teste an einer Stichprobe von 10 Leads,
nicht am ganzen Datensatz. Sag mir vorher, wie viele Credits ein Durchlauf kostet.
```

---

## Block 4 — Outreach-Templates korrigieren (Textfehler, kein Versand)

```
Kontext: ~/werkspree/scraper/email_templates.json.
KEIN Versand, keine Cron-Aktivierung — nur die Texte korrigieren.

Bekannte Fehler (HANDOVER.md 12.7):
1. Anrede nutzt {company_name}: "Guten Tag Blachnierz & Söhne
   Elektroinstallationsges. mbH" — liest sich als Serienbrief. Ersetze durch
   "Sehr geehrte Damen und Herren", solange kein Ansprechpartner bekannt ist.
2. followup_7days nennt hallo@werkspree.bki-de.de — dieses Postfach existiert
   nicht. Ersetze durch a2807d@gmail.com oder frag mich nach der echten Adresse.
3. Signatur und Fließtext verlinken https://2anton1.github.io/werkspree/ —
   ersetze durch die Produktivdomain. Frag mich, welche das sein soll.
4. Tippfehler in followup_3days: "Ich kümmere um den Rest" → "Ich kümmere mich
   um den Rest".
5. Der Satz "Ich habe mir Ihre Website angesehen" ist nachweislich unzutreffend,
   die Pipeline liest nur das Impressum. Streiche oder ersetze ihn durch etwas,
   das tatsächlich stimmt.
6. Es fehlt ein Abmeldehinweis. Ergänze einen.

Zeig mir die überarbeiteten Templates im Diff, bevor du speicherst.
```

---

## Hinweise für jeden Block

- **Nichts eigenmächtig live schalten.** Kein Cron aktivieren, kein Outreach
  starten, keine Zahlung auslösen, kein force-push.
- **Verifizieren statt behaupten.** Jede Aussage "funktioniert jetzt" braucht
  eine Ausgabe, die das belegt — Testlauf, API-Response, Parser-Ergebnis.
- **Preise, Stripe-Links und Rechtstexte** (impressum.html, datenschutz.html)
  nur nach Rückfrage ändern.
- **Server-Regel:** pv-ki.de, anton-drooff.de, career-tool.pv-ki.de auf dem
  Hetzner-VPS nicht anfassen.
- **Änderungen im Changelog** von HANDOVER.md (Abschnitt 10) festhalten.
