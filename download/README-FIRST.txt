آموزشگاه آنک — static website build
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
