# Klarraum Gesundheit — Projekt-Handover

**Diese Datei ist das zentrale Projektgedächtnis für Klarraum Gesundheit.** Vor Änderungen an diesem Projekt zuerst lesen; danach den relevanten Abschnitt und den Changelog aktualisieren.

## 1. Identität und Ziel

- **Marke:** Klarraum Gesundheit
- **Domain:** `klarraum-gesundheit.de` (gesichert; Hosting und DNS noch nicht eingerichtet)
- **Zusatz:** KI-Kompetenz im Versorgungsalltag
- **Angebot:** Ein 75-minütiger Workshop für kleinere Einrichtungen im Gesundheitswesen. Ergebnis: gemeinsame Ampel-Logik, ausgefüllte KI-Richtlinie, Anwendungsverzeichnis und Teilnahmenachweis.
- **Zielgruppen:** Arztpraxen, MVZ, ambulante und stationäre Pflege, Hospiz- und Betreuungsvereine sowie Therapie- und Hebammenpraxen.
- **Abgrenzung:** Eigenständiges Projekt. Kein Bezug zu Werkspree, dessen Marke, Pseudonym, Domain, CRM, Formularen oder Infrastruktur.

## 2. Fachlicher Kern

- **Ampel:** Grün = kein Personenbezug und kein fachliches Risiko; Gelb = fachlich relevant, Prüfung durch zuständige Person; Rot = Personen- oder Behandlungsbezug, nicht in einen nicht freigegebenen Dienst eingeben.
- **Merksatz:** „Keine Namen. Keine Befunde. Kein ungeprüfter Text in ein Dokument.“
- **Tonalität:** nüchtern, knapp, ohne Angstrhetorik und ohne Beratersprache; konkrete Beispiele aus dem Versorgungsalltag, Sie-Ansprache.
- **Grenze:** allgemeine Schulung und Arbeitshilfen, keine Rechtsberatung im Einzelfall. Keine Patientendaten werden durch Klarraum verarbeitet.

## 3. Rechtlicher Rahmen

- Art. 4 KI-VO verpflichtet Anbieter und Betreiber zu Maßnahmen zur Förderung der KI-Kompetenz ihrer Beschäftigten bzw. weiterer für sie handelnder Personen. Die Maßnahme soll zum Wissen, zur Erfahrung und zum Einsatzkontext passen.
- Die Änderung durch Verordnung (EU) 2026/1744 ist zu berücksichtigen. Keine Aussage treffen, ein bestimmtes Zertifikat oder ein bestimmter Schulungsrhythmus sei gesetzlich vorgeschrieben.
- Nicht mit Bußgelddrohungen aus Art. 4 werben. Konkrete Fragen zu Vertrag, Haftung, Datenschutz oder beruflicher Verschwiegenheit an die zuständige Fachberatung verweisen.
- Rechtsaussagen vor Veröffentlichung und bei jeder materiellen Änderung gegen Primärquellen aktualisieren.

## 4. Stand der Dateien

- `index.html`: statischer, zugänglicher Landingpage-Entwurf; Canonical zeigt auf die gesicherte Domain. Absichtlich `noindex, nofollow`, ohne Formular, Tracking, Kontaktangaben oder Datenverarbeitung.
- `assets/logo-signal.svg`: ausgewähltes, skalierbares Zeichen „Signal“; drei abgestufte Signale im offenen Kreis, entsprechend der Ampel-Logik.
- `assets/logo-signal-concept.png`: ursprünglicher Bildentwurf zur gestalterischen Referenz.
- `README.md`: kompakte Launch-Checkliste.
- `impressum.html` und `datenschutz.html`: Pflichtseiten-Entwürfe mit den
  festgelegten Angaben zum Verantwortlichen. Die Datenschutzseite enthält bis
  zur Wahl des konkreten Hosting- und E-Mail-Anbieters eine sichtbare
  Veröffentlichungs-Sperre.
- `anfrage.php`: datensparsames, serverseitiges Anfrageformular mit
  Sitzungskennung, CSRF-Schutz, Honeypot und Versand an die Klarraum-Adresse.
  Es ist nur für einen HTTPS-fähigen eigenen Server ausgelegt; GitHub Pages
  kann PHP nicht ausführen.
- `dokumente/originale/` und `dokumente/gebrandete/`: unveränderte Quellen und
  daraus erzeugte Klarraum-Kopien. Das Signalzeichen steht unmittelbar vor dem
  Titel; das funktioniert auch bei Vorlagen mit unterdrücktem Kopfbereich.
- `scripts/brand_documents.py`: reproduzierbare Erstellung der Marken-Kopien;
  nach Veränderungen an Originalen oder Logo erneut ausführen und visuell prüfen.
- Die vier vom Eigentümer bereitgestellten Unterlagen (Richtlinie, Team-Handout, Nachweise, Leitfaden) sind fachliche Ausgangsbasis; keine Originaldatei ohne ausdrücklichen Auftrag verändern.

## 5. Veröffentlichungsgrenzen

1. Eigenes Hosting und DNS für `klarraum-gesundheit.de` einrichten; niemals die Werkspree-CNAME oder deren Deployment überschreiben.
2. Verantwortliche Kontaktangaben, Impressum und eine zum tatsächlichen Anfrageweg passende Datenschutzerklärung festlegen.
3. Anfrageweg bewusst wählen und datensparsam bauen; keine Übernahme des Werkspree-/Airtable-Flows ohne eigenständige Datenschutzentscheidung.
4. Rechtliche Inhalte sowie die Materialien fachlich final prüfen, insbesondere Rollenbegriff, Anwendungsbereich von § 203 StGB und Umgang mit Gesundheitsdaten.
5. Nebentätigkeit, Rechnungsstellung und Umsatzsteuerstatus klären.
6. Erst danach `noindex` entfernen, veröffentlichen und den vollständigen Anfrageweg testen.

## 6. Changelog

### 13.09.2026 — Pflichtseiten und Anfrageweg vorbereitet

- Impressum und Datenschutzerklärung sind als Entwürfe angelegt; die
  Verantwortlichenangaben wurden eingetragen. Die finale Benennung von
  Hosting- und E-Mail-Dienstleister bleibt eine Veröffentlichungsbedingung.
- Das Anfrageformular sammelt nur Organisations- und Kontaktdaten, weist vor
  sensiblen Daten ausdrücklich zurück und nutzt keine externe Formular- oder
  Tracking-Plattform. Die technische Zielumgebung ist ein eigener Server mit
  HTTPS und konfiguriertem E-Mail-Versand.

### 13.09.2026 — Abgrenzungsfeld von der Landingpage entfernt

- Das separate Feld zur allgemeinen Schulungs- und Beratungsgrenze wurde auf
  Wunsch entfernt. Der Bereich für Zielgruppen steht nun allein und führt
  ohne Leerraum in den vorbereitenden Anfragebereich.

### 13.09.2026 — Logo in Workshop-Dokumente übernommen

- Die vier gelieferten Workshop-Dokumente werden als unveränderte Quellen
  abgelegt und als Klarraum-Kopien mit Signalzeichen am Dokumenttitel erzeugt.
- Die Originale bleiben erhalten. Jede gebrandete Datei ist vor Übergabe als
  PDF zu rendern und mindestens auf dem Titelblatt visuell zu prüfen. Der
  Generator umgeht abweichende Kopfbereich-Einstellungen, damit das Logo auf
  allen vier Dokumenttypen sichtbar bleibt.

### 13.09.2026 — Landingpage visuell neu strukturiert

- Die Landingpage führt nun klar über Nutzen, Ampel, Ablauf, Unterlagen und
  Zielgruppen statt gleichwertiger Textblöcke. Logo, Navigation, Kontrast und
  responsive Reihenfolge wurden dabei überarbeitet.
- Der Veröffentlichungsschutz bleibt unverändert: `noindex, nofollow`, kein
  Formular, kein Tracking und keine Kontaktverarbeitung.

### 13.09.2026 — Handover und Logo-Auswahl angelegt

- Klarraum Gesundheit wurde aus der Werkspree-Handover herausgelöst und erhält diese eigene Projekt-Handover.
- Die Eigentümerentscheidung wählt die Logo-Richtung „Signal“. Das finale Website-Zeichen liegt als `assets/logo-signal.svg` vor; der Rasterentwurf bleibt als Referenz erhalten.
- Der Landingpage-Entwurf nutzt das neue Zeichen. Es bleibt unveröffentlicht und `noindex, nofollow`.
