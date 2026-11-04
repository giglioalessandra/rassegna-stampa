<!doctype html>
<html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rassegna stampa</title>
<style>
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:#f4f2ee;color:#1f2328;font:18px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
.wrap{max-width:46rem;margin:0 auto;padding:0 16px 48px}
header.testata{padding:28px 0 14px}
.testata h1{margin:0;font:700 2rem/1.15 Georgia,"Times New Roman",serif;letter-spacing:-.01em}
.testata .data{margin:.35rem 0 0;color:#5c6470;font-size:1rem}
nav.indice{position:sticky;top:0;z-index:5;background:#f4f2ee;padding:10px 0;margin:0 -16px;padding-left:16px;padding-right:16px;border-bottom:1px solid #dcd8cf;display:-webkit-flex;display:flex;-webkit-flex-wrap:wrap;flex-wrap:wrap}
nav.indice a{display:inline-block;margin:0 8px 6px 0;padding:6px 14px;border-radius:999px;background:#fff;border:1px solid #d3cfc5;color:#1f2328;text-decoration:none;font-size:.9rem;font-weight:600}
nav.indice a:active,nav.indice a:hover{background:#e8e4da}
section{padding-top:8px}
section h2{margin:30px 0 4px;font:700 1.35rem/1.25 Georgia,"Times New Roman",serif;padding-left:12px;border-left:6px solid var(--c,#555)}
section.politica{--c:#b3402a}
section.tech{--c:#1f5fb3}
section.varia{--c:#2b7a4b}
section.cronaca{--c:#6b4aa0}
h3.sotto{margin:22px 0 2px;font-size:.8rem;letter-spacing:.09em;text-transform:uppercase;color:#5c6470}
.card{background:#fff;border:1px solid #e3dfd5;border-radius:12px;padding:16px 18px;margin:12px 0}
.meta{font-size:.8rem;color:#6a7280;margin-bottom:4px}
.etichetta{font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--c,#555);margin-right:10px}
.card h3{margin:0 0 6px;font:700 1.18rem/1.35 Georgia,"Times New Roman",serif}
.card h3 a{color:inherit;text-decoration:none}
.card h3 a:hover,.card h3 a:focus{text-decoration:underline}
.riass{margin:0 0 10px;color:#3d444d;font-size:1rem;line-height:1.55}
.fonti{display:-webkit-flex;display:flex;-webkit-flex-wrap:wrap;flex-wrap:wrap;-webkit-align-items:center;align-items:center}
.badge{font-size:.78rem;font-weight:700;padding:3px 10px;border-radius:6px;margin:0 8px 6px 0}
.badge.ok{background:#dff1e6;color:#17613a}
.badge.uno{background:#f7ecd3;color:#7a5200}
.pill{font-size:.85rem;margin:0 8px 6px 0;padding:3px 10px;border-radius:999px;border:1px solid #c9d6ee;color:#1f5fb3;text-decoration:none;background:#f3f7fd}
.pill:hover{background:#e3ecfa}
.avviso{background:#fff;border:1px solid #e3dfd5;border-left:5px solid #b3402a;border-radius:10px;padding:14px 16px;margin:16px 0;font-size:.95rem}
.ricarica{margin-top:10px;padding:10px 18px;background:#1f5fb3;color:#fff;border:0;border-radius:10px;font-size:.95rem;font-weight:700;cursor:pointer}
.stato{color:#6a7280;text-align:center;padding:36px 12px}
.vuoto{color:#6a7280;font-style:italic}
footer{margin-top:36px;padding-top:14px;border-top:1px solid #dcd8cf;color:#6a7280;font-size:.85rem}
a:focus-visible{outline:3px solid #1f5fb3;outline-offset:2px}
@media (prefers-color-scheme:dark){
  .avviso{background:#1d2024;border-color:#2d3138;border-left-color:#ef8a74}
  .stato{color:#9aa3b0}
  body{background:#15171a;color:#e8e6e1}
  nav.indice{background:#15171a;border-bottom-color:#2d3138}
  nav.indice a{background:#1f2328;border-color:#343a42;color:#e8e6e1}
  .testata .data,.meta,h3.sotto,.vuoto,footer{color:#9aa3b0}
  .card{background:#1d2024;border-color:#2d3138}
  .riass{color:#c4c9d0}
  .badge.ok{background:#173323;color:#7ed4a1}
  .badge.uno{background:#35290f;color:#f0c46a}
  .pill{background:#1c2432;border-color:#2c3c58;color:#8db4ff}
  section.politica{--c:#ef8a74} section.tech{--c:#7eb0ff} section.varia{--c:#6fcf97} section.cronaca{--c:#b79cf0}
}
@media (min-width:700px){body{font-size:19px}.testata h1{font-size:2.4rem}}
</style></head><body>
<div class="wrap">
  <header class="testata">
    <h1>Rassegna stampa</h1>
    <p class="data" id="data">caricamento…</p>
  </header>
  <nav class="indice" id="indice" aria-label="Sezioni" style="display:none"></nav>
  <main id="contenuto"><p class="stato">Scarico le notizie…</p></main>
</div>
<script>
/* ===================================================================
   Le notizie stanno su GitHub e le scarica il browser: il server
   Altervista non può collegarsi all'esterno. Se GitHub non risponde,
   si usa l'ultima copia salvata sul dispositivo.
   =================================================================== */
var GITHUB_UTENTE = 'giglioalessandra';
var GITHUB_REPO   = 'rassegna-stampa';
var GITHUB_RAMO   = 'main';
var URL_NOTIZIE = 'https://raw.githubusercontent.com/' + GITHUB_UTENTE + '/' +
                  GITHUB_REPO + '/' + GITHUB_RAMO + '/cache/articles.json';

var BLOCCHI = [
  ['politica', 'Politica Italia e mondo'],
  ['tech',     'AI e tecnologia'],
  ['varia',    'Attualità varia'],
  ['cronaca',  'Cronaca: grandi eventi']
];
var GIORNI = ['domenica','lunedì','martedì','mercoledì','giovedì','venerdì','sabato'];
var MESI = ['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre'];

function esc(t) {
  return String(t == null ? '' : t).replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function urlSicuro(u) { return /^https?:\/\//i.test(u || '') ? u : '#'; }
function due(n) { return (n < 10 ? '0' : '') + n; }

function riassunto(s) {
  s = String(s || '').replace(/\s*L'articolo .*? proviene da .*$/i, '').replace(/\s+/g, ' ').trim();
  if (s.length > 260) { s = s.slice(0, 260).replace(/\s+\S*$/, '') + '…'; }
  return s;
}
function quando(ts, adesso) {
  var m = Math.max(0, (adesso - ts) / 60);
  if (m < 60) return "meno di un'ora fa";
  if (m < 1440) { var o = Math.round(m / 60); return o + (o === 1 ? ' ora fa' : ' ore fa'); }
  var g = Math.round(m / 1440);
  return g === 1 ? 'ieri' : g + ' giorni fa';
}

function scheda(i, adesso) {
  var etichetta = i.subtype ? (i.subtype === 'scienza' ? 'Scienza e ambiente' : 'Società e cultura') : '';
  var n = i.n_sources || 1, riass = riassunto(i.summary);
  var h = '<article class="card"><div class="meta">';
  if (etichetta) h += '<span class="etichetta">' + esc(etichetta) + '</span>';
  h += '<span class="quando">' + esc(quando(i.pub_ts, adesso)) + '</span></div>';
  h += '<h3><a href="' + esc(urlSicuro(i.link)) + '" target="_blank" rel="noopener">' + esc(i.title) + '</a></h3>';
  if (riass) h += '<p class="riass">' + esc(riass) + '</p>';
  h += '<div class="fonti"><span class="badge ' + (n >= 2 ? 'ok' : 'uno') + '">' +
       (n >= 2 ? 'Confermata da ' + n + ' fonti' : 'Una sola fonte') + '</span>';
  (i.sources || []).forEach(function (s) {
    h += '<a class="pill" href="' + esc(urlSicuro(s.link)) + '" target="_blank" rel="noopener">' + esc(s.name) + '</a>';
  });
  return h + '</div></article>';
}

function perCategoria(items, cat) {
  return items.filter(function (i) { return i.category === cat; });
}

function disegna(dati, avviso) {
  var items = dati.items || [];
  var adesso = Math.floor(Date.now() / 1000);
  var ref = new Date((dati.generated_at || adesso) * 1000);
  document.getElementById('data').textContent =
    GIORNI[ref.getDay()] + ' ' + ref.getDate() + ' ' + MESI[ref.getMonth()] + ' ' + ref.getFullYear() +
    ' · aggiornata alle ' + due(ref.getHours()) + ':' + due(ref.getMinutes());

  var nav = '', html = avviso ? '<div class="avviso">' + avviso + '</div>' : '';
  BLOCCHI.forEach(function (b) {
    var sel = perCategoria(items, b[0]);
    if (!sel.length) return;
    nav += '<a href="#' + b[0] + '">' + esc(b[1]) + '</a>';
    html += '<section class="' + b[0] + '" id="' + b[0] + '"><h2>' + esc(b[1]) + '</h2>';
    if (b[0] === 'politica') {
      [['italia','Italia'],['mondo','Mondo']].forEach(function (a) {
        var g = sel.filter(function (i) { return (i.area || 'italia') === a[0]; });
        if (!g.length) return;
        html += '<h3 class="sotto">' + a[1] + '</h3>';
        g.forEach(function (i) { html += scheda(i, adesso); });
      });
    } else {
      sel.forEach(function (i) { html += scheda(i, adesso); });
    }
    html += '</section>';
  });
  html += '<footer>' + items.length + ' notizie selezionate da fonti italiane. «Confermata» significa che più ' +
          'testate hanno riportato lo stesso fatto; le fonti sono sotto ogni notizia.</footer>';
  var indice = document.getElementById('indice');
  indice.innerHTML = nav;
  indice.style.display = nav ? '' : 'none';
  document.getElementById('contenuto').innerHTML = html;
}

function erroreSchermo(msg) {
  document.getElementById('data').textContent = 'notizie non disponibili';
  document.getElementById('indice').style.display = 'none';
  document.getElementById('contenuto').innerHTML = '<div class="avviso">' + msg +
    '<br><button class="ricarica" onclick="location.reload()">Riprova</button></div>';
}

function salvaLocale(d) { try { localStorage.setItem('rassegna_dati_v2', JSON.stringify(d)); } catch (e) {} }
function leggiLocale() {
  try { var g = localStorage.getItem('rassegna_dati_v2'); return g ? JSON.parse(g) : null; } catch (e) { return null; }
}

function carica() {
  fetch(URL_NOTIZIE, { cache: 'no-store' })
    .then(function (r) {
      if (!r.ok) throw new Error('GitHub ha risposto ' + r.status);
      return r.json();
    })
    .then(function (dati) {
      if (!dati || !dati.items || !dati.items.length) throw new Error('il file delle notizie è vuoto o in un formato vecchio');
      salvaLocale(dati);
      disegna(dati, null);
    })
    .catch(function (err) {
      var vecchi = leggiLocale();
      if (vecchi && vecchi.items && vecchi.items.length) {
        disegna(vecchi, '<strong>Notizie non aggiornate.</strong> Non sono riuscita a contattare GitHub (' +
          esc(err.message) + '), quindi vedi l\'ultima copia scaricata su questo dispositivo.');
      } else {
        erroreSchermo('<strong>Non riesco a scaricare le notizie.</strong><br>' + esc(err.message) +
          '<br><br>Controlla che il deposito GitHub <em>' + esc(GITHUB_UTENTE + '/' + GITHUB_REPO) +
          '</em> sia <strong>pubblico</strong> e contenga <em>cache/articles.json</em>.');
      }
    });
}
carica();
</script>
</body></html>
