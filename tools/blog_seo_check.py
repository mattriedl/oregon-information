#!/usr/bin/env python3
"""SEO + quality gate for Oregon Information blog articles.

Usage:
  python3 tools/blog_seo_check.py <slug>     check one article (source + metadata + built page)
  python3 tools/blog_seo_check.py --all      check every article (published ones get a lighter check)

Run AFTER building:  python3 generate_city_pages.py && python3 build_blog_index.py
The last line printed is "Problems: N". An article may only be published when N == 0.
Warnings are advice; fix them when you reasonably can.
"""
import html, json, os, re, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTS = os.path.join(ROOT, 'data', 'blog_articles.json')
CONTENT = os.path.join(ROOT, 'data', 'blog_content')
TRUSTED = ('.gov', '.us', '.edu', 'oregon.gov', 'nps.gov', 'fs.usda.gov', 'blm.gov', 'noaa.gov', 'weather.gov',
           'stateparks.oregon.gov', 'traveloregon.com', 'travelportland.com', 'census.gov', 'odot', 'tripcheck.com')


def text_of(h):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h))).strip()


def check(slug, strict=True):
    probs, warns = [], []
    P, W = probs.append, warns.append
    arts = json.load(open(ARTS, encoding='utf-8'))
    a = next((x for x in arts if x['slug'] == slug), None)
    if not a:
        return [f'{slug}: not in data/blog_articles.json'], []
    src = os.path.join(CONTENT, f'{slug}.html')
    if not os.path.exists(src):
        return [f'{slug}: missing data/blog_content/{slug}.html'], []
    body = open(src, encoding='utf-8').read()
    words = len(text_of(body).split())

    # ---- metadata
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug): P('slug must be lowercase words separated by hyphens')
    if len(slug) > 60: W(f'slug is long ({len(slug)} chars); keep URLs short')
    for k in ('title', 'description', 'date', 'category', 'cta', 'keywords', 'excerpt', 'hero_sub'):
        if not a.get(k): P(f'metadata: "{k}" is missing')
    st = a.get('seo_title') or f'{a.get("title", "")} | Oregon Information'
    if len(st) > 60: P(f'seo_title is {len(st)} chars (max 60): {st}')
    if len(st) < 35: W(f'seo_title is short ({len(st)} chars)')
    d = a.get('description', '')
    if not 140 <= len(d) <= 160: P(f'description is {len(d)} chars (must be 140-160)')
    kws = a.get('keywords') or []
    if not 4 <= len(kws) <= 10: P(f'keywords: need 4-10 (primary first), found {len(kws)}')
    primary = (kws[0] if kws else '').lower()
    if a.get('category') not in ('Moving to Oregon', 'Living in Oregon', 'Visiting Oregon'):
        P('category must be "Moving to Oregon", "Living in Oregon" or "Visiting Oregon"')
    if a.get('cta') not in ('moving', 'visiting'): P('cta must be "moving" or "visiting"')
    try:
        if date.fromisoformat(a['date']) > date.today(): P('date is in the future')
    except Exception:
        P('date must be YYYY-MM-DD')
    for other in arts:
        if other['slug'] != slug and other.get('keywords') and other['keywords'][0].lower() == primary:
            P(f'primary keyword "{primary}" is already the primary keyword of /blog/{other["slug"]}/')
    if not a.get('image'): P('metadata: "image" (hero photo) is missing')
    elif not a.get('image_page') or not a.get('image_credit'): P('hero image needs image_page and image_credit (author / license)')
    if a.get('image') and not a.get('image_alt'): P('hero image needs image_alt')

    # ---- keyword placement
    if primary:
        pk = re.escape(primary)
        if not re.search(pk, st.lower()) and not all(w in st.lower() for w in primary.split()[:3]):
            W('primary keyword (or its main words) should appear in seo_title')
        if primary.split()[0] not in d.lower(): W('primary keyword should appear in the description')
        first = ' '.join(text_of(body).split()[:120]).lower()
        if not re.search(pk, first): P('primary keyword must appear in the first 120 words')
        h2s = [text_of(h).lower() for h in re.findall(r'<h2[^>]*>(.*?)</h2>', body, re.S)]
        if not any(all(w in h for w in primary.split() if len(w) > 2) for h in h2s):
            W('primary keyword should appear in at least one <h2>')
        n = len(re.findall(pk, text_of(body).lower()))
        density = n * len(primary.split()) / max(words, 1) * 100
        if n < 3: W(f'primary keyword appears only {n} times')
        if density > 2.5: P(f'primary keyword density {density:.1f}% looks like keyword stuffing (keep under 2.5%)')

    # ---- structure
    if strict:
        if words < 1500: P(f'only {words} words (minimum 1,500)')
        if words > 4000: W(f'{words} words; consider tightening')
    if '<h1' in body: P('do not put an <h1> in the body (the template adds it)')
    if not body.lstrip().startswith('<p class="lede">'): P('body must start with <p class="lede">')
    if 'class="callout"' not in body: P('add a "Quick answer" <div class="callout"> near the top')
    h2 = re.findall(r'<h2 id="([^"]+)"', body)
    if len(re.findall(r'<h2', body)) < 6: P('need at least 6 <h2> sections')
    if len(re.findall(r'<h2(?! id=)', body)): P('every <h2> needs an id="" so the table of contents can link to it')
    toc = re.search(r'<nav class="toc".*?</nav>', body, re.S)
    if not toc: P('missing <nav class="toc"> table of contents')
    else:
        for anchor in re.findall(r'href="#([^"]+)"', toc.group(0)):
            if anchor not in h2: P(f'table of contents links to #{anchor}, which no <h2> has')
    lv = [int(x) for x in re.findall(r'<h([2-4])', body)]
    for x, y in zip([2] + lv, lv):
        if y > x + 1: P('heading levels skip (e.g. h2 -> h4)'); break
    if 'class="tbl"' not in body: W('add a comparison <table class="tbl"> when the topic allows')

    # ---- FAQ
    faq = re.search(r'<div class="faq"[^>]*>(.*?)</div>', body, re.S)
    qs = re.findall(r'<details>\s*<summary>(.*?)</summary>\s*<p>(.*?)</p>\s*</details>', faq.group(1) if faq else '', re.S)
    if not faq: P('missing <div class="faq"> section')
    elif not 4 <= len(qs) <= 8: P(f'FAQ needs 4-8 <details> questions, found {len(qs)}')
    for q, ans in qs:
        if not q.strip().endswith('?'): P(f'FAQ question should end with "?": {text_of(q)[:60]}')
        if len(text_of(ans).split()) < 15: W(f'FAQ answer is very short: {text_of(q)[:50]}')

    # ---- links
    links = re.findall(r'href="([^"]+)"', body)
    internal = [u for u in links if u.startswith('/') or u.startswith('../')]
    external = [u for u in links if u.startswith('http')]
    if len(set(internal)) < 6: P(f'need at least 6 distinct internal links (city/county/region/guide/blog pages), found {len(set(internal))}')
    if not any('/cities/' in u for u in internal): P('link at least one relevant /cities/ page')
    if not any('/blog/' in u for u in internal): W('link at least one related earlier blog article')
    for u in set(internal):
        p = u.split('#')[0]
        if p.startswith('../'): p = '/' + re.sub(r'^(\.\./)+', '', p)
        f = os.path.join(ROOT, p.lstrip('/'))
        if p.endswith('/'): f = os.path.join(f, 'index.html')
        if p and not os.path.exists(f): P(f'internal link {u} points to a page that does not exist')
    trusted = [u for u in external if any(t in u for t in TRUSTED)]
    if len(set(external)) < 3: P(f'cite at least 3 external sources, found {len(set(external))}')
    if len(set(trusted)) < 2: P('at least 2 external links must be official/authoritative sources (.gov, state parks, NPS, USFS, NOAA, Travel Oregon...)')
    for tag in re.findall(r'<a [^>]*href="http[^"]*"[^>]*>', body):
        if 'target="_blank"' not in tag or 'rel="noopener"' not in tag:
            W('external links should use target="_blank" rel="noopener"'); break
    if re.search(r'>\s*(click here|here|read more)\s*<', body, re.I): W('use descriptive anchor text instead of "click here"/"read more"')

    # ---- images
    figs = re.findall(r'<figure class="photo">(.*?)</figure>', body, re.S)
    if len(figs) < 2: P(f'need at least 2 in-article photos (<figure class="photo">), found {len(figs)}')
    for fg in figs:
        img = re.search(r'<img [^>]*>', fg)
        if not img: P('figure without <img>'); continue
        t = img.group(0)
        if not re.search(r'alt="[^"]{15,}"', t): P('every photo needs descriptive alt text (15+ characters)')
        if 'loading="lazy"' not in t: W('in-article photos should have loading="lazy"')
        if not re.search(r'width="\d+" height="\d+"', t): W('add width and height to images to prevent layout shift')
        if 'commons.wikimedia.org/wiki/File:' not in fg and 'Photo:' not in fg: P('every photo needs a visible credit linking to its source/license')

    # ---- honesty / quality
    for bad in ('as an ai', 'lorem ipsum', 'in conclusion', 'delve', 'tapestry', 'nestled', 'bustling', "in today's fast-paced"):
        if bad in text_of(body).lower(): W(f'avoid filler/cliche phrase: "{bad}"')
    if re.search(r'\bTODO\b|\[citation needed\]|XX+', body): P('remove TODO / placeholder text')

    # ---- built page
    page = os.path.join(ROOT, 'blog', slug, 'index.html')
    if not os.path.exists(page):
        P('built page blog/<slug>/index.html missing; run the build')
    else:
        h = open(page, encoding='utf-8').read()
        types = []
        for j in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
            try: types.append(json.loads(j).get('@type'))
            except Exception: P('built page has invalid JSON-LD')
        for t in ('Article', 'BreadcrumbList', 'FAQPage'):
            if t not in types: P(f'built page is missing {t} structured data')
        if f'<link rel="canonical" href="https://oregoninformation.com/blog/{slug}/">' not in h: P('canonical tag missing or wrong')
        if len(re.findall(r'<h1', h)) != 1: P('built page must have exactly one <h1>')
        if f'/blog/{slug}/' not in open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read(): P('article missing from sitemap.xml')
        if f'/blog/{slug}/' not in open(os.path.join(ROOT, 'blog', 'index.html'), encoding='utf-8').read(): P('article missing from /blog/ index')
    return probs, warns


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    arts = json.load(open(ARTS, encoding='utf-8'))
    slugs = [a['slug'] for a in arts] if sys.argv[1] == '--all' else [sys.argv[1]]
    total = 0
    for s in slugs:
        probs, warns = check(s, strict=sys.argv[1] != '--all')
        print(f'== {s}: {len(probs)} problem(s), {len(warns)} warning(s)')
        for p in probs: print('  PROBLEM:', p)
        for w in warns: print('  warning:', w)
        total += len(probs)
    print(f'Problems: {total}')
    sys.exit(1 if total else 0)


if __name__ == '__main__':
    main()
