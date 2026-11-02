<?php
// Pagina della rassegna: legge articles.json (già selezionato da curate.py).
// Va caricata nella stessa cartella di articles.json; se esiste, usa anche cache/articles.json.
date_default_timezone_set('Europe/Rome');

$f = is_file(__DIR__ . '/articles.json') ? __DIR__ . '/articles.json' : __DIR__ . '/cache/articles.json';
$d = is_file($f) ? json_decode(file_get_contents($f), true) : null;
if ($d && !isset($d['items'], $d['generated_at'])) { $d = null; } // file nel vecchio formato
$items = $d['items'] ?? [];

function h($s) { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }

// Toglie la coda "L'articolo ... proviene da ..." che alcuni feed aggiungono e accorcia il testo.
function riassunto($s, $max = 260) {
    $s = trim(preg_replace('/\s*L\'articolo .*? proviene da .*$/us', '', (string)$s));
    $s = preg_replace('/\s+/u', ' ', $s);
    if (mb_strlen($s) > $max) {
        $s = mb_substr($s, 0, $max);
        $s = preg_replace('/\s+\S*$/u', '', $s) . '…';
    }
    return $s;
}

// "2 ore fa", "ieri", ecc.
function quando($ts) {
    $m = max(0, (time() - (int)$ts) / 60);
    if ($m < 60)   return 'meno di un\'ora fa';
    if ($m < 1440) { $o = (int)round($m / 60); return $o . ($o == 1 ? ' ora fa' : ' ore fa'); }
    $g = (int)round($m / 1440);
    return $g == 1 ? 'ieri' : $g . ' giorni fa';
}

$giorni = ['domenica','lunedì','martedì','mercoledì','giovedì','venerdì','sabato'];
$mesi   = ['','gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre'];
$ts_ref = $d ? (int)$d['generated_at'] : time();
$data_it = $giorni[(int)date('w', $ts_ref)] . ' ' . (int)date('j', $ts_ref) . ' ' . $mesi[(int)date('n', $ts_ref)] . ' ' . date('Y', $ts_ref);

$blocchi = [
  'politica' => ['Politica Italia e mondo', 'politica'],
  'tech'     => ['AI e tecnologia',         'tech'],
  'varia'    => ['Attualità varia',         'varia'],
  'cronaca'  => ['Cronaca: grandi eventi',  'cronaca'],
];

function per_categoria($items, $cat) {
    $out = [];
    foreach ($items as $i) { if (($i['category'] ?? '') === $cat) $out[] = $i; }
    return $out;
}

function scheda($i) {
    $etichetta = '';
    if (!empty($i['subtype'])) {
        $etichetta = $i['subtype'] === 'scienza' ? 'Scienza e ambiente' : 'Società e cultura';
    }
    $n = (int)($i['n_sources'] ?? 1);
    $riass = riassunto($i['summary'] ?? '');
    ?>
    <article class="card">
      <div class="meta">
        <?php if ($etichetta): ?><span class="etichetta"><?= h($etichetta) ?></span><?php endif; ?>
        <span class="quando"><?= h(quando($i['pub_ts'] ?? time())) ?></span>
      </div>
      <h3><a href="<?= h($i['link']) ?>"><?= h($i['title']) ?></a></h3>
      <?php if ($riass): ?><p class="riass"><?= h($riass) ?></p><?php endif; ?>
      <div class="fonti">
        <span class="badge <?= $n >= 2 ? 'ok' : 'uno' ?>"><?= $n >= 2 ? 'Confermata da ' . $n . ' fonti' : 'Una sola fonte' ?></span>
        <?php foreach (($i['sources'] ?? []) as $s): ?>
          <a class="pill" href="<?= h($s['link']) ?>"><?= h($s['name']) ?></a>
        <?php endforeach; ?>
      </div>
    </article>
    <?php
}
?><!doctype html>
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
.vuoto{color:#6a7280;font-style:italic}
footer{margin-top:36px;padding-top:14px;border-top:1px solid #dcd8cf;color:#6a7280;font-size:.85rem}
a:focus-visible{outline:3px solid #1f5fb3;outline-offset:2px}
@media (prefers-color-scheme:dark){
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
    <?php if ($d): ?>
      <p class="data"><?= h($data_it) ?> · aggiornata alle <?= h(date('H:i', $ts_ref)) ?></p>
    <?php else: ?>
      <p class="data">Nessuna rassegna disponibile al momento.</p>
    <?php endif; ?>
  </header>

  <?php if ($d): ?>
  <nav class="indice" aria-label="Sezioni">
    <?php foreach ($blocchi as $k => $b): if (!per_categoria($items, $k)) continue; ?>
      <a href="#<?= h($k) ?>"><?= h($b[0]) ?></a>
    <?php endforeach; ?>
  </nav>

  <?php foreach ($blocchi as $k => $b):
    $sel = per_categoria($items, $k);
    if (!$sel) continue; ?>
  <section class="<?= h($b[1]) ?>" id="<?= h($k) ?>">
    <h2><?= h($b[0]) ?></h2>
    <?php if ($k === 'politica'):
      foreach (['italia' => 'Italia', 'mondo' => 'Mondo'] as $ak => $an):
        $gruppo = array_filter($sel, function ($i) use ($ak) { return ($i['area'] ?? 'italia') === $ak; });
        if (!$gruppo) continue; ?>
        <h3 class="sotto"><?= h($an) ?></h3>
        <?php foreach ($gruppo as $i) scheda($i); ?>
      <?php endforeach;
    else:
      foreach ($sel as $i) scheda($i);
    endif; ?>
  </section>
  <?php endforeach; ?>

  <footer>
    <?= count($items) ?> notizie selezionate da fonti italiane. «Confermata» significa che più testate
    hanno riportato lo stesso fatto; le fonti sono sotto ogni notizia.
  </footer>
  <?php endif; ?>
</div>
</body></html>
