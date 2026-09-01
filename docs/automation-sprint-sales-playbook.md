# Automation Sprint — Vertriebsablauf

Ziel: Eine freiwillige Anfrage innerhalb eines Werktags in einen klaren nächsten
Schritt führen. Der Ablauf gilt für den **Automation Sprint**: 890 € einmalig,
14 Tage, ein wiederkehrender Büroprozess. Preise gemäß § 19 Abs. 1 UStG ohne
Umsatzsteuerausweis.

## 1. Eingang dokumentieren

Eine erfolgreich von Formspree angenommene Website-Anfrage wird automatisch als
neuer Eintrag `Inbound · [Betrieb]` im produktiven Airtable-CRM angelegt. Der
Eintrag beginnt mit Status `Neu`; unvollständige Eingaben oder Honeypot-Treffer
werden nicht angelegt.

Bei einer Antwort bzw. beim ersten persönlichen Kontakt sofort ergänzen:

- Status: `Kontaktiert` (bis die weiterführenden Auswahleinträge im Airtable-
  Schema ergänzt sind)
- Quelle: Website / Empfehlung / Partner / sonstige Quelle in `Notes`
- Gewählter Prozess aus dem Formular
- Datum und nächster Kontaktzeitpunkt

## 2. Erste Antwort innerhalb eines Werktags

> Hallo [Name],
>
> danke für Ihre Anfrage zum Thema [Prozess]. Damit ich einschätzen kann, ob
> ein Automation Sprint sinnvoll ist, reichen mir drei kurze Angaben:
> 1. Wie oft fällt der Vorgang ungefähr pro Monat an?
> 2. Wie läuft er heute ab und welche Programme nutzen Sie dabei?
> 3. Wer prüft oder gibt das Ergebnis am Ende frei?
>
> Danach können wir in 15 Minuten klären, ob sich der Ablauf in zwei Wochen
> sauber umsetzen lässt. Viele Grüße, Finn Werksby

Keine nicht angeforderten Folgemails senden. Ein weiterer Kontakt erfolgt nur
als Antwort auf die freiwillige Anfrage oder nach einer ausdrücklich
vereinbarten Wiedervorlage.

## 3. 15-Minuten-Check

1. Den heutigen Ablauf und die verantwortliche Person verstehen.
2. Menge und Zeitaufwand grob erfassen; keine Einsparung versprechen.
3. Eine konkrete Quelle, ein Ziel und einen Freigabepunkt festlegen.
4. Datenschutz-, Buchhaltungs- und Fehlerrisiken ansprechen.
5. Entscheiden: Sprint anbieten, später wiederkommen oder freundlich absagen.

Ein Lead wird als `Qualifiziert` markiert, wenn der Prozess wiederkehrend ist,
eine zuständige Freigabeperson vorhanden ist, der Betrieb zwei Wochen für Tests
und Rückfragen einplant und der Nutzen für ihn nachvollziehbar ist.

## 4. Angebot

Nach einem qualifizierten Check wird ein kurzes, konkretes Angebot verschickt:

- Prozess und Ziel in einem Satz
- enthalten: Analyse, ein Workflow, drei Normalfälle plus ein Fehlerfall,
  Freigabeprozess und Übergabedokumentation
- nicht enthalten: fachliche Buchhaltungs-/Steuerprüfung, autonome Zahlungen,
  neue unvereinbarte Zusatzprozesse
- Preis: 890 € einmalig
- Start, benötigte Kundenzugänge und Abnahmekriterium

CRM-Status: `Angebot`. Erst nach Zahlung und verbindlichem Start: `Kunde`.
Eine Monatsbetreuung wird nur separat vereinbart und dann mit ihrem MRR im CRM
erfasst.

## 5. Wöchentliche Umsatzprüfung

Jeden Montag die Anzahl der Einträge für `Eingehend`, `Qualifiziert`, `Angebot`
und `Kunde` prüfen sowie die Summe der einmaligen Sprint-Umsätze und des MRR
notieren. Dabei Herkunft und Prozess vergleichen: Der Kanal mit qualifizierten
Gesprächen und Zahlungen erhält Vorrang, nicht der Kanal mit den meisten Klicks.
