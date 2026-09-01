const test = require('node:test');
const assert = require('node:assert/strict');
const { extractRechnungsdaten } = require('./rechnungs-ocr-parser.js');

const FULL_INVOICE_TEXT = [
  'Musterfirma GmbH',
  'Rechnungsnummer: RE-2026-00123',
  'Rechnungsdatum: 01.03.2026',
  'Zahlungsziel: 15.03.2026',
  'Gesamtbetrag: 1.234,56 EUR',
  'USt: 19,00%',
  'IBAN: DE89 3704 0044 0532 0130 00',
  'BIC: COBADEFFXXX',
].join('\n');

test('echtes JSON-Objekt: extrahiert alle Felder korrekt', () => {
  const result = extractRechnungsdaten({ text: FULL_INVOICE_TEXT });
  assert.equal(result.rechnungsnummer, 'RE-2026-00123');
  assert.equal(result.datum, '01.03.2026');
  assert.equal(result.faelligkeit, '15.03.2026');
  assert.equal(result.betrag, '1.234,56');
  assert.equal(result.ust, '19,00');
  assert.equal(result.iban.replace(/\s+/g, ''), 'DE89370400440532013000');
  assert.equal(result.bic, 'COBADEFFXXX');
  assert.equal(result.absender, 'Musterfirma GmbH');
  assert.equal(result.konfidenz, 100);
});

test('echte n8n-Webhook-Form: Body liegt verschachtelt unter .body (kein Top-Level-Feld)', () => {
  // So sieht $input.first().json in Produktion tatsaechlich aus: der Webhook-Node
  // packt Header/Query/Body in ein Huellobjekt, der eigentliche POST-Body liegt
  // als verschachteltes Objekt unter .body, nicht flach unter .text.
  const result = extractRechnungsdaten({
    headers: { 'content-type': 'application/json' },
    params: {},
    query: {},
    body: { text: FULL_INVOICE_TEXT },
    webhookUrl: 'https://n8n.anton-drooff.de/webhook/rechnung-ocr',
    executionMode: 'production',
  });
  assert.equal(result.rechnungsnummer, 'RE-2026-00123');
  assert.equal(result.betrag, '1.234,56');
  assert.equal(result.absender, 'Musterfirma GmbH');
});

test('JSON-String mit \\n: ganzer Payload kommt als String an (nicht als Objekt)', () => {
  // Simuliert einen Webhook-Aufruf, bei dem der Body als rohe JSON-Zeichenkette
  // ankommt statt als geparstes Objekt, mit escaped \n statt echten Zeilenumbruechen.
  const rawString = JSON.stringify({ text: FULL_INVOICE_TEXT.replace(/\n/g, '\\n') });
  const result = extractRechnungsdaten(rawString);
  assert.equal(result.rechnungsnummer, 'RE-2026-00123');
  assert.equal(result.datum, '01.03.2026');
  assert.equal(result.betrag, '1.234,56');
  assert.equal(result.absender, 'Musterfirma GmbH');
});

test('Webhook-Body als JSON-String: verschachtelter Body wird ebenfalls geparst', () => {
  const result = extractRechnungsdaten({
    headers: { 'content-type': 'text/plain' },
    body: JSON.stringify({ text: FULL_INVOICE_TEXT }),
  });
  assert.equal(result.rechnungsnummer, 'RE-2026-00123');
  assert.equal(result.betrag, '1.234,56');
  assert.equal(result.konfidenz, 100);
});

test('fehlende USt-Zeile: bleibt leer, kein Crash', () => {
  const textOhneUst = [
    'Musterfirma GmbH',
    'Rechnungsnummer: RE-2026-00124',
    'Rechnungsdatum: 02.03.2026',
    'Gesamtbetrag: 500,00 EUR',
    'IBAN: DE89370400440532013000',
  ].join('\n');
  const result = extractRechnungsdaten({ text: textOhneUst });
  assert.equal(result.ust, '');
  assert.equal(result.rechnungsnummer, 'RE-2026-00124');
  assert.equal(result.betrag, '500,00');
});

test('deutsches Zahlenformat (1.234,56): wird vollstaendig erfasst, nicht abgeschnitten', () => {
  const result = extractRechnungsdaten({ text: 'Gesamtbetrag: 1.234,56 EUR' });
  assert.equal(result.betrag, '1.234,56');
  assert.notEqual(result.betrag, '1.23');
});

test('IBAN mit Leerzeichen (Standard-4er-Gruppierung)', () => {
  const result = extractRechnungsdaten({ text: 'IBAN: DE89 3704 0044 0532 0130 00' });
  assert.equal(result.iban.replace(/\s+/g, ''), 'DE89370400440532013000');
});

test('IBAN ohne Leerzeichen', () => {
  const result = extractRechnungsdaten({ text: 'IBAN: DE89370400440532013000' });
  assert.equal(result.iban.replace(/\s+/g, ''), 'DE89370400440532013000');
});

test('leere Eingabe: scheitert sauber, kein Crash', () => {
  const result = extractRechnungsdaten({ text: '' });
  assert.equal(result.rechnungsnummer, '');
  assert.equal(result.betrag, '');
  assert.equal(result.konfidenz, 0);
});

test('unlesbare Eingabe (null/undefined/Zahl statt Text): scheitert sauber, kein Crash', () => {
  assert.doesNotThrow(() => extractRechnungsdaten({}));
  assert.doesNotThrow(() => extractRechnungsdaten({ text: null }));
  assert.doesNotThrow(() => extractRechnungsdaten(null));
  assert.doesNotThrow(() => extractRechnungsdaten(undefined));
  assert.doesNotThrow(() => extractRechnungsdaten(12345));
  const result = extractRechnungsdaten(null);
  assert.equal(result.konfidenz, 0);
});
