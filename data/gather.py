"""Refresh data/cities.json and data/counties.json from Wikipedia + Wikidata.
Run from the repo root: python3 data/gather.py"""
import json, re, time, requests
from bs4 import BeautifulSoup

H = {'User-Agent': 'OregonInformationBot/1.0 (mattriedl@hotmail.com)'}
API = 'https://en.wikipedia.org/w/api.php'

def clean(t):
    return re.sub(r'\[[^\]]*\]', '', t).replace('\u2020', '').replace('\u2021', '').strip()

def num(t):
    t = re.sub(r'[^\d.]', '', clean(t))
    return t

def parse_table(page, idx):
    r = requests.get(API, headers=H, params={'action': 'parse', 'page': page, 'prop': 'text', 'format': 'json', 'formatversion': 2}).json()
    soup = BeautifulSoup(r['parse']['text'], 'lxml')
    tables = [t for t in soup.find_all('table', class_='wikitable')]
    return tables[idx]

def cities():
    t = parse_table('List_of_cities_in_Oregon', 1)
    out = []
    for tr in t.find_all('tr'):
        cells = tr.find_all(['th', 'td'])
        if len(cells) < 9: continue
        a = cells[0].find('a')
        if not a: continue
        name = clean(cells[0].get_text())
        if name == 'Name': continue
        txt = cells[0].get_text()
        out.append({
            'name': name, 'title': a['title'], 'county': clean(cells[1].get_text()),
            'pop2020': num(cells[2].get_text()), 'pop2010': num(cells[3].get_text()),
            'change': clean(cells[4].get_text()), 'area_sqmi': num(cells[5].get_text()),
            'incorporated': num(cells[8].get_text()),
            'seat': '\u2020' in txt or '\u2021' in txt, 'capital': '\u2021' in txt,
        })
    return out

def counties():
    t = parse_table('List_of_counties_in_Oregon', 0)
    out = []
    for tr in t.find_all('tr'):
        cells = tr.find_all(['th', 'td'])
        if len(cells) < 8: continue
        a = cells[0].find('a')
        if not a or 'County' not in cells[0].get_text(): continue
        area = clean(cells[7].get_text())
        out.append({
            'name': clean(cells[0].get_text()).replace(' County', ''), 'title': a['title'],
            'fips': num(cells[1].get_text()), 'seat': clean(cells[2].get_text()),
            'est': num(cells[3].get_text()), 'origin': clean(cells[4].get_text()),
            'etymology': clean(cells[5].get_text()), 'pop2020': num(cells[6].get_text()),
            'area_sqmi': re.sub(r'[^\d]', '', area.split('sq')[0]),
        })
    return out

def enrich(items):
    """Add summary extract, coordinates, official website, wikipedia url."""
    titles = [i['title'] for i in items]
    info = {}
    for k in range(0, len(titles), 20):
        chunk = titles[k:k + 20]
        r = requests.get(API, headers=H, params={
            'action': 'query', 'format': 'json', 'formatversion': 2, 'redirects': 1,
            'prop': 'extracts|coordinates|pageprops|info|pageimages', 'piprop': 'thumbnail|name', 'pithumbsize': 960, 'pilimit': 50, 'inprop': 'url',
            'exintro': 1, 'explaintext': 1, 'exlimit': 'max', 'ppprop': 'wikibase_item',
            'titles': '|'.join(chunk)}).json()
        redir = {x['from']: x['to'] for x in r['query'].get('redirects', [])}
        norm = {x['from']: x['to'] for x in r['query'].get('normalized', [])}
        pages = {p['title']: p for p in r['query']['pages']}
        for t in chunk:
            tt = redir.get(norm.get(t, t), norm.get(t, t))
            info[t] = pages.get(tt, {})
        time.sleep(0.5)
    qids = [p.get('pageprops', {}).get('wikibase_item') for p in info.values()]
    qids = [q for q in qids if q]
    web, geo = {}, {}
    for k in range(0, len(qids), 50):
        r = requests.get('https://www.wikidata.org/w/api.php', headers=H, params={
            'action': 'wbgetentities', 'format': 'json', 'props': 'claims',
            'ids': '|'.join(qids[k:k + 50])}).json()
        for q, e in r.get('entities', {}).items():
            c = e.get('claims', {}).get('P856', [])
            if c:
                try: web[q] = c[0]['mainsnak']['datavalue']['value']
                except KeyError: pass
            g = e.get('claims', {}).get('P625', [])
            if g:
                try:
                    v = g[0]['mainsnak']['datavalue']['value']; geo[q] = (v['latitude'], v['longitude'])
                except KeyError: pass
        time.sleep(0.5)
    for i in items:
        p = info.get(i['title'], {})
        ex = (p.get('extract') or '').strip()
        i['summary'] = ex
        co = (p.get('coordinates') or [{}])[0]
        i['lat'], i['lon'] = co.get('lat'), co.get('lon')
        i['wiki_url'] = p.get('fullurl', '')
        i['image'] = (p.get('thumbnail') or {}).get('source', '')
        i['image_file'] = p.get('pageimage', '')
        q = p.get('pageprops', {}).get('wikibase_item')
        i['website'] = web.get(q, '')
        if i['lat'] is None and q in geo: i['lat'], i['lon'] = geo[q]
    return items

if __name__ == '__main__':
    c = enrich(cities()); print('cities', len(c))
    json.dump(c, open('data/cities.json', 'w'), indent=1, ensure_ascii=False)
    k = enrich(counties()); print('counties', len(k))
    json.dump(k, open('data/counties.json', 'w'), indent=1, ensure_ascii=False)
