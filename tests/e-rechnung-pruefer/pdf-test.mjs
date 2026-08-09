import fs from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const pdfjsLib = require('pdfjs-dist/legacy/build/pdf.js');
pdfjsLib.GlobalWorkerOptions.workerSrc = require.resolve('pdfjs-dist/legacy/build/pdf.worker.js');

// exakt dieselbe Auswahl-Logik wie auf der Seite
function pickXml(att) {
  const keys = att ? Object.keys(att) : [];
  for (const k of keys) {
    if (/\.xml$/i.test(k) || /\.xml$/i.test(att[k].filename || '')) return k;
  }
  return null;
}

let fails = 0;
const ok = (n, c, d) => { console.log((c ? '  OK  ' : '  XX  ') + n + (c ? '' : '  -> ' + d)); if (!c) fails++; };

async function attOf(file) {
  const data = new Uint8Array(fs.readFileSync(file));
  const pdf = await pdfjsLib.getDocument({ data }).promise;
  return pdf.getAttachments();
}

console.log('\n== ZUGFeRD-PDF mit eingebetteter factur-x.xml ==');
let att = await attOf(new URL('./samples/zugferd.pdf', import.meta.url).pathname);
const key = pickXml(att);
ok('XML-Anhang gefunden', !!key, JSON.stringify(Object.keys(att || {})));
if (key) {
  const text = new TextDecoder('utf-8').decode(att[key].content);
  ok('Anhang ist CrossIndustryInvoice', text.includes('CrossIndustryInvoice'), text.slice(0, 80));
  ok('Rechnungsnummer im Anhang', text.includes('2026-4711'));
}

console.log('\n== Einfache PDF ohne strukturierte Daten ==');
att = await attOf(new URL('./samples/nur_pdf.pdf', import.meta.url).pathname);
ok('kein XML-Anhang -> als "keine E-Rechnung" behandelt', pickXml(att) === null, JSON.stringify(Object.keys(att || {})));

console.log('\n' + (fails ? fails + ' FEHLGESCHLAGEN' : 'PDF-Pfad bestanden'));
process.exit(fails ? 1 : 0);
