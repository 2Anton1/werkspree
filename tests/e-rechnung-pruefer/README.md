# Tests: E-Rechnungs-Prüfer

Prüft die Auswertelogik von `/e-rechnung-pruefen/index.html` gegen Beispieldateien.
Die Tests laden die echte Seite in jsdom und schleusen Dateien durch denselben
Weg, den auch ein Besucher nimmt (Dateiauswahl → `change`-Event).

## Ausführen

```bash
cd tests/e-rechnung-pruefer
npm install jsdom pdfjs-dist@3.11.174
node test.mjs        # XML-Pfad: XRechnung (UBL) und ZUGFeRD (CII)
node pdf-test.mjs    # PDF-Pfad: Anhang-Extraktion aus ZUGFeRD-PDF
```

## Beispieldateien

| Datei | Zweck |
|---|---|
| `samples/xrechnung.xml` | vollständige XRechnung (UBL), muss als gültig durchgehen |
| `samples/zugferd.xml` | vollständige ZUGFeRD-Rechnung (CII), Profil EN 16931 |
| `samples/zugferd_minimum_kaputt.xml` | Profil MINIMUM, fehlender Käufer, falsche Summe — drei Fehler, alle müssen erkannt werden |
| `samples/zugferd.pdf` | PDF mit eingebetteter `factur-x.xml` |
| `samples/nur_pdf.pdf` | gewöhnliche PDF ohne strukturierte Daten — muss als „keine E-Rechnung" erkannt werden |

Alle Beispieldaten sind erfunden. Die Firmennamen, IBANs und Steuernummern
stammen nicht von realen Betrieben.
