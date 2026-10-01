#!/usr/bin/env python3
"""Oregon Information - city page generator (FINAL). Reads oregon_cities.csv, builds site."""

import csv, json, os
from datetime import date

CITIES_CSV   = 'oregon_cities.csv'
CUSTOM_JSON  = 'custom_city_content.json'
ANALYTICS_ID = ''
BASE_URL     = 'https://mattriedl.github.io/oregon-information'
OUT          = 'site'

COUNTY_INFO = {
 'Multnomah':('Portland Metro','Portland General Electric'),'Washington':('Portland Metro','Portland General Electric'),
 'Clackamas':('Portland Metro','Portland General Electric'),'Columbia':('Northwest Oregon','Portland General Electric'),
 'Clatsop':('North Coast','Portland General Electric'),'Tillamook':('North Coast','Pacific Power'),
 'Yamhill':('Willamette Valley','Portland General Electric'),'Marion':('Willamette Valley','Portland General Electric'),
 'Polk':('Willamette Valley','Portland Power'),'Linn':('Willamette Valley','Pacific Power'),
 'Benton':('Willamette Valley','Pacific Power'),'Lane':('Willamette Valley','EWEB / Pacific Power'),
 'Lincoln':('Central Coast','Central Lincoln PUD'),'Douglas':('Southwest Oregon','Douglas Electric Cooperative'),
 'Coos':('South Coast','Coos-Curry Electric Cooperative'),'Curry':('South Coast','Coos-Curry Electric Cooperative'),
 'Josephine':('Rogue Valley','Pacific Power'),'Jackson':('Rogue Valley','Pacific Power'),
 'Klamath':('South Central Oregon','Pacific Power'),'Lake':('South Central Oregon','Harney Electric Cooperative'),
 'Deschutes':('Central Oregon','Pacific Power'),'Jefferson':('Central Oregon','Pacific Power'),
 'Crook':('Central Oregon','Pacific Power'),'Hood River':('Columbia River Gorge','Pacific Power'),
 'Wasco':('Columbia River Gorge','Northern Wasco PUD'),'Sherman':('North Central Oregon','Wasco Electric Cooperative'),
 'Gilliam':('North Central Oregon','Umatilla Electric Cooperative'),'Morrow':('North Central Oregon','Umatilla Electric Cooperative'),
 'Umatilla':('Eastern Oregon','Umatilla Electric Cooperative'),'Union':('Eastern Oregon','Pacific Power'),
 'Wallowa':('Northeast Oregon','Pacific Power'),'Baker':('Northeast Oregon','Oregon Trail Electric Cooperative'),
 'Grant':('Eastern Oregon','Oregon Trail Electric Cooperative'),'Harney':('Southeast Oregon','Harney Electric Cooperative'),
 'Malheur':('Southeast Oregon','Idaho Power'),
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

CSS = ":root{--gd:#14382a;--g:#1a5632;--gold:#c8a24b;--blue:#1f4e79;--bg:#f6f8f7;--tx:#22302b;--mu:#5c6b64}*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Inter',sans-serif;color:var(--tx);line-height:1.6;background:#fff}h1,h2,h3{font-family:Georgia,serif;line-height:1.25}.wrap{max-width:1000px;margin:0 auto;padding:0 24px}.hd{background:var(--gd);color:#fff;padding:14px 0;position:sticky;top:0;z-index:50}.hd nav{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}.logo{display:flex;align-items:center;gap:10px;font-weight:800;font-size:1.1rem;color:#fff;text-decoration:none}.badge{width:30px;height:30px;background:var(--gold);border-radius:50%;display:flex;align-items:center;justify-content:center}.nl{list-style:none;display:flex;gap:16px;flex-wrap:wrap}.nl a{color:#dbe7e0;text-decoration:none;font-weight:600;font-size:.9rem}.nl a:hover{color:var(--gold)}.hero{background:linear-gradient(160deg,var(--gd),var(--g));color:#fff;padding:52px 0 44px;margin-bottom:36px}.hero h1{font-size:clamp(1.6rem,4vw,2.4rem);max-width:760px}.hero p{color:#dceee3;margin-top:12px;max-width:640px}.crumbs{font-size:.88rem;color:var(--mu);padding:14px 0 0}.crumbs a{color:var(--blue);text-decoration:none}h2.st{font-size:1.45rem;color:var(--gd);margin:36px 0 16px;border-bottom:3px solid var(--g);padding-bottom:8px}.facts{background:var(--bg);border:1px solid #e3eae6;border-radius:10px;padding:20px;margin:24px 0}.facts table{width:100%;border-collapse:collapse}.facts th{text-align:left;padding:9px;color:var(--gd);border-bottom:2px solid var(--g);width:35%}.facts td{padding:9px;border-bottom:1px solid #e3eae6}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin:24px 0}.card{background:#fff;border:1px solid #e3eae6;border-top:4px solid var(--g);border-radius:10px;padding:20px}.card h3{font-size:1rem;color:var(--gd);margin-bottom:10px}.card ul{list-style:none}.card li{padding:6px 0;border-bottom:1px dashed #e3eae6;font-size:.92rem}.card a{color:var(--blue);text-decoration:none;font-weight:600}.faq details{background:#fff;border:1px solid #e3eae6;border-radius:8px;margin:9px 0;padding:0 16px}.faq summary{cursor:pointer;font-weight:600;padding:13px 0;color:var(--gd)}.faq p{padding:0 0 14px;font-size:.94rem}.back{margin-top:40px;padding-top:18px;border-top:1px solid #e3eae6}.back a{color:var(--g);font-weight:700;text-decoration:none}.ft{background:var(--gd);color:#cfe0d6;padding:30px 0;text-align:center;font-size:.84rem;margin-top:44px}.ft a{color:#cfe0d6;text-decoration:none}.dir-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin:22px 0}.dir-list a{background:var(--bg);border:1px solid #d7e2db;border-radius:6px;padding:10px 14px;text-decoration:none;color:var(--blue);font-weight:600;font-size:.9rem}.dir-list a:hover{background:var(--g);color:#fff}"

def slug(name):
    s = name.lower().replace('.', '').replace(' ', '-')
    while '--' in s: s = s.replace('--', '-')
    return s.strip('-')

def fmt_pop(p):
    p = (p or '').strip()
    if not p or p.upper() == 'NA': return ''
    try: return f'{int(float(p)):,}'
    except ValueError: return ''

def load_custom():
    if os.path.exists(CUSTOM_JSON):
        try:
            with open(CUSTOM_JSON, encoding='utf-8') as f: return json.load(f)
        except: return {}
    starter = {'portland': {'major_employers': 'Nike, Intel, Providence Health', 'nearest_hospital': 'Legacy Good Samaritan', 'transit': 'TriMet bus and MAX light rail'}}
    with open(CUSTOM_JSON, 'w', encoding='utf-8') as f: json.dump(starter, f, indent=2)
    return starter

def faq_for(city, county, region, electric):
    k = sum(ord(c) for c in city) % 3
    q = [
     (f"What is the cost of living in {city}, Oregon?", f"{city} lies in the {region} region, where costs vary mainly by housing. Oregon charges no statewide sales tax."),
     (f"What utilities do I set up when moving to {city}?", f"Electricity is generally provided by {electric}; natural gas, where available, by NW Natural. Water, sewer, and trash are handled by the City of {city}."),
     (f"How do I find a job near {city}?", "WorkSource Oregon offers free career coaching, and iMatchSkills is the state's largest job board."),
     (f"Which schools serve families in {city}?", f"Assignment depends on your exact address. Start with the Oregon Department of Education directory or the {county} County district office."),
     (f"How soon must I register my car after moving to {city}?", "Within 30 days of establishing residency — both the vehicle registration and an Oregon driver's license."),
     (f"Are there food banks or assistance programs near {city}?", f"Yes. Apply for SNAP at the ONE Oregon portal, find a pantry through Oregon Food Bank, or dial 211 for {county} County community resources."),
    ]
    if k == 1: q[0] = (f"Is {city}, Oregon affordable to live in?", q[0][1]); q[2] = (f"What is the job market like around {city}?", q[2][1])
    elif k == 2: q[1] = (f"How do I connect utilities in {city}?", q[1][1]); q[4] = (f"After moving to {city}, what's the DMV deadline?", q[4][1])
    return q

def city_page(city, county, pop, custom):
    region, electric = COUNTY_INFO.get(county, ('Oregon', 'Local utility district'))
    c = custom.get(city.lower().replace(' ', '_'), {})
    employers = c.get('major_employers', f'Employers in and around {city} and {county} County')
    pop_txt = fmt_pop(pop) or 'See PSU certified estimate'
    fq = faq_for(city, county, region, electric)
    faq_details = '\n'.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in fq)
    ld_city = json.dumps({'@context':'https://schema.org','@type':'City','name':city,'containedInPlace':{'@type':'State','name':'Oregon'}}, ensure_ascii=False)
    ld_bread = json.dumps({'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Home','item':f'{BASE_URL}/'},{'@type':'ListItem','position':2,'name':'Oregon Cities','item':f'{BASE_URL}/cities/'},{'@type':'ListItem','position':3,'name':city}]})
    ld_faq = json.dumps({'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in fq[:5]]}, ensure_ascii=False)
    ga = f'<script async src="https://www.googletagmanager.com/gtag/js?id={ANALYTICS_ID}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","{ANALYTICS_ID}");</script>' if ANALYTICS_ID else ''
    sl = '\n'.join(f'<li><a href="{u}" target="_blank" rel="noopener">{t}</a></li>' for t,u in STATE_LINKS)
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{city}, Oregon | Population, Facts, Moving Guide &amp; Local Links</title><meta name="description" content="Guide to {city}, Oregon ({county} County): population, moving and utility checklist, jobs, schools, healthcare, DMV steps, and assistance programs."><meta name="robots" content="index, follow"><meta name="viewport" content="width=device-width, initial-scale=1.0"><link rel="canonical" href="{BASE_URL}/cities/{slug(city)}/"><meta property="og:type" content="article"><meta property="og:title" content="{city}, Oregon — City Guide"><script type="application/ld+json">{ld_city}</script><script type="application/ld+json">{ld_bread}</script><script type="application/ld+json">{ld_faq}</script>{ga}<style>{CSS}</style></head><body><header class="hd"><div class="wrap"><nav><a class="logo" href="../../index.html"><span class="badge">&#127795;</span> Oregon Information</a><ul class="nl"><li><a href="../../moving-to-oregon/index.html">Moving</a></li><li><a href="../../visit-oregon/index.html">Visiting</a></li><li><a href="../../counties/index.html">Counties</a></li><li><a href="../index.html">Cities A&ndash;Z</a></li></ul></nav></div></header><div class="hero"><div class="wrap"><h1>{city}, Oregon</h1><p>Located in {county} County in the {region} region — local facts, a newcomer checklist, and government links in one place.</p></div></div><main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="../../index.html">Home</a> &rsaquo;<a href="../index.html">Oregon Cities</a> &rsaquo; {city}</nav><h2 class="st">Quick Facts</h2><section class="facts"><table><tr><th>County</th><td>{county} County, Oregon</td></tr><tr><th>Region</th><td>{region}</td></tr><tr><th>Population</th><td>{pop_txt}</td></tr><tr><th>Status</th><td>Incorporated city</td></tr></table></section><h2 class="st">Moving to {city}</h2><div class="cards"><div class="card"><h3>&#9889; Utilities Checklist</h3><ul><li><strong>Electricity:</strong> {electric}</li><li><strong>Natural gas:</strong> NW Natural (where available)</li><li><strong>Water &amp; sewer:</strong> City of {city} / {county} County</li><li><strong>Trash:</strong> Assigned hauler &mdash; verify by service address</li><li><strong>Internet:</strong> Comcast, CenturyLink/Lumen, local ISPs</li></ul></div><div class="card"><h3>&#128188; Jobs &amp; Economy</h3><ul><li><strong>Notable employers:</strong> {employers}</li><li><a href="https://www.worksourceoregon.org/" target="_blank" rel="noopener">WorkSource Oregon (free)</a></li><li><a href="https://www.imatchskills.org/" target="_blank" rel="noopener">iMatchSkills job board</a></li></ul></div><div class="card"><h3>&#127968; Housing</h3><ul><li><a href="https://www.zillow.com/or/" target="_blank" rel="noopener">Zillow Oregon</a></li><li><a href="https://www.apartments.com/oregon/" target="_blank" rel="noopener">Apartments.com</a></li><li><a href="https://www.oregon.gov/ohcs/" target="_blank" rel="noopener">OHCS buyer/renter programs</a></li></ul></div><div class="card"><h3>&#128663; DMV Steps</h3><ul><li>Vehicle registration &amp; Oregon license within <strong>30 days</strong></li><li><a href="https://www.oregon.gov/odot/dmv/pages/new_residents.aspx" target="_blank" rel="noopener">New resident guide</a></li><li><a href="https://www.oregon.gov/odot/dmv/pages/find_us.aspx" target="_blank" rel="noopener">Find a DMV office</a></li></ul></div><div class="card"><h3>&#127891; Schools</h3><ul><li>Districts vary by address &mdash; verify before renting/buying</li><li><a href="https://www.oregon.gov/ode/pages/default.aspx" target="_blank" rel="noopener">Oregon Dept. of Education</a></li><li>Contact the {county} County district office</li></ul></div><div class="card"><h3>&#127973; Healthcare &amp; Assistance</h3><ul><li><a href="https://one.oregon.gov/" target="_blank" rel="noopener">ONE portal (OHP/SNAP)</a></li><li><a href="https://www.oregonfoodbank.org/" target="_blank" rel="noopener">Oregon Food Bank</a></li><li><a href="https://www.211info.org/" target="_blank" rel="noopener">Dial 211 for local help</a></li></ul></div></div><h2 class="st">Frequently Asked Questions</h2><section class="faq">{faq_details}</section><h2 class="st">Official State Links</h2><section class="faq"><ul>{sl}</ul></section><p class="back"><a href="../index.html">&larr; All Oregon Cities</a></p></div></main><footer class="ft"><p>&copy; 2026 Oregon Information &mdash; independent resource, not affiliated with the State of Oregon.<br>Population data: PSU Population Research Center estimates.</p></footer></body></html>'''

def cities_index(cities):
    links = sorted(cities, key=lambda x: x[0].lower())
    items = '\n'.join(f'<a href="{slug(n)}/index.html">{n}</a>' for n, _, _ in links)
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Oregon Cities A&ndash;Z | Complete Directory</title><meta name="description" content="Directory of every incorporated city in Oregon with county, population, moving guides, and official links."><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>{CSS}</style></head><body><header class="hd"><div class="wrap"><nav><a class="logo" href="../../index.html"><span class="badge">&#127795;</span> Oregon Information</a><ul class="nl"><li><a href="../../moving-to-oregon/index.html">Moving</a></li><li><a href="../../visit-oregon/index.html">Visiting</a></li><li><a href="../../counties/index.html">Counties</a></li></ul></nav></div></header><main><div class="wrap"><div class="hero" style="margin-bottom:20px"><h1>Oregon Cities A&ndash;Z</h1><p>Browse every incorporated city in Oregon ({len(cities)} total).</p></div><nav class="dir-list">{items}</nav></div></main><footer class="ft"><p>&copy; 2026 Oregon Information</p></footer></body></html>'''

def main():
    print('=' * 60); print('Oregon Information Website Generator'); print('=' * 60)
    custom = load_custom()
    with open(CITIES_CSV, encoding='utf-8') as f: rows = list(csv.DictReader(f))
    cities, seen, skipped = [], set(), 0
    for r in rows:
        name = (r.get('city_name') or '').strip(); county = (r.get('county') or '').strip()
        if not name or not county or name.lower() in seen: skipped += 1; continue
        seen.add(name.lower()); cities.append((name, county, r.get('population')))
    print(f'Loaded {len(cities)} valid cities ({skipped} skipped)')
    os.makedirs(f'{OUT}/cities', exist_ok=True)
    for name, county, pop in cities:
        d = f'{OUT}/cities/{slug(name)}'; os.makedirs(d, exist_ok=True)
        with open(f'{d}/index.html', 'w', encoding='utf-8') as f: f.write(city_page(name, county, pop, custom))
        print(f'  built {name}')
    with open(f'{OUT}/cities/index.html', 'w', encoding='utf-8') as f: f.write(cities_index(cities))
    urls = [f'{BASE_URL}/'] + [f'{BASE_URL}/cities/{slug(n)}/' for n, _, _ in cities]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += '\n'.join(f'  <url><loc>{u}</loc></url>' for u in urls) + '\n</urlset>\n'
    with open(f'{OUT}/sitemap.xml', 'w', encoding='utf-8') as f: f.write(sm)
    with open(f'{OUT}/robots.txt', 'w', encoding='utf-8') as f: f.write(f'User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n')
    print('=' * 60); print(f'DONE: {len(cities)} city pages + index + sitemap.xml + robots.txt in "{OUT}/"')

if __name__ == '__main__': main()
