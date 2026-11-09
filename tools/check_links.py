#!/usr/bin/env python3
"""Site-wide link checker for the built site (run from the repo root after building).

Checks every .html page for internal links that are broken or malformed:
  - '//path' links (browsers treat them as a different website)  -> problem
  - links to pages/files that don't exist in the repo              -> problem
  - relative links ('../', 'cities/...') or '.../index.html' links -> warning (they work, but
    aren't the canonical address; the generators should emit '/path/')
  - in-page '#anchor' links with no matching id                    -> problem

Usage: python3 tools/check_links.py        (last line: "Problems: N"; exit code 1 if N > 0)
"""
import os, re, sys
from html import unescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {'.git', 'data', 'docs', 'tools', '.github', 'node_modules', '__pycache__'}
URL_ATTR = re.compile(r'\b(href|src)="([^"]*)"')
SCHEME = re.compile(r'^[a-z][a-z0-9+.-]*:', re.I)


def pages():
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.endswith('.html'):
                yield os.path.join(d, f)


def resolve(page, url):
    """Repo file a site URL points at, or None if it doesn't exist."""
    path = url.split('#')[0].split('?')[0]
    if not path:
        return page
    if not path.startswith('/'):
        path = os.path.normpath(os.path.join('/' + os.path.relpath(os.path.dirname(page), ROOT), path))
    f = os.path.join(ROOT, unescape(path).lstrip('/'))
    if path.endswith('/') or os.path.isdir(f):
        f = os.path.join(f, 'index.html')
    return f if os.path.exists(f) else None


def main():
    problems, warnings = [], []
    n = 0
    for page in pages():
        n += 1
        rel = os.path.relpath(page, ROOT)
        html = open(page, encoding='utf-8', errors='replace').read()
        body = re.sub(r'<script\b.*?</script>', '', html, flags=re.S)
        ids = set(re.findall(r'\bid="([^"]+)"', html))
        for attr, url in URL_ATTR.findall(body):
            if not url or url.startswith(('mailto:', 'tel:', 'javascript:', 'data:')) or SCHEME.match(url):
                continue
            if url.startswith('//'):
                problems.append(f'{rel}: {attr}="{url}" starts with // (points at another website)')
                continue
            if url.startswith('#'):
                if url[1:] and url[1:] not in ids:
                    problems.append(f'{rel}: {attr}="{url}" has no element with that id')
                continue
            if not url.startswith('/'):
                warnings.append(f'{rel}: relative link {url}')
            elif re.search(r'/index\.html(?:[#?]|$)', url):
                warnings.append(f'{rel}: link to {url} (use the /path/ address)')
            target = resolve(page, url)
            if target is None:
                problems.append(f'{rel}: {attr}="{url}" points at a page or file that does not exist')
            elif '#' in url and url.split('#', 1)[1] and target.endswith('.html'):
                frag = url.split('#', 1)[1]
                if f'id="{frag}"' not in open(target, encoding='utf-8', errors='replace').read():
                    problems.append(f'{rel}: {attr}="{url}" - that page has no element with id "{frag}"')
    for w in sorted(set(warnings))[:40]:
        print('warning:', w)
    if len(set(warnings)) > 40:
        print(f'warning: ... and {len(set(warnings)) - 40} more')
    for p in problems:
        print('PROBLEM:', p)
    print(f'Checked {n} pages. Warnings: {len(set(warnings))}')
    print(f'Problems: {len(problems)}')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
