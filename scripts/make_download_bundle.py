# -*- coding: utf-8 -*-
"""
Package dist/ for desktop download.

Produces  download/anek-site.zip  containing:

  site/           the production build, byte-identical to dist/ — upload this
  site-offline/   same pages rewritten to RELATIVE paths + .html files, so the
                  pages can be opened by double-clicking, with no server
  START-*.{command,bat,sh}   one-click local web server launchers
  README-FIRST.txt

Why two copies: the production build uses 247 root-absolute links per page
(/music/piano/, /assets/css/...) and directory-style URLs. Those are correct for
a real web root and WRONG for file:// — the browser resolves "/assets/..." to the
root of your hard disk. Rewriting them is a viewing convenience only; never
upload site-offline/ to the real domain.
"""
import os
import re
import shutil
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
OUT_DIR = os.path.join(ROOT, "download")
STAGE = "/tmp/anek_bundle"

# assets that keep their exact name at the site root
ROOT_FILES = {"favicon.svg", "favicon.ico", "site.webmanifest", "robots.txt",
              "sitemap.xml", "404.html"}


def page_targets():
    """map of root-absolute URL -> path of the real file inside the tree"""
    m = {}
    for dirpath, _dirnames, filenames in os.walk(DIST):
        for fn in filenames:
            abs_p = os.path.join(dirpath, fn)
            rel = os.path.relpath(abs_p, DIST).replace(os.sep, "/")
            if fn == "index.html":
                url = "/" + rel[: -len("index.html")]
                m[url] = rel
                if url != "/":
                    m[url.rstrip("/")] = rel          # tolerate a missing trailing slash
            else:
                m["/" + rel] = rel
    return m


def rewrite(html: str, depth: int, targets: dict) -> str:
    """turn every root-absolute attribute value into a ../-relative one"""
    up = "../" * depth or "./"

    def repl(match):
        attr, url = match.group(1), match.group(2)
        if url.startswith("//"):
            return match.group(0)
        frag = ""
        if "#" in url:
            url, frag = url.split("#", 1)
            frag = "#" + frag
        if not url:                                    # pure "#anchor"
            return f'{attr}="{frag}"'
        target = targets.get(url) or targets.get(url.rstrip("/") + "/")
        if target is None:
            base = url.lstrip("/")
            target = base if base in ROOT_FILES else base
        return f'{attr}="{up}{target}{frag}"'

    html = re.sub(r'\b(href|src)="(/[^"]*)"', repl, html)
    # file:// treats every document as an opaque origin, so a crossorigin font
    # request is rejected before it starts. Drop the attribute for this copy.
    html = html.replace(
        ' as="font" type="font/woff2" crossorigin>', ' as="font" type="font/woff2">')
    html = html.replace(
        "</head>",
        "  <!-- OFFLINE PREVIEW COPY: links rewritten to relative paths. "
        "Do not upload; upload the site/ folder instead. -->\n</head>")
    return html


def build_offline(src, dst, targets):
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)
    pages = 0
    for dirpath, _d, filenames in os.walk(dst):
        for fn in filenames:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(dirpath, fn)
            depth = len(os.path.relpath(p, dst).replace(os.sep, "/").split("/")) - 1
            with open(p, encoding="utf-8") as fh:
                html = fh.read()
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(rewrite(html, depth, targets))
            pages += 1
    return pages


README = """آموزشگاه آنک — static website build
===================================================================

WHAT IS IN THIS ZIP
-------------------
site/            The real production build (34 pages). THIS is what you upload.
site-offline/    The same pages with links rewritten so you can just
                 double-click them. For looking only - never upload it.
START-local-server.command   macOS  - double-click
START-local-server.bat       Windows - double-click
START-local-server.sh        Linux  - run in a terminal


HOW TO LOOK AT IT ON YOUR DESKTOP
---------------------------------
BEST WAY (shows the site exactly as visitors will see it):
  Double-click the START-local-server file for your system.
  It opens http://localhost:8000 in your browser.
  Requires Python, which macOS and Linux already have. On Windows,
  install it from python.org if the window closes instantly.

QUICK WAY (no server, good enough for a look):
  Open  site-offline/index.html  by double-clicking it.
  Caveat: Chrome refuses to load webfonts over file://, so Persian text
  falls back to Tahoma. Firefox shows the correct font. Layout, colours
  and all 34 pages work either way.


DO THE URLS NEED TO CHANGE BEFORE GOING LIVE?
---------------------------------------------
NO - if the site sits at the ROOT of a domain, e.g.
       https://aanak.ir/            -> upload the CONTENTS of site/
     into public_html / www / htdocs. Every link already matches,
     and the canonical tags already say https://aanak.ir/.
     Works as-is on cPanel, Netlify, Vercel, Cloudflare Pages,
     Liara, ArvanCloud, plain nginx/Apache.

YES - if the site sits in a SUBFOLDER, e.g.
       https://example.com/anek/
       https://username.github.io/anek/
     Every link starts with "/" so it would point at the domain root
     and 404. Ask for a rebuild with a base path - it is a one-line
     change in scripts/coder_phase2_build.py, not manual editing.

YES - if the domain is not aanak.ir. The <link rel="canonical">,
     og:url, sitemap.xml and the JSON-LD @id values all hardcode
     https://aanak.ir. Change DOMAIN in the build script and rebuild.


SERVER NOTES
------------
The URLs are directory-style (/music/piano/), so the server must serve
index.html for a directory. Apache, nginx, cPanel, Netlify and Vercel all
do this by default. Nothing else is required: no PHP, no database, no
Node, no build step. It is plain HTML, one CSS file, one JS file, one
font and 11 SVGs.

Upload order tip: copy assets/ first, then the HTML folders, so visitors
never hit a page whose stylesheet has not arrived yet.


STILL TO FINISH
---------------
The pages contain 182 [INTERNAL_DATA_NEEDED] markers. Those are the
facts nobody has supplied yet - 7 of 16 instructors have no name, and 13
courses have no instructor assigned. They are deliberate: the build never
invents a teacher, a price or a review. Search for the marker to find them.
See output/client_data_request.md for the full list of questions.
"""

SH = """#!/bin/sh
cd "$(dirname "$0")/site" || exit 1
echo "Serving the Anak website at http://localhost:8000"
echo "Press Ctrl+C to stop."
(sleep 1; (command -v xdg-open >/dev/null && xdg-open http://localhost:8000) \\
  || (command -v open >/dev/null && open http://localhost:8000)) >/dev/null 2>&1 &
python3 -m http.server 8000 2>/dev/null || python -m http.server 8000
"""

BAT = """@echo off
cd /d "%~dp0site"
echo Serving the Anak website at http://localhost:8000
echo Press Ctrl+C to stop.
start "" http://localhost:8000
python -m http.server 8000 || py -m http.server 8000
pause
"""


def main():
    targets = page_targets()
    shutil.rmtree(STAGE, ignore_errors=True)
    os.makedirs(STAGE)
    shutil.copytree(DIST, os.path.join(STAGE, "site"))
    pages = build_offline(DIST, os.path.join(STAGE, "site-offline"), targets)

    with open(os.path.join(STAGE, "README-FIRST.txt"), "w", encoding="utf-8") as fh:
        fh.write(README)
    for name, body in (("START-local-server.sh", SH),
                       ("START-local-server.command", SH),
                       ("START-local-server.bat", BAT)):
        p = os.path.join(STAGE, name)
        with open(p, "w", encoding="utf-8", newline="\r\n" if name.endswith(".bat") else "\n") as fh:
            fh.write(body)
        if not name.endswith(".bat"):
            os.chmod(p, 0o755)

    os.makedirs(OUT_DIR, exist_ok=True)
    zip_path = os.path.join(OUT_DIR, "anek-site.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dirpath, _d, filenames in os.walk(STAGE):
            for fn in sorted(filenames):
                p = os.path.join(dirpath, fn)
                arc = os.path.join("anek-site", os.path.relpath(p, STAGE))
                zi = zipfile.ZipInfo.from_file(p, arc)
                zi.compress_type = zipfile.ZIP_DEFLATED
                if fn.endswith((".sh", ".command")):
                    zi.external_attr = 0o755 << 16
                with open(p, "rb") as fh:
                    z.writestr(zi, fh.read())

    raw = sum(os.path.getsize(os.path.join(dp, f))
              for dp, _d, fs in os.walk(STAGE) for f in fs)
    print("=" * 66)
    print("DOWNLOAD BUNDLE READY")
    print("=" * 66)
    print(f"  {os.path.relpath(zip_path, ROOT)}")
    print(f"  pages rewritten for offline viewing : {pages}")
    print(f"  uncompressed                        : {raw:,} bytes")
    print(f"  zipped                              : {os.path.getsize(zip_path):,} bytes")


if __name__ == "__main__":
    main()
