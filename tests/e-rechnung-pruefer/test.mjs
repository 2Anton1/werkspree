import fs from 'node:fs';
import path from 'node:path';
import { JSDOM, VirtualConsole } from 'jsdom';

const PAGE = new URL('../../e-rechnung-pruefen/index.html', import.meta.url).pathname;
const html = fs.readFileSync(PAGE, 'utf8');

function makeDom() {
  const vc = new VirtualConsole();
  vc.on('jsdomError', () => {});
  const dom = new JSDOM(html, {
    runScripts: 'dangerously',
    url: 'https://werkspree.bki-de.de/e-rechnung-pruefen/',
    virtualConsole: vc,
    pretendToBeVisual: true,
  });
  dom.window.HTMLElement.prototype.scrollIntoView = () => {};
  return dom;
}

async function run(file) {
  const dom = makeDom();
  const { window } = dom;
  const doc = window.document;
  const input = doc.getElementById('file');
  const bytes = fs.readFileSync(file);
  const f = new window.File([bytes], path.basename(file), { type: 'application/xml' });
  Object.defineProperty(input, 'files', { value: [f], configurable: true });
  input.dispatchEvent(new window.Event('change'));
  await new Promise(r => setTimeout(r, 400));
  const out = {
    verdictClass: doc.getElementById('verdict').className,
    title: doc.getElementById('verdict-title').textContent,
    checks: [...doc.querySelectorAll('#checks li')].map(li => ({
      state: li.querySelector('.mark')?.className.replace('mark ', ''),
      label: li.querySelector('strong')?.textContent,
    })),
    fields: (() => {
      const dl = doc.getElementById('fields');
      const o = {}; const kids = [...dl.children];
      for (let i = 0; i < kids.length; i += 2) o[kids[i].textContent] = kids[i + 1].textContent;
      return o;
    })(),
    hidden: doc.getElementById('result').classList.contains('hidden'),
  };
  dom.window.close();
  return out;
}

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log('  OK  ' + name);
  else { failures++; console.log('  XX  ' + name + (detail ? '  -> ' + detail : '')); }
}
const S = new URL('./samples/', import.meta.url).pathname;

console.log('\n== XRechnung (UBL), vollstaendig ==');
let r = await run(S + 'xrechnung.xml');
console.log('  Urteil:', r.title);
check('nicht versteckt', !r.hidden);
check('als gueltig bewertet', r.verdictClass.includes('ok'), r.verdictClass + ' | ' + r.title);
check('Rechnungsnummer', r.fields['Rechnungsnummer'] === 'RE-2026-0815', r.fields['Rechnungsnummer']);
check('Datum', r.fields['Rechnungsdatum'] === '2026-07-31', r.fields['Rechnungsdatum']);
check('Verkaeufer', r.fields['Verkäufer'] === 'Elektro Griesbach GmbH', r.fields['Verkäufer']);
check('Anschrift', r.fields['Anschrift'] === 'Musterweg 5, 10115 Berlin, DE', r.fields['Anschrift']);
check('USt-IdNr', r.fields['USt-IdNr. / Steuernr.'] === 'DE123456789', r.fields['USt-IdNr. / Steuernr.']);
check('Kaeufer', r.fields['Käufer'] === 'Dachdecker Sommer e.K.', r.fields['Käufer']);
check('Brutto', r.fields['Bruttobetrag'] === '1.190,00 EUR', r.fields['Bruttobetrag']);
check('IBAN', r.fields['IBAN'] === 'DE02120300000000202051', r.fields['IBAN']);
check('2 Positionen', r.fields['Positionen'] === '2', r.fields['Positionen']);
check('Profil XRechnung', r.checks[0] && r.checks[0].label.includes('XRechnung'), r.checks[0] && r.checks[0].label);
check('keine Fehler', r.checks.every(c => c.state !== 'bad'), JSON.stringify(r.checks.filter(c => c.state === 'bad')));

console.log('\n== ZUGFeRD (CII), Profil EN 16931 ==');
r = await run(S + 'zugferd.xml');
console.log('  Urteil:', r.title);
check('als gueltig bewertet', r.verdictClass.includes('ok'), r.verdictClass + ' | ' + r.title);
check('Rechnungsnummer', r.fields['Rechnungsnummer'] === '2026-4711', r.fields['Rechnungsnummer']);
check('CII-Datum umgewandelt', r.fields['Rechnungsdatum'] === '15.07.2026', r.fields['Rechnungsdatum']);
check('Verkaeufer', r.fields['Verkäufer'] === 'Bau & Technik Havel GmbH', r.fields['Verkäufer']);
check('Anschrift', r.fields['Anschrift'] === 'Werftstr. 12, 14467 Potsdam, DE', r.fields['Anschrift']);
check('USt-IdNr', r.fields['USt-IdNr. / Steuernr.'] === 'DE987654321', r.fields['USt-IdNr. / Steuernr.']);
check('Kaeufer', r.fields['Käufer'] === 'Tischlerei Nord OHG', r.fields['Käufer']);
check('Brutto', r.fields['Bruttobetrag'] === '2.975,00 EUR', r.fields['Bruttobetrag']);
check('IBAN', r.fields['IBAN'] === 'DE44500105175407324931', r.fields['IBAN']);
check('Profil EN 16931', r.checks[0] && r.checks[0].label.includes('EN 16931'), r.checks[0] && r.checks[0].label);

console.log('\n== ZUGFeRD MINIMUM, Kaeufer fehlt, Betraege falsch ==');
r = await run(S + 'zugferd_minimum_kaputt.xml');
console.log('  Urteil:', r.title);
check('als fehlerhaft bewertet', r.verdictClass.includes('bad'), r.verdictClass);
check('MINIMUM unzureichend', r.checks[0] && r.checks[0].state === 'bad' && r.checks[0].label.includes('MINIMUM'), JSON.stringify(r.checks[0]));
check('fehlender Kaeufer erkannt', r.checks.some(c => c.state === 'bad' && c.label.includes('Käufer')), JSON.stringify(r.checks.map(c => c.label)));
check('Rechenfehler erkannt', r.checks.some(c => c.state === 'bad' && c.label.includes('passen nicht zusammen')), JSON.stringify(r.checks.filter(c => c.state === 'bad').map(c => c.label)));

console.log('\n== Unbekanntes XML ==');
fs.writeFileSync(S + 'fremd.xml', '<?xml version="1.0"?><Bestellung><Nr>1</Nr></Bestellung>');
r = await run(S + 'fremd.xml');
check('unbekanntes Format erkannt', r.title.includes('Kein bekanntes E-Rechnungsformat'), r.title);

console.log('\n== Kaputtes XML ==');
fs.writeFileSync(S + 'kaputt.xml', '<Invoice><nicht geschlossen');
r = await run(S + 'kaputt.xml');
check('Parserfehler abgefangen', r.title.includes('lässt sich nicht lesen'), r.title);

console.log('\n' + (failures ? failures + ' FEHLGESCHLAGEN' : 'Alle Pruefungen bestanden'));
process.exit(failures ? 1 : 0);
