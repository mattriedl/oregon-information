#!/usr/bin/env python3
"""Oregon Information - statewide blog builder.

Reads data/blog_articles.json and writes:
  blog/index.html               article cards, newest first
  blog/{slug}/index.html        one page per article whose body exists in data/blog_content/{slug}.html
                                (articles without a body source are left untouched, so hand-written
                                 article files are never overwritten)
  sitemap.xml                   adds /blog/ URLs (idempotent; safe to run after generate_city_pages.py)

Head, CSS, header, footer, ticker and alert bar are imported from generate_city_pages.py so the
blog is styled identically to every other generated page.

Adding an article: append an object to data/blog_articles.json
  {"slug", "title", "description" (150-160 chars), "date" (YYYY-MM-DD), "dateModified" (optional),
   "category", "keywords": [...], "excerpt" (optional, card text), "hero_sub" (optional),
   "cta": "moving" | "visiting"}
then save the article body (HTML fragment, starting at the first <p>/<h2>) as
data/blog_content/{slug}.html and run:  python3 build_blog_index.py
"""

import json, os, re
from datetime import date

from generate_city_pages import (BASE_URL, SITE_NAME, DEFAULT_IMG, head, header, footer,
                                 ticker_html, alert_banner, ld, e, oregon_silhouette)

ROOT = os.path.dirname(os.path.abspath(__file__))
ARTICLES_JSON = os.path.join(ROOT, 'data', 'blog_articles.json')
CONTENT_DIR = os.path.join(ROOT, 'data', 'blog_content')
BLOG_DIR = os.path.join(ROOT, 'blog')
PUBLISHER = {'@type': 'Organization', 'name': SITE_NAME, 'url': f'{BASE_URL}/',
             'logo': {'@type': 'ImageObject', 'url': f'{BASE_URL}/assets/favicon-32.png'}}

CTAS = {
    'moving': ('Planning your move to Oregon?',
               'Our free Moving to Oregon guide walks you through DMV deadlines, utilities, voter registration, schools and choosing the right city &mdash; step by step.',
               'moving-to-oregon/index.html', 'Read the Moving to Oregon guide &rarr;', 'cities/index.html', 'Browse all 241 cities'),
    'visiting': ('Ready to see Oregon for yourself?',
                 'Our Visit Oregon guide covers the coast, Crater Lake, the Gorge, wine country and road-trip routes &mdash; with links to every official source.',
                 'visit-oregon/index.html', 'Plan your Oregon visit &rarr;', 'regions/index.html', 'Explore the 7 regions'),
}


def load_articles():
    with open(ARTICLES_JSON, encoding='utf-8') as f:
        arts = json.load(f)
    return sorted(arts, key=lambda a: (a.get('date', ''), a.get('slug', '')), reverse=True)


def nice_date(iso):
    return date.fromisoformat(iso).strftime('%B %-d, %Y')


def word_count(body):
    return len(re.sub(r'<[^>]+>', ' ', body).split())


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def card(a, up):
    return (f'<a class="card post-card" href="{up}{a["slug"]}/index.html"><span class="pc-cat">{e(a.get("category", "Oregon"))}</span>'
            f'<h3>{e(a["title"])}</h3><p>{e(a.get("excerpt") or a["description"])}</p>'
            f'<span class="pc-date"><time datetime="{a["date"]}">{nice_date(a["date"])}</time></span><span class="pc-more">Read article &rarr;</span></a>')


def auto_image(a, body):
    """If an article has no photo, use the first gallery photo of the first city page it links to."""
    if a.get('image'):
        return
    try:
        imgs = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'city_images.json')))
    except Exception:
        return
    by_slug = {re.sub(r'[^a-z0-9]+', '-', k.lower()).strip('-'): v for k, v in imgs.items()}
    for sl in re.findall(r'cities/([a-z0-9-]+)/', body):
        for v in by_slug.get(sl, []):
            if v.get('src', '').lower().split('?')[0].endswith(('.jpg', '.jpeg', '.png')):
                a.update(image=v['src'], image_page=v.get('page', ''), image_alt=(v.get('caption') or a['title'])[:120],
                         image_credit=f"{(v.get('artist') or 'Wikimedia Commons')[:60]} / {v.get('license', '')}")
                return


def article_page(a, body, all_arts):
    auto_image(a, body)
    up = '../../'
    path = f'/blog/{a["slug"]}/'
    url = f'{BASE_URL}{path}'
    modified = a.get('dateModified') or a['date']
    words = word_count(body)
    minutes = max(1, round(words / 230))
    img = a.get('image') or DEFAULT_IMG
    art_ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': a['title'], 'description': a['description'],
              'datePublished': a['date'], 'dateModified': modified, 'image': img, 'wordCount': words,
              'articleSection': a.get('category', ''), 'keywords': ', '.join(a.get('keywords', [])), 'inLanguage': 'en-US',
              'author': {'@type': 'Organization', 'name': f'{SITE_NAME} Editorial Team', 'url': f'{BASE_URL}/about/'},
              'publisher': PUBLISHER, 'mainEntityOfPage': {'@type': 'WebPage', '@id': url}}
    bread = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{BASE_URL}/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Blog', 'item': f'{BASE_URL}/blog/'},
        {'@type': 'ListItem', 'position': 3, 'name': a['title'], 'item': url}]}
    extra = (ld(art_ld) + ld(bread) + f'<meta property="article:published_time" content="{a["date"]}">'
             f'<meta property="article:modified_time" content="{modified}"><meta property="article:section" content="{e(a.get("category", ""))}">')
    h, p, href, btn, href2, btn2 = CTAS.get(a.get('cta', 'moving'), CTAS['moving'])
    cta = (f'<aside class="cta-box"><h2>{h}</h2><p>{p}</p><a class="btn-cta" href="{up}{href}">{btn}</a>'
           f'<a class="btn-ghost" href="{up}{href2}">{btn2}</a></aside>')
    related = [x for x in all_arts if x['slug'] != a['slug']][:3]
    rel_html = (f'<h2 class="st">More from the Oregon Information Blog</h2><div class="cards">{"".join(card(x, "../") for x in related)}</div>'
                if related else '')
    title_tag = a.get('seo_title') or f'{a["title"]} | {SITE_NAME}'
    fig = ''
    if a.get('image'):
        credit = (f'<small>Photo: <a href="{e(a["image_page"])}" target="_blank" rel="noopener">{e(a.get("image_credit", "Wikimedia Commons"))}</a></small>'
                  if a.get('image_page') else '')
        fig = (f'<figure class="post-hero"><img src="{e(a["image"])}" alt="{e(a.get("image_alt") or a["title"])}" width="960" height="540" '
               f'fetchpriority="high" style="width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;border-radius:10px">'
               f'<figcaption style="font-size:.8rem;color:#5b6b64;margin-top:4px">{credit}</figcaption></figure>')
    return (head(title_tag, a['description'], path, 'article', img, extra, up, ', '.join(a.get('keywords', [])))
            + header(up) + ticker_html() + alert_banner()
            + f'<div class="hero region-hero">{oregon_silhouette()}<div class="wrap"><p class="or-eyebrow">{e(a.get("category", "Oregon"))}</p>'
            + f'<h1>{e(a.get("h1") or a["title"])}</h1>' + (f'<p>{e(a["hero_sub"])}</p>' if a.get('hero_sub') else '')
            + f'<div class="post-meta"><span class="pill">&#128197; <time datetime="{a["date"]}">{nice_date(a["date"])}</time></span>'
            + (f'<span class="pill">Updated <time datetime="{modified}">{nice_date(modified)}</time></span>' if modified != a['date'] else '')
            + f'<span class="pill">&#9201; {minutes} min read</span></div></div></div>'
            + f'<main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="{up}index.html">Home</a> &rsaquo; '
            + f'<a href="../index.html">Blog</a> &rsaquo; {e(a["title"])}</nav>'
            + f'<article class="post prose">{fig}{body}{cta}</article>{rel_html}'
            + '<p class="back"><a href="../index.html">&larr; All blog articles</a></p></div></main>'
            + footer(up, '<br>Information is provided for general guidance; confirm details with the official agency.'))


def index_page(arts):
    up = '../'
    path = '/blog/'
    title = 'Oregon Information Blog | Moving, Living & Visiting Oregon'
    desc = ('Practical, well-researched guides to moving to Oregon, the best places to live, cost of living, '
            'small towns and visiting the Beaver State.')
    kw = 'Oregon blog, moving to Oregon, living in Oregon, best places to live in Oregon, Oregon cost of living, visiting Oregon'
    items = [{'@type': 'ListItem', 'position': i + 1, 'url': f'{BASE_URL}/blog/{a["slug"]}/', 'name': a['title']} for i, a in enumerate(arts)]
    blog_ld = {'@context': 'https://schema.org', '@type': 'Blog', 'name': f'{SITE_NAME} Blog', 'url': f'{BASE_URL}{path}',
               'description': desc, 'publisher': PUBLISHER,
               'blogPost': [{'@type': 'BlogPosting', 'headline': a['title'], 'url': f'{BASE_URL}/blog/{a["slug"]}/',
                             'datePublished': a['date'], 'dateModified': a.get('dateModified') or a['date']} for a in arts]}
    list_ld = {'@context': 'https://schema.org', '@type': 'ItemList', 'itemListElement': items}
    bread = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{BASE_URL}/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Blog', 'item': f'{BASE_URL}{path}'}]}
    cats = sorted({a.get('category', 'Oregon') for a in arts})
    cards = ''.join(card(a, '') for a in arts) or '<p>New articles are on the way &mdash; check back soon.</p>'
    return (head(title, desc, path, 'website', None, ld(blog_ld) + ld(list_ld) + ld(bread), up, kw)
            + header(up) + ticker_html() + alert_banner()
            + f'<div class="hero region-hero">{oregon_silhouette()}<div class="wrap"><p class="or-eyebrow">The Oregon Information Blog</p>'
            + '<h1>Moving, Living &amp; Visiting Oregon</h1>'
            + '<p>In-depth, plain-language guides for newcomers, house-hunters and travelers &mdash; built on Census data, official state sources and local knowledge.</p>'
            + f'<div class="pills"><span class="pill">&#128240; {len(arts)} article{"s" if len(arts) != 1 else ""}</span>'
            + ''.join(f'<span class="pill">{e(c)}</span>' for c in cats) + '</div></div></div>'
            + f'<main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="{up}index.html">Home</a> &rsaquo; Blog</nav>'
            + f'<h2 class="st">Latest Articles</h2><div class="cards">{cards}</div>'
            + '<h2 class="st">Keep Exploring Oregon</h2><nav class="dir-list">'
            + f'<a href="{up}moving-to-oregon/index.html">Moving to Oregon<small>Step-by-step relocation guide</small></a>'
            + f'<a href="{up}visit-oregon/index.html">Visit Oregon<small>Trip planning &amp; top sights</small></a>'
            + f'<a href="{up}regions/index.html">Oregon&rsquo;s 7 Regions<small>Coast to high desert</small></a>'
            + f'<a href="{up}cities/index.html">Cities A&ndash;Z<small>All 241 incorporated cities</small></a>'
            + f'<a href="{up}counties/index.html">Counties<small>All 36 Oregon counties</small></a></nav>'
            + '</div></main>' + footer(up))


def update_sitemap(arts):
    sm_path = os.path.join(ROOT, 'sitemap.xml')
    if not os.path.exists(sm_path):
        return 0
    with open(sm_path, encoding='utf-8') as f:
        sm = f.read()
    sm = re.sub(r'\s*<url><loc>' + re.escape(BASE_URL) + r'/blog/[^<]*</loc>.*?</url>', '', sm)   # drop stale blog URLs
    entries = [('/blog/', max((a.get('dateModified') or a['date']) for a in arts) if arts else date.today().isoformat())]
    entries += [(f'/blog/{a["slug"]}/', a.get('dateModified') or a['date']) for a in arts]
    block = ''.join(f'\n  <url><loc>{BASE_URL}{u}</loc><lastmod>{d}</lastmod></url>' for u, d in entries)
    sm = sm.replace('\n</urlset>', block + '\n</urlset>')
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(sm)
    return len(entries)


def main():
    arts = load_articles()
    built = []
    for a in arts:
        src = os.path.join(CONTENT_DIR, f'{a["slug"]}.html')
        if os.path.exists(src):
            with open(src, encoding='utf-8') as f:
                body = f.read().strip()
            write(os.path.join(BLOG_DIR, a['slug'], 'index.html'), article_page(a, body, arts))
            built.append(f'{a["slug"]} ({word_count(body)} words)')
        elif not os.path.exists(os.path.join(BLOG_DIR, a['slug'], 'index.html')):
            print(f'WARNING: no body source or page for "{a["slug"]}"')
    write(os.path.join(BLOG_DIR, 'index.html'), index_page(arts))
    n = update_sitemap(arts)
    print(f'Blog index: {len(arts)} articles. Article pages built: {", ".join(built) or "none"}. Sitemap blog URLs: {n}.')


if __name__ == '__main__':
    main()
