#!/usr/bin/env python3
"""
Rassegna Stampa — generatore della cache delle notizie.

Gira su GitHub Actions (non su Altervista, che blocca le connessioni in uscita):
scarica i feed RSS elencati in feeds.json e produce cache/articles.json, che
poi viene caricato via FTP sullo spazio web. La pagina index.php legge quel
file e non ha bisogno di collegarsi a nessun sito esterno.

Usa solo la libreria standard di Python: niente da installare.

Uso:
    python3 build_cache.py [cartella_di_uscita]
"""

import concurrent.futures
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

TIMEOUT = 25
MAX_AGE_HOURS = 60

# Spazi dei nomi usati dai vari formati di feed.
NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'rss1': 'http://purl.org/rss/1.0/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'dc': 'http://purl.org/dc/elements/1.1/',
}


def scarica(url):
    """Scarica un feed. Solleva un'eccezione se non ci riesce."""
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def pulisci_testo(grezzo, max_len=400):
    """Toglie HTML, spazi doppi e punteggiatura urlata; accorcia senza tagliare parole."""
    if not grezzo:
        return ''
    testo = re.sub(r'<[^>]+>', ' ', grezzo)
    testo = html.unescape(testo)
    testo = re.sub(r'\s+', ' ', testo).strip()
    testo = re.sub(r'([!?])\1+', r'\1', testo)
    if len(testo) > max_len:
        testo = testo[:max_len]
        testo = re.sub(r'\s+\S*$', '', testo) + '…'
    return testo


def pulisci_titolo(titolo):
    """Normalizza il titolo togliendo l'effetto urlato (TUTTO MAIUSCOLO, '!!!')."""
    t = html.unescape((titolo or '').strip())
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'([!?])\1+', r'\1', t)
    if len(t) > 8 and t == t.upper():
        t = t.title()
    return t


def _testo(nodo):
    return (nodo.text or '') if nodo is not None else ''


def _quando(stringa):
    """Interpreta le date dei feed: RFC822 (RSS) oppure ISO 8601 (Atom)."""
    if not stringa:
        return None
    stringa = stringa.strip()
    try:
        d = parsedate_to_datetime(stringa)
        if d is not None:
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return int(d.timestamp())
    except (TypeError, ValueError):
        pass
    try:
        d = datetime.fromisoformat(stringa.replace('Z', '+00:00'))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return int(d.timestamp())
    except ValueError:
        return None


def analizza(xml_bytes, meta):
    """Estrae gli articoli da un feed RSS 2.0, RSS 1.0/RDF o Atom."""
    radice = ET.fromstring(xml_bytes)
    nodi = (radice.findall('./channel/item')          # RSS 2.0
            or radice.findall('.//rss1:item', NS)      # RSS 1.0 / RDF (Deutsche Welle)
            or radice.findall('.//atom:entry', NS))    # Atom

    adesso = int(datetime.now(timezone.utc).timestamp())
    articoli = []

    for n in nodi:
        titolo = _testo(n.find('title')) or _testo(n.find('atom:title', NS)) \
            or _testo(n.find('rss1:title', NS))
        titolo = pulisci_titolo(titolo)
        if not titolo:
            continue

        # Il link: negli Atom sta nell'attributo href
        link = _testo(n.find('link')) or _testo(n.find('rss1:link', NS))
        if not link:
            for ln in n.findall('atom:link', NS):
                rel = ln.get('rel', 'alternate')
                if rel == 'alternate' and ln.get('href'):
                    link = ln.get('href')
                    break
        link = (link or '').strip()
        if not link:
            continue

        descr = (_testo(n.find('description'))
                 or _testo(n.find('rss1:description', NS))
                 or _testo(n.find('atom:summary', NS))
                 or _testo(n.find('content:encoded', NS))
                 or _testo(n.find('atom:content', NS)))

        data = (_testo(n.find('pubDate'))
                or _testo(n.find('dc:date', NS))
                or _testo(n.find('atom:published', NS))
                or _testo(n.find('atom:updated', NS)))
        ts = _quando(data) or adesso

        articoli.append({
            'title': titolo,
            'link': link,
            'description': pulisci_testo(descr),
            'pub_ts': ts,
            'source': meta['name'],
            'source_priority': int(meta['priority']),
            'section': meta['section'],
        })

    return articoli


def lavora_feed(meta):
    """Scarica e analizza un singolo feed, senza mai far fallire tutto il resto."""
    try:
        dati = scarica(meta['url'])
    except urllib.error.HTTPError as e:
        return meta, [], 'HTTP %s' % e.code
    except Exception as e:                      # rete, timeout, DNS...
        return meta, [], type(e).__name__ + ': ' + str(e)[:80]
    try:
        return meta, analizza(dati, meta), None
    except ET.ParseError as e:
        return meta, [], 'XML non valido: %s' % str(e)[:80]


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    uscita = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base, 'cache')

    with open(os.path.join(base, 'feeds.json'), encoding='utf-8') as f:
        feeds = json.load(f)

    print('Scarico %d fonti...\n' % len(feeds))

    risultati = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for meta, articoli, errore in ex.map(lavora_feed, feeds):
            risultati.append((meta, articoli, errore))

    tutti = []
    falliti = 0
    for meta, articoli, errore in risultati:
        if errore:
            falliti += 1
            print('  %-22s ERRORE: %s' % (meta['name'], errore))
        else:
            print('  %-22s %d articoli' % (meta['name'], len(articoli)))
            tutti.extend(articoli)

    # Toglie i doppioni (stesso link) e le notizie troppo vecchie.
    adesso = int(datetime.now(timezone.utc).timestamp())
    limite = adesso - MAX_AGE_HOURS * 3600
    per_link = {}
    for a in tutti:
        if a['pub_ts'] >= limite:
            per_link[a['link']] = a
    articoli = sorted(per_link.values(), key=lambda a: a['pub_ts'], reverse=True)

    print('\n%d fonti su %d hanno risposto' % (len(feeds) - falliti, len(feeds)))
    print('%d articoli unici e recenti' % len(articoli))

    if not articoli:
        # Meglio interrompersi che sovrascrivere una cache buona con una vuota.
        print('\nERRORE: nessun articolo scaricato, non aggiorno il file.')
        return 1

    os.makedirs(uscita, exist_ok=True)
    percorso = os.path.join(uscita, 'articles.json')
    with open(percorso, 'w', encoding='utf-8') as f:
        json.dump({'updated_at': adesso, 'articles': articoli},
                  f, ensure_ascii=False, separators=(',', ':'))

    print('Scritto %s (%.1f KB)' % (percorso, os.path.getsize(percorso) / 1024))
    return 0


if __name__ == '__main__':
    sys.exit(main())
