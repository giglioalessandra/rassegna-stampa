<?php
// Pagina della rassegna: legge articles.json (già selezionato da curate.py).
// Va caricata nella stessa cartella di articles.json; se esiste, usa anche cache/articles.json.
$f = is_file(__DIR__ . '/articles.json') ? __DIR__ . '/articles.json' : __DIR__ . '/cache/articles.json';
$d = is_file($f) ? json_decode(file_get_contents($f), true) : null;
if ($d && !isset($d['items'], $d['generated_at'])) { $d = null; } // file nel vecchio formato
$items = $d['items'] ?? [];
$blocchi = [
  'politica' => 'Politica Italia e mondo',
  'tech'     => 'AI e tecnologia',
  'varia'    => 'Attualità varia',
  'cronaca'  => 'Cronaca: grandi eventi',
];
function h($s) { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }
?><!doctype html>
<html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rassegna stampa</title>
<style>
body{font:17px/1.5 system-ui,sans-serif;max-width:760px;margin:0 auto;padding:16px;background:#fafafa;color:#222}
h1{font-size:1.5rem}h2{margin-top:2rem;border-bottom:2px solid #ccc;padding-bottom:.2rem}
article{background:#fff;border-radius:10px;padding:12px 14px;margin:12px 0;box-shadow:0 1px 3px #0002}
article h3{margin:0 0 .3rem;font-size:1.05rem}article a{color:inherit}
.s{font-size:.9rem;color:#555}.s a{color:#06c;margin-right:.6rem}.tag{font-size:.75rem;color:#777}
@media(prefers-color-scheme:dark){body{background:#151515;color:#eee}article{background:#222}.s{color:#aaa}.s a{color:#7ab8ff}}
</style></head><body>
<h1>Rassegna stampa</h1>
<?php if ($d): ?><p class="tag">Aggiornata il <?= h(date('d/m/Y H:i', $d['generated_at'])) ?></p><?php else: ?><p>Nessuna rassegna disponibile.</p><?php endif; ?>
<?php foreach ($blocchi as $k => $titolo):
  $sel = array_filter($items, fn($i) => $i['category'] === $k);
  if (!$sel) continue; ?>
<h2><?= h($titolo) ?></h2>
<?php foreach ($sel as $i): ?>
<article>
  <h3><a href="<?= h($i['link']) ?>"><?= h($i['title']) ?></a></h3>
  <?php if (!empty($i['summary'])): ?><div><?= h($i['summary']) ?></div><?php endif; ?>
  <div class="s">Fonti (<?= (int)$i['n_sources'] ?>):
    <?php foreach ($i['sources'] as $s): ?><a href="<?= h($s['link']) ?>"><?= h($s['name']) ?></a><?php endforeach; ?>
  </div>
</article>
<?php endforeach; endforeach; ?>
</body></html>
