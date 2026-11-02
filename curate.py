#!/usr/bin/env python3
"""
Rassegna Stampa — selezione dei contenuti.

Legge cache/raw.json e produce cache/articles.json (la rassegna selezionata) con:
  - 10 notizie di politica Italia/mondo
  - 4 su AI e tecnologia
  - 5 di attualità varia (società/costume/cultura + scienza/tecnologia/ambiente)
  - cronaca solo se è un grande evento
Ogni voce raggruppa le notizie sullo stesso fatto (niente ripetizioni) e riporta
tutte le fonti che lo documentano: più fonti indipendenti = notizia più solida.

Solo libreria standard.   Uso: python3 curate.py [cartella_cache]
"""
import json, os, re, sys, unicodedata
from datetime import datetime, timezone

QUOTE = {'politica': 10, 'tech': 4, 'varia': 5}
MIN_POLITICA_PER_AREA = 4          # almeno 4 Italia e 4 mondo (sui 10)
FINESTRA_ORE = 36                  # notizie più vecchie non entrano
SOGLIA_SIMILARITA = 0.34

STOP = set("""il lo la i gli le un uno una di a da in con su per tra fra e ed o ma che chi cui non
del dello della dei degli delle al allo alla ai agli alle dal dallo dalla dai dagli dalle nel nello nella
nei negli nelle sul sullo sulla sui sugli sulle sono è era sarà ha hanno essere dopo prima anche più come
the a an of to in on for and or with by from at is are was be as it its that this after over new says
say will has have not but his her their into about up out more than who what how why""".split())

# Sezioni in cui finiscono i feed (feeds.json)
POLITICA = {'italia', 'mondo'}

# Parole che indicano politica / non-politica nelle sezioni generaliste
RE_POLITICA = re.compile(
    r"\b(govern|meloni|schlein|salvini|tajani|mattarella|parlament|camera|senato|ministr|premier|"
    r"legge|manovra|elezion|voto|partit|coalizion|opposizion|referendum|commission|ue\b|unione europea|"
    r"nato|onu|trump|putin|zelensk|ucraina|russia|gaza|israel|hamas|iran|cina|xi jinping|usa|casa bianca|"
    r"congresso|presiden|vertice|sanzion|dazi|guerra|cessate|negoziat|diplomat|tregua|parliament|"
    r"election|minister|white house|sanction|tariff|ceasefire|war|summit|treaty|government|senate)", re.I)
RE_ITALIA_POL = re.compile(
    r"\b(meloni|schlein|salvini|tajani|mattarella|conte|renzi|calenda|crosetto|giorgetti|nordio|piantedosi|"
    r"govern\w*|manovra|quirinale|palazzo chigi|montecitorio|csm|magistrat\w*|regional\w*|comunal\w*|"
    r"lega|fratelli d'italia|pd|m5s|forza italia|legge di bilancio|ddl|decreto)\b", re.I)
RE_SPORT_GOSSIP = re.compile(
    r"(\d\s?€|€\s?\d|\bofferta\b|\boffert[ae]\b|\bsconto\b|\bscont[io]\b|\bcoupon\b|\bsu amazon\b|\bprezzo minimo\b)|\b(formula|f1|antonelli|kimi|ferrari|verstappen|pilota|campione del mondo|titolo mondiale|zanicchi|mediaset|vaffa|reality|tronista|influencer|vip|talk show|televisione|tv show|comics|parata|star wars|cosplay|wnba|basket|volley|scudetto|olimpiad\w*|gol|mondiali di|coppa|campionato|concert\w*|ricoverat\w*|serie a|champions|calcio|juventus|inter\b|milan\b|napoli|roma\b|lazio|gp\b|formula 1|motogp|"
    r"tennis|nba|oroscopo|gossip|grande fratello|sanremo|isola dei famosi|football|premier league)\b", re.I)
RE_AI = re.compile(
    r"\bai\b|\bia\b|intelligenza artificiale|artificial intelligence|openai|anthropic|claude|chatgpt|gemini|"
    r"llm|chatbot|machine learning|deepfake|nvidia|semiconduttor|chip|robot|algoritm|cyber|ciber|"
    r"big tech|google|microsoft|apple|meta\b|amazon|tesla|spacex|quantum|quantistic|software|app\b", re.I)
RE_SCIENZA = re.compile(
    r"scienz|scoperta|studio|ricerc|clima|ambient|ecolog|emission|riscaldamento|ghiacci|biodivers|"
    r"medic|vaccin|cancro|tumor|farmac|salute|spazio|nasa|esa\b|astronom|pianeta|fossil|archeolog|"
    r"energia|rinnovabil|climate|environment|species|researchers|scientists|study|health|space|cop3\d", re.I)
RE_CULTURA = re.compile(
    r"cultur|libr|romanzo|scrittor|film|cinema|regist|festival|mostra|museo|arte\b|artist|teatro|serie tv|"
    r"musica|concerto|album|premio|nobel|strega|oscar|societ|costume|moda|tradizion|giovani|famigli|"
    r"scuola|università|diritti|migranti|book|novel|exhibition|theatre|culture|society|prize", re.I)
RE_CRIMINE = re.compile(
    r"\b(arrestat\w*|polizia|carabinieri|omicid\w*|indagat\w*|rapin\w*|furto|spaccio|truffa|fermato|criminalit\w*|"
    r"police|arrested|murder|robbery)\b", re.I)
RE_INCIDENTE = re.compile(
    r"\b(crash\w*|died|dead|killed|incidente|ferroviario|train|schianto|vittime|morti|deragli\w*)\b", re.I)
RE_GRANDE_EVENTO = re.compile(
    r"strage|terremoto|alluvione|attentato|attacco terroristico|esplosione|crollo|naufragio|"
    r"incendio devastante|disastro|vittime|morti|sequestro|omicidio plurimo|maxi[- ]?operazione|"
    r"earthquake|flood|attack|explosion|collapse|shooting|massacre|death toll|killed", re.I)


def norm(s):
    s = unicodedata.normalize('NFKD', s.lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def token(a):
    t = norm(a['title'] + ' ' + a['title'] + ' ' + a.get('description', '')[:160])
    parole = re.findall(r"[a-z0-9]{4,}", t)
    return {p for p in parole if p not in STOP}


def tok_titolo(a):
    return {p for p in re.findall(r"[a-z0-9]{4,}", norm(a['title'])) if p not in STOP}


def simile(a, b):
    ta, tb = a['_tt'], b['_tt']
    if not ta or not tb:
        return 0
    inter = len(ta & tb)
    base = inter / min(len(ta), len(tb))
    full = len(a['_t'] & b['_t']) / max(1, len(a['_t'] | b['_t']))
    return max(base * 0.8, full * 1.6) if inter >= 2 else 0


def clusterizza(articoli):
    """Raggruppa gli articoli che parlano dello stesso fatto."""
    gruppi = []
    for a in articoli:
        a['_t'], a['_tt'] = token(a), tok_titolo(a)
        for g in gruppi:
            if any(simile(a, b) >= SOGLIA_SIMILARITA for b in g[:6]):
                g.append(a)
                break
        else:
            gruppi.append([a])
    return gruppi


def punteggio(g, adesso):
    fonti = {a['source'] for a in g}
    migliore_prio = min(a['source_priority'] for a in g)
    recenza = max(a['pub_ts'] for a in g)
    ore = (adesso - recenza) / 3600
    return len(fonti) * 10 + (4 - migliore_prio) * 2 - ore * 0.15


def categoria(g):
    """Decide a quale blocco appartiene il gruppo, o None se scartarlo."""
    sezioni = {a['section'] for a in g}
    testo = ' '.join(a['title'] for a in g)
    fonti = {a['source'] for a in g}
    cronaca = any(a['source'] == 'ANSA Cronaca' for a in g) and not (sezioni & {'tech', 'varia_scienza', 'varia_cultura'})
    if RE_SPORT_GOSSIP.search(testo):
        return None
    # AI/tech: il titolo deve parlare davvero di AI o tecnologia
    if sezioni & {'tech'}:
        return 'tech' if RE_AI.search(testo) else None
    # Varia: niente incidenti o grandi eventi (vanno in cronaca o restano fuori)
    if sezioni & {'varia_scienza', 'varia_cultura'}:
        if RE_INCIDENTE.search(testo) or RE_GRANDE_EVENTO.search(testo):
            return None
        return 'varia'
    # Grandi eventi di cronaca (anche se arrivano dalle sezioni politiche)
    if RE_GRANDE_EVENTO.search(testo) and len(fonti) >= 3 and (cronaca or RE_INCIDENTE.search(testo)):
        return 'cronaca'
    # Politica: serve un riferimento politico nel titolo; la cronaca nera non vale
    if RE_POLITICA.search(testo) and sezioni & POLITICA:
        if RE_CRIMINE.search(testo) and not RE_ITALIA_POL.search(testo):
            return None
        return 'politica'
    return None


def area(g):
    testo = ' '.join(a['title'] for a in g)
    if RE_ITALIA_POL.search(testo):
        return 'italia'
    if any(a['section'] == 'mondo' for a in g) or any(a['source'].startswith('ANSA') and a['section'] == 'italia' for a in g):
        return 'mondo'
    return 'italia'


def voce(g, cat):
    g = sorted(g, key=lambda a: (a['source_priority'], -a['pub_ts']))
    principale = g[0]
    fonti, viste = [], set()
    for a in g:
        if a['source'] not in viste:
            viste.add(a['source'])
            fonti.append({'name': a['source'], 'link': a['link'], 'title': a['title']})
    return {
        'category': cat,
        'area': area(g) if cat == 'politica' else None,
        'title': principale['title'],
        'summary': principale.get('description', ''),
        'link': principale['link'],
        'pub_ts': max(a['pub_ts'] for a in g),
        'n_sources': len(fonti),
        'documented': len(fonti) >= 2,
        'sources': fonti,
    }


def sottotipo_varia(g):
    return 'scienza' if any(a['section'] == 'varia_scienza' for a in g) else 'cultura'


def main():
    cartella = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
    dati = json.load(open(os.path.join(cartella, 'raw.json'), encoding='utf-8'))
    adesso = int(datetime.now(timezone.utc).timestamp())
    arts = [a for a in dati['articles'] if a['pub_ts'] >= adesso - FINESTRA_ORE * 3600]

    gruppi = clusterizza(arts)
    per_cat = {'politica': [], 'tech': [], 'varia': [], 'cronaca': []}
    for g in gruppi:
        c = categoria(g)
        if c:
            per_cat[c].append((punteggio(g, adesso), g))
    for v in per_cat.values():
        v.sort(key=lambda x: -x[0])

    # Politica: 10, con almeno 4 Italia e 4 mondo; preferisce fatti confermati da più fonti
    pol = per_cat['politica']
    scelte, usati = [], set()
    for ar in ('italia', 'mondo'):
        for s, g in [x for x in pol if area(x[1]) == ar][:MIN_POLITICA_PER_AREA]:
            scelte.append((s, g)); usati.add(id(g))
    for s, g in pol:
        if len(scelte) >= QUOTE['politica']:
            break
        if id(g) not in usati:
            scelte.append((s, g)); usati.add(id(g))
    scelte.sort(key=lambda x: -x[0])
    out = [voce(g, 'politica') for _, g in scelte[:QUOTE['politica']]]

    out += [voce(g, 'tech') for _, g in per_cat['tech'][:QUOTE['tech']]]

    # Varia: mix scienza/ambiente e società/cultura (almeno 2 per tipo se disponibili)
    var = per_cat['varia']
    sc = [x for x in var if sottotipo_varia(x[1]) == 'scienza']
    cu = [x for x in var if sottotipo_varia(x[1]) == 'cultura']
    pick = sc[:2] + cu[:2]
    resto = sorted([x for x in var if x not in pick], key=lambda x: -x[0])
    pick += resto[:QUOTE['varia'] - len(pick)]
    pick.sort(key=lambda x: -x[0])
    for s, g in pick[:QUOTE['varia']]:
        v = voce(g, 'varia'); v['subtype'] = sottotipo_varia(g); out.append(v)

    # Cronaca: solo grandi eventi, massimo 2
    for s, g in per_cat['cronaca'][:2]:
        out.append(voce(g, 'cronaca'))

    # 'articles' mantiene il formato del vecchio articles.json, così anche una pagina
    # che non conosce 'items' continua a funzionare.
    vecchio = [{'title': v['title'], 'link': v['link'], 'description': v['summary'],
                'pub_ts': v['pub_ts'], 'source': v['sources'][0]['name'],
                'source_priority': 1, 'section': v['category']} for v in out]
    risultato = {'generated_at': adesso, 'updated_at': adesso, 'quotas': QUOTE,
                 'items': out, 'articles': vecchio}
    with open(os.path.join(cartella, 'articles.json'), 'w', encoding='utf-8') as f:
        json.dump(risultato, f, ensure_ascii=False, indent=1)

    conta = {}
    for v in out:
        conta[v['category']] = conta.get(v['category'], 0) + 1
    print('Selezione:', conta)
    for v in out:
        print('  [%s%s] (%d fonti) %s' % (v['category'], '/' + v['area'] if v['area'] else '', v['n_sources'], v['title'][:90]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
