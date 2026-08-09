# Marketingstrategie Werkspree — was ein Agent allein betreiben kann

**Stand:** 09.08.2026
**Rahmen (von Anton vorgegeben):** 0 € Budget, Live-Deployment ohne Vorabfreigabe, Umsetzung startet sofort.

---

## 1. Die Ausgangslage bestimmt die Strategie, nicht umgekehrt

Der Rahmen "0 € und ohne Anton" schließt fast alles aus, was in Abschnitt 12.6 des Handovers als hoher Hebel steht. Deshalb zuerst die Trennung, bevor irgendein Kanal vorgeschlagen wird:

### Geht nicht ohne Anton

| Kanal | Warum blockiert |
|---|---|
| Steuerberater-Kooperation | Der größte Hebel überhaupt. Braucht ein Gespräch zwischen zwei Menschen. Eine Mail von einem Agenten an eine Kanzlei erreicht das Gegenteil. |
| Innung / Handwerkskammer | Vortrag, Mitgliedschaft, Beitrag im Mitgliedermagazin — persönlicher Kontakt und Verbandszugang. |
| Telefonakquise | Es muss jemand sprechen. |
| Google Business Profile | Verifizierung per Postkarte oder Anruf an die Betriebsadresse. |
| Referenzkunde, Fallstudie | Setzt einen Verkauf voraus. |
| Google Ads, eigene .de-Domain, Cal.com | Kostet Geld. Bei 0 € raus. |

### Geht gar nicht — unabhängig davon, wer es macht

**Kaltakquise per E-Mail.** § 7 UWG untersagt Werbung per E-Mail ohne vorherige ausdrückliche Einwilligung, auch im B2B. Die "mutmaßliche Einwilligung" ist eine enge Ausnahme, auf die sich Gerichte selten stützen. Das ist im Handover unter 12.7 bereits vermerkt und dort als "vor dem Scharfschalten anwaltlich klären" markiert. Ich schalte nichts scharf und ich versende nichts. Ein Agent, der im Dauerbetrieb ungefragt Werbemails an gescrapte Adressen schickt, produziert Abmahnungen, keine Kunden.

> **Bitte prüfen:** Der Cron-Job `e1e5b8283664` ("Werkspree Lead Pipeline", täglich 10:00) ist im Handover mit "Neue Leads scrapen **+ E-Mails versenden**" beschrieben. An anderer Stelle steht, Outreach sei nie gestartet worden. Falls der Versand-Teil aktiv ist, gehört er abgeschaltet, bis die Rechtsfrage geklärt ist. Das kann ich von hier aus nicht einsehen — es ist Hermes' Cron, nicht meiner.

**Posten in Facebook- und WhatsApp-Gruppen unter dem Pseudonym.** Ein Agent, der sich als "Finn Werksby" in Handwerkergruppen ausgibt und dort das eigene Angebot empfiehlt, ist verdeckte Eigenwerbung. Mache ich nicht, auch wenn es technisch ginge.

### Bleibt übrig

Genau ein Kanal, und der ist ausgerechnet der, der zu einem Agenten passt: **eingehende Anfragen über Inhalte und kostenlose Werkzeuge auf der eigenen Seite.** Kein Budget, kein menschlicher Kontakt nötig, rechtlich unproblematisch, und der Aufwand ist Schreiben und Programmieren — beides skaliert.

---

## 2. Die Strategie in einem Satz

Werkspree hört auf, sich als "KI-Automatisierung" zu bewerben, und wird stattdessen zu der Seite, die eine konkrete Frage der Zielgruppe besser beantwortet als alle anderen: **was die E-Rechnungspflicht für einen kleinen Handwerksbetrieb bedeutet.**

Warum ausgerechnet dieses Thema:

- Es ist ein Zwang, kein Wunsch. Wer googelt, sucht nicht nach Inspiration, sondern nach einer Antwort auf eine Frist.
- Die Frist ist akut. Ab **1. Januar 2027** müssen Unternehmen E-Rechnungen ausstellen, deren Umsatz **im Vorjahr über 800.000 €** lag — das Vorjahr ist das laufende Jahr 2026. Wer jetzt sucht, entscheidet in den nächsten Monaten.
- Es führt ohne Umweg zum Angebot. Wer E-Rechnungen empfangen und verarbeiten muss, hat genau das Problem, das das Starter-Paket löst.
- Der Suchbegriff ist deutlich weniger umkämpft als "KI-Automatisierung", wo Werkspree gegen Konzernbudgets antritt.

Das löst nebenbei einen Teil des Kernproblems aus Handover 12.1: Eine Seite, die eine Rechtsfrage sauber und belegt beantwortet, erzeugt Vertrauen. Eine Seite, die "wir garantieren messbare Ergebnisse" ruft, nicht.

---

## 3. Die vier Bausteine

### 3.1 Ratgeber-Seite zur E-Rechnungspflicht

Eine eigenständige Seite unter `/e-rechnung/`, die die Frage tatsächlich beantwortet — Fristen, wer wann was muss, was Kleinunternehmer betrifft, was ein PDF ist und was nicht. Mit Quellenangabe (BMF-Schreiben vom 15.10.2025) und ohne Werbeversprechen. Der Verkauf steht am Ende der Seite, nicht am Anfang.

Der entscheidende Unterschied zu einem Werbetext: Diese Seite ist auch dann nützlich, wenn der Leser nichts kauft. Genau deshalb wird sie verlinkt und weiterempfohlen.

### 3.2 Kostenloses Werkzeug: E-Rechnungs-Prüfer

Unter `/e-rechnung-pruefen/`. Der Nutzer zieht eine XRechnung-XML oder eine ZUGFeRD-PDF ins Fenster und bekommt ausgewertet, ob die Pflichtangaben nach EN 16931 vorhanden sind und was drinsteht.

Drei Gründe, warum das der stärkste Baustein ist:

1. **Es läuft vollständig im Browser.** Die Datei wird nirgendwo hochgeladen. Bei Buchhaltungsdaten ist das nicht bloß ein technisches Detail, sondern das Verkaufsargument — die Datenschutzfrage ist laut Handover 12.5 die erste, die diese Zielgruppe stellt.
2. **Es beweist Kompetenz, statt sie zu behaupten.** Ein Betrieb, der gerade eine E-Rechnung erhalten hat und nicht weiß, was er damit anfangen soll, erlebt in dreißig Sekunden, dass hier jemand die Sache beherrscht. Das ersetzt keine Referenz, kommt ihr aber näher als jeder Slogan.
3. **Es kostet nichts im Betrieb.** Statische Seite auf GitHub Pages, keine Server, keine API-Kosten, keine Wartung.

### 3.3 Auffindbarkeit technisch nachziehen

Sitemap, interne Verlinkung, Navigation, strukturierte Daten. Zusätzlich eine `llms.txt` — ein zunehmender Teil dieser Suchanfragen landet inzwischen bei Sprachmodellen statt bei Google, und eine klar strukturierte Faktenseite hat dort bessere Chancen, zitiert zu werden, als eine Werbeseite.

### 3.4 Dauerbetrieb

Ein Cron-Job, der die Rechtslage in Abständen gegen die Quellen prüft und die Seite aktualisiert, wenn sich etwas ändert. Eine veraltete Frist auf einer Ratgeberseite ist schlimmer als keine Seite.

Was ich bewusst **nicht** einrichte: einen Job, der monatlich automatisch Blogbeiträge generiert. Fünfzig maschinell erzeugte Seiten über "KI im Handwerk" sind für Google erkennbarer Füllstoff und schaden der Domain mehr, als sie nützen. Zwei Seiten, die stimmen, schlagen fünfzig, die nur existieren.

---

## 4. Was das realistisch bringt

Eine ehrliche Erwartung, weil eine unehrliche später teurer wird:

Die Domain ist neu, hat keine eingehenden Links und ist eine Subdomain eines fremden Projekts. Für Suchmaschinen ist das ein schwaches Signal. Bis eine neue Seite überhaupt indexiert und bewertet ist, vergehen Wochen bis Monate. Es ist gut möglich, dass in den ersten drei Monaten **null** Anfragen darüber kommen.

Was dafür spricht, es trotzdem zu tun: Es kostet 0 € und keine Stunde Deiner Zeit, es verfällt nicht, und es ist der einzige Kanal, den ich überhaupt allein betreiben kann. Verglichen mit der Alternative — nichts tun oder rechtswidrig Mails versenden — ist die Rechnung eindeutig.

Der ehrlichere Satz dazu: **Marketing ist derzeit nicht der Engpass.** Der Engpass sind die fehlende Referenz und die Lieferfähigkeit (Handover 12.8: ein Workflow existiert, drei Pakete sind verkauft). Wenn morgen zehn Anfragen kämen, könnte Werkspree neun davon nicht bedienen. Was ich hier baue, ist die Vorarbeit für den Moment, in dem Du die Schritte 1 bis 7 aus Handover 12.9 gemacht hast — nicht ihr Ersatz.

---

## 5. Was ich Dir nicht abnehmen kann, in Reihenfolge des Hebels

1. Ein Gespräch mit zwei, drei Steuerberatern in Berlin. Eine Kanzlei mit Handwerksmandanten hat das Vertrauen, das Werkspree fehlt, und ein Eigeninteresse an vorerfassten Belegen.
2. Den ersten Kunden — notfalls kostenlos, gegen Freigabe von Name, Zitat und Zahlen.
3. Die Rechtsfrage zum Outreach klären oder den Zweig stilllegen.
4. Entscheiden, ob "Finn Werksby" als Absendername bleibt. Ein Impressum mit Anton Drooff neben Mails von Finn Werksby ist für den Empfänger ein Widerspruch, und Widersprüche kosten genau das Vertrauen, das die ganze Übung erzeugen soll.

---

## 6. Quellen für die Rechtsangaben auf der Ratgeber-Seite

- BMF-Schreiben vom 15.10.2025 zur Einführung der obligatorischen E-Rechnung: https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Steuerarten/Umsatzsteuer/Umsatzsteuer-Anwendungserlass/2025-10-15-einfuehrung-obligatorische-e-rechnung.pdf
- Zentralverband des Deutschen Handwerks, Fachbereich Steuern und Finanzen: https://www.zdh.de/ueber-uns/fachbereich-steuern-und-finanzen/elektronische-rechnung/
- Bundessteuerberaterkammer, FAQ zur E-Rechnung: https://www.bstbk.de/downloads/bstbk/steuerrecht-und-rechnungslegung/fachinfos/BStBK_FAQ_E-Rechnung_final.pdf

Alle Rechtsangaben auf der Seite werden auf diese Quellen zurückgeführt und sind als Information gekennzeichnet, nicht als Rechtsberatung.
