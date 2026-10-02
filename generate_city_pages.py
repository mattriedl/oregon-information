#!/usr/bin/env python3
"""Oregon Information - site generator.

Builds every city page, every county page, the cities A-Z directory, the About /
Contact / Privacy pages, sitemap.xml and robots.txt from:
  data/cities.json    (241 incorporated cities: 2020/2010 Census, area, incorporation,
                       coordinates, official website, Wikipedia summary + photo)
  data/counties.json  (36 counties)
  custom_city_content.json (optional hand-written extras, keyed like "portland")
Data refresh: python3 data/gather.py   |   Build: python3 generate_city_pages.py
"""

import html, json, math, os, re, shutil
from datetime import date

BASE_URL     = 'https://oregoninformation.com'
SITE_NAME    = 'Oregon Information'
CONTACT_EMAIL = 'contact@oregoninformation.com'
ANALYTICS_ID = ''
OUT          = '.'
TODAY        = date.today().isoformat()
DEFAULT_IMG  = f'{BASE_URL}/assets/og-image.png'
SLUG_OVERRIDES = {'Mt. Angel': 'mount-angel'}   # keep existing URL

COUNTY_INFO = {
 'Multnomah':('Portland Metro','Portland General Electric'),'Washington':('Portland Metro','Portland General Electric'),
 'Clackamas':('Portland Metro','Portland General Electric'),'Columbia':('Northwest Oregon','Portland General Electric'),
 'Clatsop':('North Coast','Pacific Power'),'Tillamook':('North Coast','Tillamook PUD'),
 'Yamhill':('Willamette Valley','Portland General Electric'),'Marion':('Willamette Valley','Portland General Electric'),
 'Polk':('Willamette Valley','Portland General Electric / Pacific Power'),'Linn':('Willamette Valley','Pacific Power'),
 'Benton':('Willamette Valley','Pacific Power'),'Lane':('Willamette Valley','EWEB / Pacific Power'),
 'Lincoln':('Central Coast','Central Lincoln PUD'),'Douglas':('Southwest Oregon','Pacific Power / Douglas Electric Cooperative'),
 'Coos':('South Coast','Pacific Power / Coos-Curry Electric Cooperative'),'Curry':('South Coast','Coos-Curry Electric Cooperative'),
 'Josephine':('Rogue Valley','Pacific Power'),'Jackson':('Rogue Valley','Pacific Power'),
 'Klamath':('South Central Oregon','Pacific Power'),'Lake':('South Central Oregon','Pacific Power / Surprise Valley Electric'),
 'Deschutes':('Central Oregon','Pacific Power / Central Electric Cooperative'),'Jefferson':('Central Oregon','Pacific Power'),
 'Crook':('Central Oregon','Pacific Power'),'Hood River':('Columbia River Gorge','Pacific Power'),
 'Wasco':('Columbia River Gorge','Northern Wasco County PUD'),'Sherman':('North Central Oregon','Wasco Electric Cooperative'),
 'Gilliam':('North Central Oregon','Columbia Basin Electric Cooperative'),'Morrow':('North Central Oregon','Umatilla Electric Cooperative'),
 'Umatilla':('Eastern Oregon','Pacific Power / Umatilla Electric Cooperative'),'Union':('Northeast Oregon','Oregon Trail Electric Cooperative'),
 'Wallowa':('Northeast Oregon','Pacific Power'),'Baker':('Northeast Oregon','Oregon Trail Electric Cooperative'),
 'Grant':('Eastern Oregon','Oregon Trail Electric Cooperative'),'Harney':('Southeast Oregon','Harney Electric Cooperative'),
 'Malheur':('Southeast Oregon','Idaho Power'),'Wheeler':('North Central Oregon','Columbia Power Cooperative'),
}

STATE_LINKS = [
 ('Oregon.gov', 'https://www.oregon.gov/'),
 ('Oregon DMV', 'https://www.oregon.gov/odot/dmv/'),
 ('WorkSource Oregon', 'https://www.worksourceoregon.org/'),
 ('Oregon Dept. of Education', 'https://www.oregon.gov/ode/'),
 ('Oregon Health Plan', 'https://one.oregon.gov/'),
 ('SNAP Food Benefits', 'https://www.oregon.gov/odhs/food/pages/snap.aspx'),
 ('Oregon Food Bank', 'https://www.oregonfoodbank.org/'),
 ('211info', 'https://www.211info.org/'),
 ('Oregon Housing', 'https://www.oregon.gov/ohcs/'),
 ('Travel Oregon', 'https://traveloregon.com/'),
]

CSS = ":root{--gd:#14382a;--g:#1a5632;--gold:#c8a24b;--blue:#1f4e79;--bg:#f6f8f7;--tx:#22302b;--mu:#5c6b64}*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Inter',system-ui,sans-serif;color:var(--tx);line-height:1.6;background:#fff}h1,h2,h3{font-family:Georgia,serif;line-height:1.25}.wrap{max-width:1000px;margin:0 auto;padding:0 24px}.hd{background:var(--gd);color:#fff;padding:14px 0;position:sticky;top:0;z-index:50}.hd nav{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}.logo{display:flex;align-items:center;gap:10px;font-weight:800;font-size:1.1rem;color:#fff;text-decoration:none}.badge{width:30px;height:30px;background:var(--gold);border-radius:50%;display:flex;align-items:center;justify-content:center}.nl{list-style:none;display:flex;gap:16px;flex-wrap:wrap}.nl a{color:#dbe7e0;text-decoration:none;font-weight:600;font-size:.9rem}.nl a:hover{color:var(--gold)}.hero{background:linear-gradient(160deg,var(--gd),var(--g));color:#fff;padding:52px 0 44px;margin-bottom:36px}.hero h1{font-size:clamp(1.6rem,4vw,2.4rem);max-width:760px}.hero p{color:#dceee3;margin-top:12px;max-width:640px}.crumbs{font-size:.88rem;color:var(--mu);padding:14px 0 0}.crumbs a{color:var(--blue);text-decoration:none}h2.st{font-size:1.45rem;color:var(--gd);margin:36px 0 16px;border-bottom:3px solid var(--g);padding-bottom:8px}.facts{background:var(--bg);border:1px solid #e3eae6;border-radius:10px;padding:20px;margin:24px 0}.facts table{width:100%;border-collapse:collapse}.facts th{text-align:left;padding:9px;color:var(--gd);border-bottom:2px solid var(--g);width:35%;vertical-align:top}.facts td{padding:9px;border-bottom:1px solid #e3eae6}.facts a,.prose a,.tbl a{color:var(--blue)}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin:24px 0}.card{background:#fff;border:1px solid #e3eae6;border-top:4px solid var(--g);border-radius:10px;padding:20px}.card h3{font-size:1rem;color:var(--gd);margin-bottom:10px}.card ul{list-style:none}.card li{padding:6px 0;border-bottom:1px dashed #e3eae6;font-size:.92rem}.card a{color:var(--blue);text-decoration:none;font-weight:600}.faq details{background:#fff;border:1px solid #e3eae6;border-radius:8px;margin:9px 0;padding:0 16px}.faq summary{cursor:pointer;font-weight:600;padding:13px 0;color:var(--gd)}.faq p{padding:0 0 14px;font-size:.94rem}.faq ul{padding-left:20px}.faq li{padding:3px 0}.faq a{color:var(--blue)}.back{margin-top:40px;padding-top:18px;border-top:1px solid #e3eae6}.back a{color:var(--g);font-weight:700;text-decoration:none}.ft{background:var(--gd);color:#cfe0d6;padding:30px 0;text-align:center;font-size:.84rem;margin-top:44px}.ft a{color:#fff;text-decoration:none;font-weight:600}.ft .fl{margin-bottom:10px}.ft .fl a{margin:0 9px}.dir-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin:16px 0 26px}.dir-list a{background:var(--bg);border:1px solid #d7e2db;border-radius:6px;padding:10px 14px;text-decoration:none;color:var(--blue);font-weight:600;font-size:.9rem}.dir-list a small{display:block;color:var(--mu);font-weight:400;font-size:.78rem}.dir-list a:hover{background:var(--g);color:#fff}.dir-list a:hover small{color:#dceee3}.photo{margin:24px 0}.photo img{width:100%;max-height:440px;object-fit:cover;border-radius:10px;background:var(--bg)}.photo figcaption,.src{font-size:.8rem;color:var(--mu);margin-top:6px}.src a{color:var(--mu)}.prose p{margin:0 0 14px}.tbl{width:100%;border-collapse:collapse;margin:16px 0;font-size:.93rem}.tbl th{background:var(--gd);color:#fff;text-align:left;padding:9px}.tbl td{padding:9px;border-bottom:1px solid #e3eae6}.tbl tr:nth-child(even) td{background:var(--bg)}.alpha{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 20px}.alpha a{background:var(--gd);color:#fff;text-decoration:none;font-weight:700;padding:6px 11px;border-radius:5px}.alpha a:hover{background:var(--gold)}h3.letter{font-size:1.3rem;color:var(--gd);margin-top:22px;scroll-margin-top:80px}#q{width:100%;padding:12px 14px;font-size:1rem;border:2px solid #d7e2db;border-radius:8px}"


def slug(name):
    if name in SLUG_OVERRIDES: return SLUG_OVERRIDES[name]
    s = name.lower().replace('.', '').replace("'", '').replace(' ', '-')
    while '--' in s: s = s.replace('--', '-')
    return s.strip('-')


def e(t):
    return html.escape(str(t), quote=True)


def n(v):
    try: return f'{int(float(v)):,}'
    except (TypeError, ValueError): return ''


def host(url):
    return re.sub(r'^https?://(www\.)?', '', url).rstrip('/')


def miles(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a['lat'], a['lon'], b['lat'], b['lon']))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def summary_html(text, limit=1100):
    """Clean a Wikipedia intro (drop stripped pronunciation guides) and trim to whole paragraphs/sentences."""
    text = re.sub(r' \(\s[^)]*\)', '', text or '')
    text = re.sub(r'\s+([,.])', r'\1', text)
    out, total = [], 0
    for para in [p.strip() for p in text.split('\n') if p.strip()]:
        if total + len(para) > limit and out: break
        if len(para) > limit:
            cut = para[:limit]
            para = cut[:cut.rfind('. ') + 1] if '. ' in cut else cut
        out.append(para); total += len(para)
    return ''.join(f'<p>{e(p)}</p>' for p in out)


def head(title, desc, path, og_type='website', image=None, extra=''):
    url = f'{BASE_URL}{path}'
    img = image or DEFAULT_IMG
    ga = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={ANALYTICS_ID}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","{ANALYTICS_ID}");</script>' if ANALYTICS_ID else '')
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{e(title)}</title>'
            f'<meta name="description" content="{e(desc)}"><meta name="robots" content="index, follow">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0"><link rel="canonical" href="{url}">'
            f'<meta property="og:site_name" content="{SITE_NAME}"><meta property="og:type" content="{og_type}">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:url" content="{url}"><meta property="og:image" content="{e(img)}">'
            f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}">'
            f'<meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{e(img)}">'
            f'{extra}{ga}<style>{CSS}</style></head><body>')


def header(up):
    return (f'<header class="hd"><div class="wrap"><nav><a class="logo" href="{up}index.html"><span class="badge">&#127795;</span> Oregon Information</a>'
            f'<ul class="nl"><li><a href="{up}moving-to-oregon/index.html">Moving</a></li><li><a href="{up}visit-oregon/index.html">Visiting</a></li>'
            f'<li><a href="{up}counties/index.html">Counties</a></li><li><a href="{up}cities/index.html">Cities A&ndash;Z</a></li></ul></nav></div></header>')


def footer(up, note=''):
    return (f'<footer class="ft"><div class="wrap"><p class="fl"><a href="{up}about/index.html">About</a><a href="{up}contact/index.html">Contact</a>'
            f'<a href="{up}privacy/index.html">Privacy Policy</a><a href="{up}cities/index.html">Cities</a><a href="{up}counties/index.html">Counties</a></p>'
            f'<p>&copy; 2026 Oregon Information &mdash; independent resource, not affiliated with the State of Oregon.{note}</p></div></footer></body></html>')


def ld(obj):
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'


def photo(item, alt):
    if not item.get('image'): return ''
    f = item.get('image_file', '')
    credit = f'<a href="https://commons.wikimedia.org/wiki/File:{e(f)}" target="_blank" rel="noopener">Wikimedia Commons</a>' if f else 'Wikimedia Commons'
    fit = ' style="object-fit:contain"' if f.lower().endswith(('.svg', '.png')) else ''
    return (f'<figure class="photo"><img src="{e(item["image"])}"{fit} alt="{e(alt)}" loading="lazy">'
            f'<figcaption>Image: {credit} (see file page for author and license)</figcaption></figure>')


def wiki_credit(item):
    return (f'<p class="src">Source: adapted from <a href="{e(item["wiki_url"])}" target="_blank" rel="noopener">Wikipedia</a>, '
            f'available under <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a>.</p>')


def faq_for(city, county, region, electric):
    k = sum(ord(c) for c in city) % 3
    q = [
     (f"What is the cost of living in {city}, Oregon?", f"{city} lies in the {region} region, where costs vary mainly by housing. Oregon charges no statewide sales tax."),
     (f"What utilities do I set up when moving to {city}?", f"Electricity in this area is generally provided by {electric} (confirm by address); natural gas, where available, by NW Natural, Avista or Cascade Natural Gas. Water, sewer, and trash are typically arranged through the City of {city}."),
     (f"How do I find a job near {city}?", "WorkSource Oregon offers free career coaching, and iMatchSkills is the state's largest job board."),
     (f"Which schools serve families in {city}?", f"Assignment depends on your exact address. Start with the Oregon Department of Education directory or the {county} County district office."),
     (f"How soon must I register my car after moving to {city}?", "Within 30 days of establishing residency — both the vehicle registration and an Oregon driver's license."),
     (f"Are there food banks or assistance programs near {city}?", f"Yes. Apply for SNAP at the ONE Oregon portal, find a pantry through Oregon Food Bank, or dial 211 for {county} County community resources."),
    ]
    if k == 1: q[0] = (f"Is {city}, Oregon affordable to live in?", q[0][1]); q[2] = (f"What is the job market like around {city}?", q[2][1])
    elif k == 2: q[1] = (f"How do I connect utilities in {city}?", q[1][1]); q[4] = (f"After moving to {city}, what's the DMV deadline?", q[4][1])
    return q


def county_links(counties_str, up):
    return ', '.join(f'<a href="{up}counties/{slug(c)}/index.html">{e(c)} County</a>' for c in counties_str)


def city_page(c, all_cities, custom):
    name = c['name']; counties = c['counties']; county = counties[0]
    region, electric = COUNTY_INFO.get(county, ('Oregon', 'Local utility'))
    x = custom.get(name.lower().replace(' ', '_'), {})
    employers = x.get('major_employers', f'Employers in and around {name} and {county} County')
    pop = n(c['pop2020'])
    area = c.get('area_sqmi')
    density = f'{float(c["pop2020"]) / float(area):,.0f} people per sq mi' if area and float(area) > 0 else ''
    status = 'Incorporated city'
    if c['capital']: status += ' &mdash; Oregon state capital and county seat'
    elif c['seat']: status += f' &mdash; county seat of {e(county)} County'
    rows = [('County' if len(counties) == 1 else 'Counties', county_links(counties, '../../')), ('Region', e(region)),
            ('Population (2020 Census)', pop or 'n/a'), ('Population (2010 Census)', n(c['pop2010']) or 'n/a'),
            ('Change 2010&ndash;2020', e(c['change']) or 'n/a')]
    if area: rows.append(('Land area', f'{float(area):g} sq mi'))
    if density: rows.append(('Population density', density))
    if c.get('incorporated'): rows.append(('Incorporated', e(c['incorporated'])))
    rows.append(('Status', status))
    if c.get('website'): rows.append(('Official city website', f'<a href="{e(c["website"])}" target="_blank" rel="noopener">{e(host(c["website"]))}</a>'))
    if c.get('lat') is not None: rows.append(('Coordinates', f'{c["lat"]:.4f}&deg; N, {abs(c["lon"]):.4f}&deg; W'))
    for k, label in (('nearest_hospital', 'Nearest major hospital'), ('transit', 'Public transit')):
        if x.get(k): rows.append((label, e(x[k])))
    facts = ''.join(f'<tr><th>{a}</th><td>{b}</td></tr>' for a, b in rows)
    near = sorted((miles(c, o), o) for o in all_cities if o is not c and o.get('lat') is not None and c.get('lat') is not None)[:6]
    near_html = ''.join(f'<a href="../{slug(o["name"])}/index.html">{e(o["name"])}<small>{d:.0f} mi &middot; pop. {n(o["pop2020"])}</small></a>' for d, o in near)
    fq = faq_for(name, county, region, electric)
    if pop: fq.insert(0, (f"What is the population of {name}, Oregon?", f"{name} had {pop} residents at the 2020 U.S. Census (up from {n(c['pop2010'])} in 2010)." if c['change'].startswith('+') else f"{name} had {pop} residents at the 2020 U.S. Census ({n(c['pop2010'])} in 2010)."))
    faq_details = '\n'.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in fq)
    path = f'/cities/{slug(name)}/'
    desc = f'{name}, Oregon ({county} County){": population " + pop + " (2020 Census)" if pop else ""}. City facts, history, nearby cities, moving and utility checklist, jobs, schools, DMV steps, and official links.'
    city_ld = {'@context': 'https://schema.org', '@type': 'City', 'name': f'{name}, Oregon', 'url': f'{BASE_URL}{path}',
               'containedInPlace': {'@type': 'AdministrativeArea', 'name': f'{county} County, Oregon'}}
    if c.get('lat') is not None: city_ld['geo'] = {'@type': 'GeoCoordinates', 'latitude': c['lat'], 'longitude': c['lon']}
    same = [u for u in (c.get('wiki_url'), c.get('website')) if u]
    if same: city_ld['sameAs'] = same
    if c.get('image'): city_ld['image'] = c['image']
    bread = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{BASE_URL}/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Oregon Cities', 'item': f'{BASE_URL}/cities/'},
        {'@type': 'ListItem', 'position': 3, 'name': name, 'item': f'{BASE_URL}{path}'}]}
    faq_ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in fq[:5]]}
    sl = '\n'.join(f'<li><a href="{u}" target="_blank" rel="noopener">{t}</a></li>' for t, u in STATE_LINKS)
    local = []
    if c.get('website'): local.append(f'<li><a href="{e(c["website"])}" target="_blank" rel="noopener">City of {e(name)} official website</a></li>')
    for cn in counties:
        cw = COUNTY_SITES.get(cn)
        if cw: local.append(f'<li><a href="{e(cw)}" target="_blank" rel="noopener">{e(cn)} County official website</a></li>')
    local.append(f'<li><a href="../../counties/{slug(county)}/index.html">{e(county)} County guide on Oregon Information</a></li>')
    if c.get('wiki_url'): local.append(f'<li><a href="{e(c["wiki_url"])}" target="_blank" rel="noopener">{e(name)} on Wikipedia</a></li>')
    lead = f'{e(name)} is an incorporated city in {county_links(counties, "../../")}, in Oregon&rsquo;s {e(region)} region' + (f', with a 2020 Census population of {pop}.' if pop else '.')
    return (head(f'{name}, Oregon | Population, Facts, Moving Guide & Local Links', desc, path, 'article', c.get('image'), ld(city_ld) + ld(bread) + ld(faq_ld))
            + header('../../')
            + f'<div class="hero"><div class="wrap"><h1>{e(name)}, Oregon</h1><p>Located in {e(county)} County in the {e(region)} region &mdash; city facts, history, a newcomer checklist, and official links in one place.</p></div></div>'
            + f'<main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="../../index.html">Home</a> &rsaquo; <a href="../index.html">Oregon Cities</a> &rsaquo; {e(name)}</nav>'
            + f'<h2 class="st">Quick Facts</h2><section class="facts"><table>{facts}</table></section>'
            + f'<h2 class="st">About {e(name)}</h2><section class="prose"><p>{lead}</p>{summary_html(c["summary"])}{wiki_credit(c) if c.get("wiki_url") else ""}</section>'
            + photo(c, f'{name}, Oregon')
            + f'<h2 class="st">Moving to {e(name)}</h2><div class="cards"><div class="card"><h3>&#9889; Utilities Checklist</h3><ul><li><strong>Electricity:</strong> {e(electric)} (confirm by address)</li><li><strong>Natural gas:</strong> NW Natural, Avista or Cascade Natural Gas (where available)</li><li><strong>Water &amp; sewer:</strong> City of {e(name)}</li><li><strong>Trash:</strong> Franchised hauler &mdash; verify by service address</li><li><strong>Internet:</strong> Compare providers at the <a href="https://broadbandmap.fcc.gov/" target="_blank" rel="noopener">FCC broadband map</a></li></ul></div>'
            + f'<div class="card"><h3>&#128188; Jobs &amp; Economy</h3><ul><li><strong>Notable employers:</strong> {e(employers)}</li><li><a href="https://www.worksourceoregon.org/" target="_blank" rel="noopener">WorkSource Oregon (free)</a></li><li><a href="https://www.imatchskills.org/" target="_blank" rel="noopener">iMatchSkills job board</a></li></ul></div>'
            + '<div class="card"><h3>&#127968; Housing</h3><ul><li><a href="https://www.zillow.com/or/" target="_blank" rel="noopener">Zillow Oregon</a></li><li><a href="https://www.apartments.com/oregon/" target="_blank" rel="noopener">Apartments.com</a></li><li><a href="https://www.oregon.gov/ohcs/" target="_blank" rel="noopener">OHCS buyer/renter programs</a></li></ul></div>'
            + '<div class="card"><h3>&#128663; DMV Steps</h3><ul><li>Vehicle registration &amp; Oregon license within <strong>30 days</strong></li><li><a href="https://www.oregon.gov/odot/dmv/pages/new_residents.aspx" target="_blank" rel="noopener">New resident guide</a></li><li><a href="https://www.oregon.gov/odot/dmv/pages/find_us.aspx" target="_blank" rel="noopener">Find a DMV office</a></li></ul></div>'
            + f'<div class="card"><h3>&#127891; Schools</h3><ul><li>Districts vary by address &mdash; verify before renting/buying</li><li><a href="https://www.oregon.gov/ode/pages/default.aspx" target="_blank" rel="noopener">Oregon Dept. of Education</a></li><li>Contact the {e(county)} County district office</li></ul></div>'
            + '<div class="card"><h3>&#127973; Healthcare &amp; Assistance</h3><ul><li><a href="https://one.oregon.gov/" target="_blank" rel="noopener">ONE portal (OHP/SNAP)</a></li><li><a href="https://www.oregonfoodbank.org/" target="_blank" rel="noopener">Oregon Food Bank</a></li><li><a href="https://www.211info.org/" target="_blank" rel="noopener">Dial 211 for local help</a></li></ul></div></div>'
            + (f'<h2 class="st">Nearby Cities</h2><nav class="dir-list">{near_html}</nav>' if near_html else '')
            + f'<h2 class="st">Frequently Asked Questions</h2><section class="faq">{faq_details}</section>'
            + f'<h2 class="st">Local &amp; Official Links</h2><section class="faq"><ul>{"".join(local)}{sl}</ul></section>'
            + '<p class="back"><a href="../index.html">&larr; All Oregon Cities</a></p></div></main>'
            + footer('../../', '<br>Population: U.S. Census Bureau (2010, 2020). Background text: Wikipedia (CC BY-SA 4.0).'))


COUNTY_SITES = {}


def county_page(k, cities):
    name = k['name']; region, electric = COUNTY_INFO.get(name, ('Oregon', 'Local utility'))
    members = sorted([c for c in cities if name in c['counties']], key=lambda c: -float(c['pop2020'] or 0))
    pop = n(k['pop2020']); area = k.get('area_sqmi')
    density = f'{float(k["pop2020"]) / float(area):,.1f} people per sq mi' if area and float(area) > 0 else ''
    seat = next((c for c in cities if c['name'] == k['seat']), None)
    seat_html = f'<a href="../../cities/{slug(seat["name"])}/index.html">{e(seat["name"])}</a>' if seat else e(k['seat'])
    rows = [('County seat', seat_html), ('Region', e(region)), ('Population (2020 Census)', pop), ('Land &amp; water area', f'{n(area)} sq mi' if area else 'n/a')]
    if density: rows.append(('Population density', density))
    rows += [('Established', e(k['est'])), ('Formed from', e(k['origin'])), ('Name origin', e(k['etymology'])),
             ('Incorporated cities', str(len(members))), ('Main electric utility', e(electric)), ('FIPS code', f'41{e(k["fips"])}')]
    if k.get('website'): rows.append(('Official county website', f'<a href="{e(k["website"])}" target="_blank" rel="noopener">{e(host(k["website"]))}</a>'))
    facts = ''.join(f'<tr><th>{a}</th><td>{b}</td></tr>' for a, b in rows)
    trs = ''.join(f'<tr><td><a href="../../cities/{slug(c["name"])}/index.html">{e(c["name"])}</a>{" &#9733;" if c["name"] == k["seat"] else ""}</td><td>{n(c["pop2020"])}</td><td>{e(c.get("incorporated", ""))}</td></tr>' for c in members)
    path = f'/counties/{slug(name)}/'
    desc = f'{name} County, Oregon: county seat {k["seat"]}, population {pop} (2020 Census), {len(members)} incorporated cities, history, and official links.'
    ld_obj = {'@context': 'https://schema.org', '@type': 'AdministrativeArea', 'name': f'{name} County, Oregon', 'url': f'{BASE_URL}{path}',
              'containedInPlace': {'@type': 'State', 'name': 'Oregon'}}
    if k.get('lat') is not None: ld_obj['geo'] = {'@type': 'GeoCoordinates', 'latitude': k['lat'], 'longitude': k['lon']}
    same = [u for u in (k.get('wiki_url'), k.get('website')) if u]
    if same: ld_obj['sameAs'] = same
    bread = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{BASE_URL}/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Oregon Counties', 'item': f'{BASE_URL}/counties/'},
        {'@type': 'ListItem', 'position': 3, 'name': f'{name} County', 'item': f'{BASE_URL}{path}'}]}
    links = []
    if k.get('website'): links.append(f'<li><a href="{e(k["website"])}" target="_blank" rel="noopener">{e(name)} County official website</a></li>')
    links += ['<li><a href="https://www.211info.org/" target="_blank" rel="noopener">211info &mdash; local assistance</a></li>',
              '<li><a href="https://www.oregon.gov/odot/dmv/pages/find_us.aspx" target="_blank" rel="noopener">Find a DMV office</a></li>',
              '<li><a href="https://www.worksourceoregon.org/" target="_blank" rel="noopener">WorkSource Oregon</a></li>',
              '<li><a href="https://aocweb.org/" target="_blank" rel="noopener">Association of Oregon Counties</a></li>']
    if k.get('wiki_url'): links.append(f'<li><a href="{e(k["wiki_url"])}" target="_blank" rel="noopener">{e(name)} County on Wikipedia</a></li>')
    return (head(f'{name} County, Oregon | Cities, Population, Facts & Links', desc, path, 'article', k.get('image'), ld(ld_obj) + ld(bread))
            + header('../../')
            + f'<div class="hero"><div class="wrap"><h1>{e(name)} County, Oregon</h1><p>County seat: {e(k["seat"])} &middot; {e(region)} region &middot; {len(members)} incorporated cities</p></div></div>'
            + f'<main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="../../index.html">Home</a> &rsaquo; <a href="../index.html">Oregon Counties</a> &rsaquo; {e(name)} County</nav>'
            + f'<h2 class="st">Quick Facts</h2><section class="facts"><table>{facts}</table></section>'
            + f'<h2 class="st">About {e(name)} County</h2><section class="prose">{summary_html(k["summary"], 1400)}{wiki_credit(k) if k.get("wiki_url") else ""}</section>'
            + photo(k, f'{name} County, Oregon')
            + f'<h2 class="st">Cities in {e(name)} County</h2><table class="tbl"><tr><th>City</th><th>Population (2020)</th><th>Incorporated</th></tr>{trs}</table><p class="src">&#9733; county seat. Cities that span more than one county are listed in each.</p>'
            + f'<h2 class="st">Official &amp; Helpful Links</h2><section class="faq"><ul>{"".join(links)}</ul></section>'
            + '<p class="back"><a href="../index.html">&larr; All Oregon Counties</a></p></div></main>'
            + footer('../../', '<br>Population: U.S. Census Bureau 2020. Background text: Wikipedia (CC BY-SA 4.0).'))


def cities_index(cities):
    groups = {}
    for c in sorted(cities, key=lambda x: x['name'].lower()):
        groups.setdefault(c['name'][0].upper(), []).append(c)
    alpha = ''.join(f'<a href="#letter-{L.lower()}">{L}</a>' for L in groups)
    body = ''.join(f'<h3 class="letter" id="letter-{L.lower()}">{L}</h3><nav class="dir-list">' + ''.join(
        f'<a href="{slug(c["name"])}/index.html" data-n="{e(c["name"].lower())} {e(" ".join(c["counties"]).lower())}">{e(c["name"])}<small>{e(", ".join(c["counties"]))} Co. &middot; pop. {n(c["pop2020"])}</small></a>' for c in cs) + '</nav>' for L, cs in groups.items())
    js = "<script>document.getElementById('q').addEventListener('input',function(){var v=this.value.toLowerCase();document.querySelectorAll('.dir-list a').forEach(function(a){a.style.display=a.dataset.n.indexOf(v)>-1?'':'none'});});</script>"
    desc = f'Directory of all {len(cities)} incorporated cities in Oregon with county, 2020 Census population, history, and moving guides.'
    return (head('Oregon Cities A–Z | All 241 Incorporated Cities', desc, '/cities/') + header('../')
            + f'<div class="hero"><div class="wrap"><h1>Oregon Cities A&ndash;Z</h1><p>Every incorporated city in Oregon ({len(cities)} total), with county and 2020 Census population.</p></div></div>'
            + f'<main><div class="wrap"><nav class="crumbs"><a href="../index.html">Home</a> &rsaquo; Oregon Cities</nav><p style="margin:18px 0 8px"><input id="q" type="search" placeholder="Filter by city or county name..." aria-label="Filter cities"></p>'
            + f'<nav class="alpha">{alpha}</nav>{body}</div></main>' + js + footer('../', '<br>Population: U.S. Census Bureau 2020.'))


def simple_page(path, title, desc, h1, sub, body):
    return (head(title, desc, path) + header('../')
            + f'<div class="hero"><div class="wrap"><h1>{h1}</h1><p>{sub}</p></div></div>'
            + f'<main><div class="wrap prose"><nav class="crumbs"><a href="../index.html">Home</a> &rsaquo; {h1}</nav>{body}</div></main>' + footer('../'))


ABOUT = f'''<h2 class="st">What Oregon Information is</h2>
<p>Oregon Information is an independent, free guide to the State of Oregon. It brings together practical facts about all 241 incorporated cities and all 36 counties &mdash; population, history, location, official websites &mdash; along with step-by-step guides for people <a href="../moving-to-oregon/index.html">moving to Oregon</a> and people <a href="../visit-oregon/index.html">visiting</a>.</p>
<h2 class="st">Who it is for</h2>
<p>Newcomers comparing places to live, visitors planning a trip, and Oregonians who want a quick, plain-language starting point before contacting a city, county or state office.</p>
<h2 class="st">Where the information comes from</h2>
<ul style="padding-left:20px">
<li>Population figures: U.S. Census Bureau (2010 and 2020 decennial census).</li>
<li>City and county background, incorporation dates, coordinates and photos: Wikipedia, Wikidata and Wikimedia Commons, used under their Creative Commons licenses with attribution on each page.</li>
<li>Government services and programs: official State of Oregon websites, linked directly.</li>
</ul>
<p>We check sources carefully, but details such as utility providers, school assignments and office hours change. Always confirm with the official agency before making decisions.</p>
<h2 class="st">Independence</h2>
<p>Oregon Information is not affiliated with, endorsed by, or operated by the State of Oregon or any city or county government.</p>
<h2 class="st">Corrections and suggestions</h2>
<p>Spotted something out of date? Please <a href="../contact/index.html">contact us</a> &mdash; corrections are welcome and appreciated.</p>'''

CONTACT = f'''<h2 class="st">Get in touch</h2>
<p>Questions, corrections, or suggestions for a city or county page? Email us at <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>. We read every message and aim to reply within a few business days.</p>
<h2 class="st">Reporting a correction</h2>
<p>To help us fix things quickly, please include the page address (URL), what is wrong, and a link to an official source if you have one.</p>
<h2 class="st">Need government help?</h2>
<p>Oregon Information is an independent website and cannot process applications or access government records. For official help:</p>
<ul style="padding-left:20px">
<li><a href="https://www.oregon.gov/" target="_blank" rel="noopener">Oregon.gov</a> &mdash; state agencies</li>
<li><a href="https://www.oregon.gov/odot/dmv/" target="_blank" rel="noopener">Oregon DMV</a></li>
<li><a href="https://one.oregon.gov/" target="_blank" rel="noopener">ONE Oregon</a> &mdash; Oregon Health Plan, SNAP and cash assistance</li>
<li><a href="https://www.211info.org/" target="_blank" rel="noopener">211info</a> &mdash; dial 2-1-1 for local resources</li>
</ul>'''

PRIVACY = f'''<p><em>Last updated: {date.today().strftime("%B %-d, %Y")}</em></p>
<h2 class="st">Summary</h2>
<p>Oregon Information is a read-only informational website. We do not require accounts, we do not sell personal information, and we do not run advertising trackers.</p>
<h2 class="st">Information collected automatically</h2>
<p>Like nearly all websites, our hosting provider and content-delivery/security service (Cloudflare) automatically record standard technical data when you visit &mdash; such as your IP address, browser type, the page requested, and the date and time. This data is used to deliver the site, keep it secure, and understand overall traffic. Cloudflare may set strictly necessary security cookies.</p>
<h2 class="st">Information you send us</h2>
<p>If you email us, we receive your email address and whatever you include in your message. We use it only to reply and to improve the site, and we do not share it.</p>
<h2 class="st">Analytics</h2>
<p>If we add a privacy-respecting analytics tool in the future (for example, Google Analytics), it will be used only to measure aggregate traffic, and this policy will be updated to say so.</p>
<h2 class="st">Third-party links and images</h2>
<p>Pages link to government agencies and other external websites, and some photos are loaded from Wikimedia Commons. Those sites have their own privacy policies, which we do not control.</p>
<h2 class="st">Children</h2>
<p>This site is intended for a general audience and does not knowingly collect information from children under 13.</p>
<h2 class="st">Changes and contact</h2>
<p>We may update this policy; the date above shows the latest revision. Questions? Email <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>'''


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: f.write(content)


def main():
    cities = json.load(open('data/cities.json', encoding='utf-8'))
    counties = json.load(open('data/counties.json', encoding='utf-8'))
    custom = json.load(open('custom_city_content.json', encoding='utf-8')) if os.path.exists('custom_city_content.json') else {}
    for c in cities: c['counties'] = [x.strip() for x in c['county'].split(',')]
    for k in counties: COUNTY_SITES[k['name']] = k.get('website', '')
    for c in cities:
        write(f'{OUT}/cities/{slug(c["name"])}/index.html', city_page(c, cities, custom))
    for k in counties:
        write(f'{OUT}/counties/{slug(k["name"])}/index.html', county_page(k, cities))
    write(f'{OUT}/cities/index.html', cities_index(cities))
    write(f'{OUT}/about/index.html', simple_page('/about/', 'About Oregon Information', 'About Oregon Information: an independent, free guide to every Oregon city and county, with moving and visiting guides.', 'About Oregon Information', 'An independent, plain-language guide to the State of Oregon.', ABOUT))
    write(f'{OUT}/contact/index.html', simple_page('/contact/', 'Contact Oregon Information', 'Contact Oregon Information with questions, corrections, or suggestions.', 'Contact Us', 'Questions, corrections and suggestions are always welcome.', CONTACT))
    write(f'{OUT}/privacy/index.html', simple_page('/privacy/', 'Privacy Policy | Oregon Information', 'Privacy policy for oregoninformation.com.', 'Privacy Policy', 'How oregoninformation.com handles information.', PRIVACY))
    urls = ['/', '/cities/', '/counties/', '/moving-to-oregon/', '/visit-oregon/', '/about/', '/contact/', '/privacy/']
    urls += [f'/counties/{slug(k["name"])}/' for k in counties] + [f'/cities/{slug(c["name"])}/' for c in cities]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += '\n'.join(f'  <url><loc>{BASE_URL}{u}</loc><lastmod>{TODAY}</lastmod></url>' for u in urls) + '\n</urlset>\n'
    write(f'{OUT}/sitemap.xml', sm)
    write(f'{OUT}/robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n')
    print(f'Built {len(cities)} city pages, {len(counties)} county pages, cities index, about/contact/privacy, sitemap ({len(urls)} URLs).')


if __name__ == '__main__':
    main()
