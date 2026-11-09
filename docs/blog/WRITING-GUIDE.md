# Oregon Information blog: writing and publishing guide

This is the rulebook for every new article on https://oregoninformation.com/blog/.
The scheduled blog task follows it end to end. A human writer should too.

The site is an independent guide to Oregon for people **moving to, living in and visiting** the state.
Articles must be accurate, specific, genuinely useful and written for people, not search engines.
Google's helpful-content and E-E-A-T standards are the bar: answer the search better than page one does.

---

## 1. Choose the topic and keywords (OpenSEO + web search)

Use the OpenSEO tools (project `de4ec873-04de-43ec-94df-f65fe1429c97`, market US/English).
Budget: about 150-400 OpenSEO credits per article. Never start a batch over 2,000 credits.

1. **Read `docs/blog/topics.md`** (backlog + published list) and the `keywords` of every article in
   `data/blog_articles.json`. Never reuse another article's primary keyword or search intent.
2. **Check what is timely.** Today's date decides. Seasonal topics must publish **2-6 weeks before** the
   season peaks (holiday lights by mid-November, whale watching by mid-December, tax/kicker in January,
   wildflowers and tulips in March, camping and road trips in May). Use web search for news and events
   happening in Oregon now (new attractions, festivals, laws, closures, records) and for "2026"/"2027" searches.
3. **Pick a candidate** from the top of the backlog (or a better timely idea), then confirm it with OpenSEO:
   - `research_keywords` on 1-3 seeds (the default 150 results is enough). Filter for Oregon-related rows.
   - `get_keyword_metrics` on the shortlist (primary + 10-30 long-tail candidates).
   - `get_search_console_performance` filtered to the topic (queries containing a key word, last 3 months):
     queries the site already gets impressions for are the best long tails to include.
   - `get_serp_results` for the primary keyword (depth 10). Read who ranks, what they cover and the
     "People also ask"-style questions. Plan to beat them: more complete, more current, more specific.
4. **Pick ONE primary keyword**: real demand (ideally 500+/month, or a cluster that adds up), keyword
   difficulty preferably under 30, and a page one that has blogs, forums or thin pages we can outdo.
   Avoid head terms dominated by official sites (e.g. "crater lake") unless you target a long tail
   ("crater lake in winter").
5. **Pick 4-9 secondary keywords**: long-tail variations and questions (who/what/when/where/how/is/can/best/cost).
   They become H2/H3 headings and FAQ questions.
6. Record the choice in `docs/blog/topics.md` (move the row from Backlog to Published when you publish), and
   append a one-line summary to OpenSEO with `update_project_context` → `appendResearchLog`
   (topic, primary keyword, volume/KD, credits used).

## 2. Research the facts

- Use web search and WebFetch to read **primary sources**: oregon.gov agencies (ODOT/TripCheck, Oregon State
  Parks, Department of Revenue, OHA, ODFW), NPS, USFS, BLM, NOAA/NWS, city and county sites, Travel Oregon,
  Travel Portland, official event and business websites.
- Write down exact figures, dates, prices, hours, addresses and URLs as you go.
- **Never invent** statistics, quotes, prices, events, reviews, personal experiences or "our team visited".
  If a fact can't be verified, leave it out or say plainly what to check.
- Events and prices change yearly: give the current year's dates only when an official source publishes them;
  otherwise say "typically late November; check the official site for this year's dates".
- Do not use photos of real people as the subject; never include private individuals' details.

## 3. Write the article

Files:
- Body: `data/blog_content/<slug>.html` (an HTML fragment, no `<html>`/`<head>`/`<h1>`).
- Metadata: append an object to `data/blog_articles.json` (keep the file's 2-space indent):

```json
{
  "slug": "best-hot-springs-in-oregon",
  "title": "Best Hot Springs in Oregon: 15 Natural Soaks & Resorts",
  "seo_title": "Best Hot Springs in Oregon: 15 Soaks, Map & Tips",
  "h1": "Best Hot Springs in Oregon: Natural Pools, Resorts & Tips",
  "description": "140-160 characters: primary keyword early, the concrete benefit, and a reason to click.",
  "excerpt": "1-2 sentences for article cards.",
  "hero_sub": "1-2 sentences under the H1.",
  "date": "YYYY-MM-DD (today, America/Los_Angeles)",
  "dateModified": "same as date",
  "category": "Visiting Oregon | Living in Oregon | Moving to Oregon",
  "cta": "visiting | moving",
  "keywords": ["primary keyword", "secondary 1", "secondary 2", "..."],
  "image": "https://upload.wikimedia.org/... or thumb.wikimedia.org/... (960px)",
  "image_page": "https://commons.wikimedia.org/wiki/File:...",
  "image_credit": "Author / License",
  "image_alt": "Specific description of what the photo shows"
}
```

Rules:
- **Slug**: the primary keyword, short, lowercase, hyphens (no dates or years).
- **seo_title** (≤ 60 chars, the `<title>`): primary keyword first, then a benefit/number/year if it fits.
  Add the year only for genuinely time-bound topics (events, taxes, "2026").
- **description**: 140-160 characters, primary keyword in the first half, written to earn the click.
- **Length**: 1,800-3,000 words for guides and lists, 1,500+ minimum. Depth over padding.
- **Structure** (copy the pattern of `data/blog_content/oregon-coast-storm-watching.html`):
  1. `<p class="lede">`: answer the search in the first 2-3 sentences; primary keyword in the first 100 words, in bold once.
  2. `<div class="callout">` "Quick answer" box: 4-6 bullet facts (great for featured snippets and AI answers).
  3. `<nav class="toc" aria-label="Table of contents">` linking to every `<h2 id="...">`.
  4. A hero-adjacent `<figure class="photo">` photo.
  5. 6-12 `<h2 id="...">` sections, in the order a reader needs them; `<h3>` for each place/item in a list.
     Phrase several headings as the questions people search ("When is whale watching season in Oregon?")
     and answer each in the first sentence below it, bolded (snippet-ready).
  6. At least one comparison `<table class="tbl">` (place, best for, season, cost, distance...).
  7. For places, a `<div class="visit-card">` with address, hours/season, fees and official website where known.
  8. `<h2 id="faq">` then `<div class="faq">` with 4-8 `<details><summary>Question?</summary><p>Answer</p></details>`
     (the build turns these into FAQPage schema). Use real "People also ask" questions.
  9. A short closing paragraph with next steps and internal links, then a `<p class="src">` note on checking current conditions.
- **Internal links (6+ distinct)**: link city names to `/cities/<slug>/` on first mention, plus relevant
  `/counties/`, `/regions/`, `/visit-oregon/`, `/moving-to-oregon/`, `/oregon-zip-codes/` and **at least one
  related `/blog/<slug>/` article**. Use descriptive anchor text, root-relative URLs, trailing slash.
- **External links (3+, 2+ official)**: cite sources inline where the fact appears, `target="_blank" rel="noopener"`.
- **Photos (hero + at least 2 in the body)**: Wikimedia Commons only, freely licensed. Open each file page with
  WebFetch to confirm author and license. Use the 960px thumbnail URL, `width`/`height`, `loading="lazy"`,
  `decoding="async"`, descriptive `alt`, and a visible credit:
  `<figcaption>Caption. <small>Photo: <a href="https://commons.wikimedia.org/wiki/File:..." target="_blank" rel="noopener">Author / License</a> via Wikimedia Commons</small></figcaption>`.
  `data/city_images.json` already lists verified photos for every city (src, page, artist, license, caption).
- **Voice**: plain, friendly, confident US English. Short paragraphs, specific details (miles, prices, months,
  trail lengths), no hype, no filler ("nestled", "bustling", "delve", "in conclusion"). Write for someone deciding
  something; tell them what to do.
- **Safety and honesty**: include safety notes for outdoor topics (weather, tides, road conditions, permits).
  Never give medical, legal or tax advice beyond summarizing official rules, and link the official source.

## 4. Build and check (all must pass)

```bash
python3 generate_city_pages.py && python3 build_blog_index.py   # builds pages, city backlinks, sitemap, home/guide blocks
python3 tools/blog_seo_check.py <slug>                           # must end with "Problems: 0"
python3 tools/blog_seo_check.py --all | tail -1                  # no new problems in other articles
```

Then view it like a reader:
- `python3 -m http.server 8765` in the repo root (background), and load `http://localhost:8765/blog/<slug>/`
  with Playwright at 390px and 1440px wide: no sideways scrolling, photos load, TOC links jump, FAQ opens.
- Re-read the whole article once as an editor against your notes: every number, date, price and name.
- `git status` should show only: the new content file, `data/blog_articles.json`, `docs/blog/topics.md`,
  rebuilt `blog/` pages, `index.html`, `moving-to-oregon/index.html` or `visit-oregon/index.html` blocks,
  city pages that gained a link to the new article, `sitemap.xml` and `data/lastmod.json`.

## 5. Publish

- Commit everything from the build with the message `Blog: <title>`, a blank line, then:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: <this session's URL>
  ```
  Use `git -c user.name="Matt Riedl" -c user.email="mattriedl@hotmail.com"`. Push to `main`
  (pushing deploys the live site; it takes about 5-15 minutes).
- Poll `https://oregoninformation.com/blog/<slug>/` (add `?v=N` to bypass caches) until it returns 200 with the new title.
- Notify search engines: OpenSEO `submit_indexnow_urls` with the article URL, `/blog/`, and the city pages it links to.
- Never push an article that fails the checks. If you can't finish, leave it unpushed and report why.
