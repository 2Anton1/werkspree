// Rechnungsdaten aus dem Request extrahieren
// Extrahiert aus dem n8n Code-Node "Rechnungsdaten extrahieren", damit die
// Logik ohne n8n lokal getestet werden kann. Muss 1:1 als jsCode zurück in
// den n8n-Workflow gespiegelt werden (siehe rechnungs-ocr-demo.json).

// Der n8n-Webhook-Node packt Header/Query/Body in ein Huellobjekt; der
// eigentliche POST-Body liegt verschachtelt unter .body (als Objekt, oder als
// String, wenn der Aufrufer keinen JSON-Content-Type gesetzt hat). Diese
// Funktion liefert das Objekt zurueck, auf dem die eigentlichen Felder
// (text/data/content) gesucht werden sollen.
function unwrapWebhookBody(payload) {
  if (payload && typeof payload === 'object' && 'body' in payload) {
    let body = payload.body;
    if (typeof body === 'string') {
      try {
        body = JSON.parse(body);
      } catch (e) {
        return { text: body };
      }
    }
    if (body && typeof body === 'object') {
      return body;
    }
  }
  return payload;
}

// Bringt beliebigen Input auf einen lesbaren Text-String. Deckt die Faelle ab,
// die im n8n-Webhook real vorkommen:
//   1. input ist der rohe Webhook-Wrapper: { headers, body: { text: "..." }, ... }
//   2. input ist bereits das entpackte Objekt: { text | data | content: "..." }
//   3. input ist selbst ein JSON-String (z.B. weil der Aufrufer den Body
//      doppelt kodiert hat) -> muss erst geparst werden.
//   4. das Text-Feld selbst ist nochmal ein JSON-String (verschachtelte
//      Doppel-Kodierung) -> muss ebenfalls geparst werden.
// Liefert immer einen String zurueck, nie null/undefined, damit die
// aufrufende Funktion nie auf einer nicht existierenden Eigenschaft crasht.
function extractRawText(input) {
  let payload = input;

  if (typeof payload === 'string') {
    try {
      payload = JSON.parse(payload);
    } catch (e) {
      // war kein JSON, sondern einfach der Rechnungstext selbst
      return payload;
    }
  }

  if (payload === null || payload === undefined || typeof payload !== 'object') {
    return '';
  }

  const source = unwrapWebhookBody(payload);
  if (source === null || typeof source !== 'object') {
    return '';
  }

  let text = source.text ?? source.data ?? source.content ?? '';

  if (typeof text !== 'string') {
    return '';
  }

  const trimmed = text.trim();
  if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
    try {
      const inner = JSON.parse(trimmed);
      if (inner && typeof inner === 'object') {
        text = inner.text ?? inner.data ?? inner.content ?? inner.body ?? text;
      }
    } catch (e) {
      // sah aus wie JSON, war aber keins -> Originaltext behalten
    }
  }

  return typeof text === 'string' ? text : '';
}

// Wandelt einen im Text gefundenen Betrag (z.B. "1.234,56" oder "1234.56")
// in eine normalisierte Zahl um. Deutsches Format (Punkt=Tausender,
// Komma=Dezimal) und englisches Format werden beide erkannt, je nachdem
// welches Trennzeichen zuletzt im String steht.
function parseGermanAmount(raw) {
  if (!raw) return null;
  const hasComma = raw.includes(',');
  const hasDot = raw.includes('.');
  let normalized = raw;

  if (hasComma && hasDot) {
    normalized = raw.lastIndexOf(',') > raw.lastIndexOf('.')
      ? raw.replace(/\./g, '').replace(',', '.')
      : raw.replace(/,/g, '');
  } else if (hasComma) {
    normalized = raw.replace(',', '.');
  }

  const num = parseFloat(normalized);
  return Number.isNaN(num) ? null : num;
}

function extractRechnungsdaten(input) {
  const text = extractRawText(input);

  // Wenn Base64-Binary, dekodieren
  let decodedText = text;
  try {
    if (text.length > 100 && text.match(/^[A-Za-z0-9+/=]+$/)) {
      decodedText = Buffer.from(text, 'base64').toString('utf-8');
    }
  } catch (e) {}

  // Escaped Newlines normalisieren (falls Text doppelt JSON-kodiert ankam)
  decodedText = decodedText.replace(/\\n/g, '\n');

  // RegEx-Muster fuer Rechnungsdaten
  const patterns = {
    rechnungsnummer: /Rechnungs?\s*(?:Nr\.?|nummer|number)[:\s]*([A-Z0-9\-/]+)/i,
    datum: /(?:Rechnungs?\s*datum|Datum)[:\s]*(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})/i,
    faelligkeit: /(?:Zahlungsziel|Faellig|Fällig|Due)[:\s]*(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})/i,
    // Erfasst den vollen Betrag inkl. Tausendertrennzeichen (z.B. "1.234,56"),
    // statt nach dem ersten Trennzeichen abzuschneiden.
    betrag: /(?:Gesamtbetrag|Total|Summe|Amount)[:\s]*(\d+(?:[.,]\d+)*)\s*(?:EUR|€|\$)?/i,
    ust: /(?:USt|MwSt|VAT)[:\s]*(\d+[.,]\d{1,2})\s*%/i,
    // Erlaubt optionale Leerzeichen nach jeder 4er-Gruppe (Standard-IBAN-Anzeige),
    // nicht nur nach der Laenderkennung.
    iban: /(DE\d{2}(?:\s?\d{4}){4}\s?\d{2})/i,
    bic: /BIC[:\s]*([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)/i,
  };

  const extracted = {};
  for (const [key, pattern] of Object.entries(patterns)) {
    const match = decodedText.match(pattern);
    extracted[key] = match ? match[1].trim() : '';
  }

  extracted.betrag_normalisiert = parseGermanAmount(extracted.betrag);

  // Absender extrahieren
  const lines = decodedText.split('\n').filter((l) => l.trim().length > 3);
  extracted.absender = lines[0] ? lines[0].trim() : '';
  extracted.volltext = decodedText.substring(0, 3000);
  extracted.verarbeitet_am = new Date().toISOString();

  // Konfidenz-Score: nur die sieben inhaltlichen Felder zaehlen, nicht die
  // immer gefuellten Meta-Felder (volltext, verarbeitet_am, konfidenz selbst).
  const contentFields = ['rechnungsnummer', 'datum', 'faelligkeit', 'betrag', 'ust', 'iban', 'bic'];
  const found = contentFields.filter((k) => extracted[k] && extracted[k].length > 0).length;
  extracted.konfidenz = Math.round((found / contentFields.length) * 100);

  return extracted;
}

module.exports = { extractRechnungsdaten };
