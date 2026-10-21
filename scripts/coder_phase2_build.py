#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CODER / DESIGNER PHASE 2 — SIX-TRACK PRODUCTION HTML BUILD  (dist/)
CODER / DESIGNER PHASE 3 — dist/sitemap.xml + dist/robots.txt

Reads: output/page_content_plan.json, output/navigation_plan.json,
       output/schema_blueprint.json, output/page_map.json
Writes: dist/**/index.html (34 pages), dist/assets/img/*.svg, sitemap, robots
"""
import html
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_lib as L  # noqa: E402

DIST = os.path.join(L.ROOT, "dist")
IMG_DIR = os.path.join(DIST, "assets", "img")


def e(s) -> str:
    return html.escape(str(s), quote=True)


def attr(s) -> str:
    return html.escape(str(s), quote=True).replace("\n", " ")


# ----------------------------------------------------------------- SVG assets
def svg(title, sub, c1, c2, w=1200, h=675, fg="#FFFFFF"):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/></linearGradient></defs>
  <rect width="{w}" height="{h}" fill="url(#g)"/>
  <g fill="{fg}" font-family="Vazirmatn, Tahoma, sans-serif" text-anchor="middle">
    <text x="{w//2}" y="{h//2 - 10}" font-size="{int(h*0.072)}" font-weight="700">{html.escape(title)}</text>
    <text x="{w//2}" y="{h//2 + int(h*0.075)}" font-size="{int(h*0.042)}" opacity=".78">{html.escape(sub)}</text>
  </g>
</svg>
"""


IMAGES = {
    "hero-home.svg": ("آموزشگاه سینمایی و بازیگری آنک", "موسیقی • بازیگری • سینما • هنرهای تجسمی • کافه هنر", "#141B2D", "#33405E"),
    "hero-music.svg": ("دانشکده موسیقی آنک کرج", "پیانو • گیتار • ویولن • سنتور • آواز", "#141B2D", "#C89B3C"),
    "hero-performing.svg": ("بازیگری، فن بیان و گویندگی", "تئاتر • دوبله • مجری‌گری", "#1E2A45", "#B45309"),
    "hero-cinema.svg": ("سینما، عکاسی، تدوین و گریم", "آتلیه • لابراتوار تدوین • گریم سینمایی", "#141B2D", "#0F766E"),
    "hero-visual.svg": ("نقاشی و خوشنویسی", "طراحی • نستعلیق • خط تحریری", "#2A201B", "#C89B3C"),
    "hero-cafe.svg": ("کافه هنر و موسیقی زنده آنک", "پیانو • گیتار • سنتور • سه‌تار • ارگ", "#1C1613", "#2A201B"),
    "hero-fardis.svg": ("هنرجویان فردیس کرج", "۵ دقیقه پیاده از مترو کرج", "#0F766E", "#141B2D"),
    "hero-audition.svg": ("تست بازیگری در کرج", "مصاحبه • مونولوگ • تست دوربین", "#1E2A45", "#B45309"),
    "hero-instructors.svg": ("اساتید آموزشگاه آنک", "رزومه‌های تأییدشده", "#141B2D", "#33405E"),
    "hero-contact.svg": ("آدرس و تماس آموزشگاه آنک", "کرج، شاه عباسی، دانشکده جنوبی", "#141B2D", "#0F766E"),
    "campus-map.svg": ("نقشه دسترسی پردیس مرکزی کرج", "کتابخانه امیرکبیر • مترو کرج • چهارراه طالقانی", "#F3EFEA", "#E3DCD2"),
}
PORTRAIT = ("portrait-placeholder.svg", "تصویر استاد", "در انتظار دریافت از آموزشگاه", "#E3DCD2", "#F3EFEA")

DEPT_HERO = {"DEPT_MUSIC": "hero-music.svg", "DEPT_PERFORMING": "hero-performing.svg",
             "DEPT_CINEMA": "hero-cinema.svg", "DEPT_VISUAL": "hero-visual.svg"}


def write_images():
    L.ensure_dirs(IMG_DIR)
    for name, (t, s, c1, c2) in IMAGES.items():
        fg = "#5B6273" if name == "campus-map.svg" else "#FFFFFF"
        L.write_text(os.path.join(IMG_DIR, name), svg(t, s, c1, c2, fg=fg))
    L.write_text(os.path.join(IMG_DIR, PORTRAIT[0]),
                 svg(PORTRAIT[1], PORTRAIT[2], PORTRAIT[3], PORTRAIT[4], 800, 1000, fg="#5B6273"))


# ================================================================= BUILDER
class Builder:
    def __init__(self):
        self.p = L.academy_profile()
        self.domain = self.p["domain"].rstrip("/")
        self.courses = L.load_course_index()
        self.instructors = L.load_instructors()
        self.plan = L.read_json(os.path.join(L.OUTPUT, "page_content_plan.json"))
        self.nav = L.read_json(os.path.join(L.OUTPUT, "navigation_plan.json"))
        self.schema = L.read_json(os.path.join(L.OUTPUT, "schema_blueprint.json"))
        self.page_map = L.read_json(os.path.join(L.OUTPUT, "page_map.json"))
        self.pm_by_slug = {p["url_slug"]: p for p in self.page_map["pages"]}
        self.by_slug = {p["url_slug"]: p for p in self.plan["pages"]}
        self.title_of = {p["url_slug"]: p["primary_keyword"] for p in self.page_map["pages"]}

    # ------------------------------------------------------------- chrome
    def header(self, slug):
        pills = []
        for pil in self.nav["desktop_mega_menu"]:
            active = ' aria-current="page"' if pil["href"] == slug else ""
            if pil["type"] == "highlighted_badge_link":
                pills.append(
                    f'<li class="nav__item"><a class="nav__link nav__link--cafe" href="{attr(pil["href"])}"{active}>'
                    f'<span aria-hidden="true">🎹</span> {e(pil["label_fa"])}</a></li>')
                continue
            panel = []
            if pil["type"] == "mega_dropdown_3_columns":
                cols = []
                for col in pil["columns"]:
                    links = "".join(
                        f'<li><a class="nav__sublink" href="{attr(i["href"])}">{e(i["label_fa"])}</a></li>'
                        for i in col["items"])
                    cols.append(f'<div><p class="nav__coltitle">{e(col["title_fa"])}</p>'
                                f'<ul class="nav__sublist">{links}</ul></div>')
                panel.append(f'<div class="nav__cols">{"".join(cols)}</div>')
                if pil.get("footer_cta"):
                    panel.append(f'<div class="nav__panelcta"><a class="btn btn--ghost btn--sm" '
                                 f'href="{attr(pil["footer_cta"]["href"])}">{e(pil["footer_cta"]["label_fa"])}</a></div>')
            else:
                links = "".join(f'<li><a class="nav__sublink" href="{attr(i["href"])}">{e(i["label_fa"])}</a></li>'
                                for i in pil.get("items", []))
                panel.append(f'<ul class="nav__sublist">{links}</ul>')
                if pil.get("cta_pill"):
                    panel.append(f'<div class="nav__panelcta"><a class="btn btn--accent btn--sm" '
                                 f'href="{attr(pil["cta_pill"]["href"])}">{e(pil["cta_pill"]["label_fa"])}</a></div>')
            mega = " nav__panel--mega" if pil["type"] == "mega_dropdown_3_columns" else ""
            pid = pil["pillar_id"].lower()
            pills.append(
                f'<li class="nav__item nav__item--has-panel" data-open="false">'
                f'<a class="nav__link" href="{attr(pil["href"])}" aria-expanded="false" aria-controls="{pid}-panel"{active}>'
                f'{e(pil["label_fa"])} <span class="nav__caret" aria-hidden="true">▾</span></a>'
                f'<div class="nav__panel{mega}" id="{pid}-panel">{"".join(panel)}</div></li>')
        return f"""<header class="site-header">
  <div class="wrap site-header__bar">
    <a class="brand" href="/">
      <span class="brand__mark" aria-hidden="true">آنک</span>
      <span class="brand__text"><span class="brand__name">{e(self.p['brand_fa'])}</span>
      <span class="brand__sub">موسیقی، بازیگری، سینما و کافه هنر در کرج</span></span>
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav"
            aria-label="باز کردن منوی اصلی"><span class="nav-toggle__bars"></span></button>
    <nav class="nav" id="primary-nav" aria-label="منوی اصلی" data-open="false">
      <ul class="nav__list">{''.join(pills)}</ul>
    </nav>
    <div class="header__actions">
      <a class="header__phone" href="tel:{attr(self.p['phone_e164'])}">{e(self.p['phone_display'])}</a>
      <button class="btn btn--primary btn--sm" type="button" data-dialog-open="#consult-dialog">رزرو تعیین سطح رایگان</button>
    </div>
  </div>
</header>"""

    def footer(self):
        f = self.nav["footer"]
        cols = []
        for col in f["columns"]:
            links = "".join(f'<li><a href="{attr(i["href"])}">{e(i["label_fa"])}</a></li>' for i in col["items"])
            cols.append(f'<div><h3>{e(col["title_fa"])}</h3><ul class="footer__list">{links}</ul></div>')
        nap = f["nap_block"]
        cols.append(f"""<div>
      <h3>پردیس مرکزی کرج</h3>
      <p class="footer__nap">{e(nap['address_fa'])}<br>
      کد پستی: {e(nap['postal_code'])}<br>
      تلفن: <a href="tel:{attr(nap['phone_e164'])}">{e(nap['phone_display'])}</a><br>
      {e(nap['opening_hours'])}<br>
      <a href="{attr(nap['whatsapp'])}" rel="noopener">واتساپ آموزشگاه</a> ·
      <a href="{attr(nap['instagram'])}" rel="noopener">اینستاگرام</a><br>
      <a href="{attr(self.p['maps_url'])}" rel="noopener">گوگل‌مپ</a> ·
      <a href="{attr(self.p['neshan_url'])}" rel="noopener">نشان</a> ·
      <a href="{attr(self.p['balad_url'])}" rel="noopener">بلد</a></p>
      <p class="footer__nap"><strong>{e(nap['license_fa'])}</strong></p>
    </div>""")
        return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="footer__grid">{''.join(cols)}</div>
    <div class="footer__bottom">
      <span>{e(f['copyright_fa'])}</span>
      <span>{e(f['service_area_fa'])}</span>
    </div>
  </div>
</footer>"""

    def mobile_bar(self, slug):
        if slug.startswith("/art-cafe") or slug.startswith("/music"):
            lbl, href, icon = "رزرو میز کافه", "/art-cafe/#reservation", "🎹"
        elif slug.startswith("/performing-arts") or slug.startswith("/acting-audition"):
            lbl, href, icon = "ثبت‌نام تست بازیگری", "/acting-audition/#booking", "🎭"
        else:
            lbl, href, icon = "استعلام شهریه", "/contact/#tuition", "💬"
        return f"""<nav class="mobile-conversion-bar" aria-label="میانبرهای تماس و ثبت‌نام">
  <button class="mcb--primary" type="button" data-dialog-open="#consult-dialog">
    <span class="mcb__icon" aria-hidden="true">📅</span><span class="mcb__label">مشاوره و تعیین سطح</span></button>
  <a href="tel:{attr(self.p['phone_e164'])}"><span class="mcb__icon" aria-hidden="true">📞</span><span class="mcb__label">تماس فوری</span></a>
  <a href="{attr(self.p['whatsapp_url'])}" rel="noopener"><span class="mcb__icon" aria-hidden="true">💬</span><span class="mcb__label">واتساپ</span></a>
  <a data-mcb-context data-default-label="استعلام شهریه" data-default-href="/contact/#tuition" href="{attr(href)}">
    <span class="mcb__icon" aria-hidden="true">{icon}</span><span class="mcb__label">{e(lbl)}</span></a>
</nav>"""

    def dialogs(self):
        return f"""<dialog class="modal" id="consult-dialog" aria-labelledby="consult-title">
  <div class="modal__head"><h2 id="consult-title" style="margin:0;font-size:1.1rem">رزرو مشاوره و تعیین سطح رایگان</h2>
    <button class="modal__close" type="button" data-dialog-close aria-label="بستن">×</button></div>
  <div class="modal__body">
    <p>برای رزرو جلسه مشاوره و تعیین سطح رایگان، با ما تماس بگیرید یا در واتساپ پیام بدهید.
       ساعات پاسخ‌گویی: {e(self.p['opening_hours'])}</p>
    <a class="btn btn--primary btn--block" href="tel:{attr(self.p['phone_e164'])}">تماس با {e(self.p['phone_display'])}</a>
    <a class="btn btn--accent btn--block" href="{attr(self.p['whatsapp_url'])}" rel="noopener">ارسال پیام واتساپ</a>
    <p style="font-size:.85rem;color:#5B6273;margin:0">آدرس: {e(self.p['address_fa'])}</p>
  </div>
</dialog>"""

    # ------------------------------------------------------- section parts
    def img(self, src, alt, w, h, eager=False, cls=""):
        load = 'loading="eager" fetchpriority="high" decoding="async"' if eager \
            else 'loading="lazy" decoding="async"'
        c = f' class="{cls}"' if cls else ""
        return f'<img{c} src="/assets/img/{src}" alt="{attr(alt)}" width="{w}" height="{h}" {load}>'

    def hero_img_for(self, entry):
        t, pid = entry["tier"], entry["page_id"]
        if t == "0":
            return "hero-home.svg"
        if t == "1":
            return DEPT_HERO[entry["department_id"]]
        if t == "2":
            return DEPT_HERO[self.courses[entry["course_id"]]["department_id"]]
        if t == "3":
            return "hero-cafe.svg"
        return {"GEO_FARDIS_HUB": "hero-fardis.svg", "CONV_AUDITION_HUB": "hero-audition.svg",
                "HUB_INSTRUCTORS": "hero-instructors.svg"}.get(pid, "hero-contact.svg")

    def breadcrumb_html(self, entry):
        slug = entry["url_slug"]
        trail = [("خانه", "/")]
        if entry["tier"] == "2":
            c = self.courses[entry["course_id"]]
            d = L.DEPARTMENTS[c["department_id"]]
            trail.append((d["name_fa"], d["slug"]))
            trail.append((c["name_fa"], slug))
        elif slug != "/":
            trail.append((entry["sections"][0]["heading_fa"][:48], slug))
        items = []
        for i, (name, href) in enumerate(trail):
            last = i == len(trail) - 1
            inner = e(name) if last else f'<a href="{attr(href)}">{e(name)}</a>'
            items.append(f"<li>{inner}</li>")
        return f'<nav class="breadcrumb" aria-label="مسیر صفحه"><ol>{"".join(items)}</ol></nav>'

    def paras(self, s):
        return "".join(f"<p>{e(p)}</p>" for p in s.get("paragraphs", []) if p)

    def gap_box(self, s):
        if not s.get("data_gap"):
            return ""
        note = s.get("note") or ("این بخش در انتظار دریافت داده رسمی از آموزشگاه است؛ هیچ اطلاعاتی ساخته نشده است.")
        return (f'<p class="data-gap"><strong>[INTERNAL_DATA_NEEDED]</strong> — {e(note)}</p>')

    def cta(self, s, style="btn--primary"):
        label = s.get("g7_cta")
        if not label or label == "—":
            return ""
        if "واتساپ" in label:
            return f'<p><a class="btn {style}" href="{attr(self.p["whatsapp_url"])}" rel="noopener">{e(label)}</a></p>'
        if "تماس" in label:
            return f'<p><a class="btn {style}" href="tel:{attr(self.p["phone_e164"])}">{e(label)}</a></p>'
        return f'<p><button class="btn {style}" type="button" data-dialog-open="#consult-dialog">{e(label)}</button></p>'

    def instructor_cards_html(self, cards, lazy=True):
        if not cards:
            return ('<p class="data-gap"><strong>[INTERNAL_DATA_NEEDED]</strong> — '
                    'هنوز هیچ استاد تأییدشده‌ای برای این دوره در فهرست رسمی آموزشگاه ثبت نشده است. '
                    'نام و رزومه استاد بلافاصله پس از تأیید منتشر می‌شود.</p>')
        out = []
        for c in cards:
            pending = c["is_placeholder"]
            name = "[INTERNAL_DATA_NEEDED]" if pending else c["name_fa"]
            alt = (f"جای‌گاه تصویر {c['role_title_fa']} — در انتظار دریافت عکس از آموزشگاه"
                   if pending else f"{c['name_fa']} — {c['role_title_fa']} در آموزشگاه آنک کرج")
            badges = [f'<span class="badge {"badge--female" if c["gender"] == "female" else "badge--teal"}">'
                      f'{e(c["gender_badge_fa"])}</span>']
            badges.append('<span class="badge badge--pending">در انتظار تأیید</span>' if pending
                          else '<span class="badge badge--teal">رزومه تأییدشده</span>')
            creds = "" if pending else f'<p class="instructor-card__creds">{e(c["credentials_fa"])}</p>'
            exp = "" if pending or not c.get("experience_highlights_fa") else \
                f'<p class="instructor-card__creds">{e(c["experience_highlights_fa"])}</p>'
            link = "" if pending or not c.get("same_as_url") else \
                f'<p class="instructor-card__creds"><a href="{attr(c["same_as_url"])}" rel="noopener nofollow">صفحه رسمی استاد</a></p>'
            sample = ('<p class="instructor-card__sample">نمونه اجرای صوتی/تصویری — '
                      '<strong>[INTERNAL_DATA_NEEDED]</strong></p>')
            out.append(f"""<article class="instructor-card{' instructor-card--pending' if pending else ''}"
         data-filter-card data-gender="{attr(c['gender'])}" data-courses="{attr(' '.join(c.get('course_ids', [])))}">
  <div class="instructor-card__media">{self.img(PORTRAIT[0], alt, 800, 1000, eager=False)}</div>
  <div class="instructor-card__body">
    <h3 class="instructor-card__name">{e(name)}</h3>
    <p class="instructor-card__role">{e(c['role_title_fa'])}</p>
    <ul class="instructor-card__tags">{''.join(f'<li>{b}</li>' for b in badges)}</ul>
    {creds}{exp}{link}{sample}
  </div>
</article>""")
        return f'<div class="instructor-roster-grid">{"".join(out)}</div>'

    def table_html(self, rows, cls, caption="", stacked=True):
        if not rows:
            return ""
        keys = [k for k in rows[0].keys() if not k.endswith("_raw") and k != "slug"]
        heads = {"format_fa": "نوع کلاس", "sessions": "تعداد جلسات", "duration_fa": "مدت هر جلسه",
                 "tuition_toman_fa": "شهریه هر ترم (تومان)", "certificate_fa": "مدرک پایان دوره",
                 "note_fa": "توضیح", "course_fa": "دوره", "private_toman_fa": "خصوصی (تومان)",
                 "group_toman_fa": "گروهی (تومان)"}
        th = "".join(f"<th scope=\"col\">{e(heads.get(k, k))}</th>" for k in keys)
        trs = []
        for r in rows:
            tds = []
            for k in keys:
                v = r.get(k, "—") or "—"
                if k in ("course_fa",) and r.get("slug"):
                    v = f'<a href="{attr(r["slug"])}">{e(v)}</a>'
                else:
                    v = e(v)
                tds.append(f'<td data-label="{attr(heads.get(k, k))}">{v}</td>')
            trs.append(f"<tr>{''.join(tds)}</tr>")
        cap = f"<caption>{e(caption)}</caption>" if caption else ""
        sc = " stacked-table" if stacked else ""
        return (f'<div class="{cls}"><table class="{sc.strip()}">{cap}'
                f"<thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div>")

    def nap_html(self, s):
        n = s["nap"]
        lm = "".join(f"<li>{e(x)}</li>" for x in s.get("landmarks", []))
        return f"""<div class="campus-map-and-nap-card">
  <div>
    <ul class="nap-list">
      <li><b>آدرس پردیس مرکزی</b><span>{e(n['address'])}</span></li>
      <li><b>تلفن</b><span><a href="tel:{attr(n['phone_e164'])}">{e(n['phone'])}</a></span></li>
      <li><b>واتساپ</b><span><a href="{attr(self.p['whatsapp_url'])}" rel="noopener">{e(self.p['mobile_whatsapp'])}</a></span></li>
      <li><b>ساعات کاری</b><span>{e(n['hours'])}</span></li>
      <li><b>کد پستی</b><span>{e(self.p['postal_code'])}</span></li>
    </ul>
    <div class="map-links">
      <a class="btn btn--ghost btn--sm" href="{attr(n['maps'])}" rel="noopener">گوگل‌مپ</a>
      <a class="btn btn--ghost btn--sm" href="{attr(n['neshan'])}" rel="noopener">نشان</a>
      <a class="btn btn--ghost btn--sm" href="{attr(n['balad'])}" rel="noopener">بلد</a>
      <a class="btn btn--ghost btn--sm" href="{attr(n['waze'])}" rel="noopener">ویز</a>
    </div>
  </div>
  <div>
    {self.img('campus-map.svg', 'نقشه دسترسی به آموزشگاه آنک در کرج، نزدیک کتابخانه امیرکبیر و مترو کرج', 1200, 675)}
    <h3 style="margin-block-start:var(--space-md);font-size:1rem">نقاط شاخص نزدیک</h3>
    <ul class="landmark-list">{lm}</ul>
  </div>
</div>"""

    def faq_html(self, items):
        out = []
        for f in items:
            out.append(f'<details><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>')
        return f'<div class="faq-accordion-rtl">{"".join(out)}</div>'

    # --------------------------------------------------- section dispatcher
    def render_section(self, entry, s, idx):
        ui = s["ui_component"]
        anchor = s["anchor"]
        tag = "header" if idx == 0 else "section"
        htag = "h1" if idx == 0 else "h2"
        alt_cls = " section--alt" if idx % 2 == 0 and idx > 0 else ""
        body = []

        if idx == 0:
            return self.render_hero(entry, s)

        # ---------- component bodies
        if ui == "instructor_roster_cards":
            body.append(self.paras(s))
            body.append(self.gap_box(s))
            body.append(self.instructor_cards_html(s.get("instructor_cards", [])))
        elif ui == "female_instructor_spotlight":
            inner = self.instructor_cards_html(s.get("instructor_cards", []))
            gap = self.gap_box(s) if s.get("data_gap") else ""
            body.append(f'<div class="female-instructor-spotlight"><div class="female-instructor-spotlight__head">'
                        f'<span class="badge badge--female">ویژه بانوان</span>'
                        f'<p style="margin:0">{e(s.get("g6_bluf", ""))}</p></div>'
                        f'{self.paras(s)}{gap}{inner}</div>')
        elif ui == "format_comparison_matrix":
            body.append(self.paras(s))
            body.append(self.table_html(s.get("matrix", []), "format-comparison-matrix",
                                        "مقایسه فرمت‌های کلاس بر اساس تعرفه رسمی آموزشگاه"))
        elif ui == "sub_specialty_tabs":
            tabs = s.get("tabs", [])
            tl, panels = [], []
            for i, t in enumerate(tabs):
                tid = f"{anchor}-tab-{i}"
                pid = f"{anchor}-panel-{i}"
                tl.append(f'<li><button class="sub-specialty-tabs__tab" id="{tid}" role="tab" type="button" '
                          f'aria-selected="{"true" if i == 0 else "false"}" aria-controls="{pid}" '
                          f'tabindex="{"0" if i == 0 else "-1"}">{e(t["title_fa"])}</button></li>')
                kw = ("<p>" + e("، ".join(t["keywords"])) + "</p>") if t.get("keywords") else ""
                panels.append(f'<div class="sub-specialty-tabs__panel" id="{pid}" role="tabpanel" '
                              f'aria-labelledby="{tid}"{"" if i == 0 else " hidden"}>'
                              f'<h3>{e(t["title_fa"])}</h3><p>{e(t["body_fa"])}</p>{kw}</div>')
            body.append(f'<div class="sub-specialty-tabs"><ul class="sub-specialty-tabs__list" role="tablist" '
                        f'aria-label="سبک‌ها و زیرتخصص‌ها">{"".join(tl)}</ul>{"".join(panels)}</div>')
        elif ui == "tuition_transparent_table":
            rows = s.get("table", [])
            cards = ""
            if rows and "tuition_toman_fa" in rows[0]:
                cs = []
                for i, r in enumerate(rows):
                    feat = " tuition-card--featured" if i == 0 else ""
                    cs.append(f'<div class="tuition-card{feat}"><span class="tuition-card__format">'
                              f'{e(r["format_fa"])}</span><span class="tuition-card__price">'
                              f'{e(r["tuition_toman_fa"])} تومان</span>'
                              f'<span class="tuition-card__meta">{e(r["sessions"])} جلسه · {e(r["duration_fa"])}</span>'
                              f'<span class="tuition-card__meta">{e(r["certificate_fa"])}</span></div>')
                cards = f'<div class="tuition-cards">{"".join(cs)}</div>'
            body.append(f'<div class="tuition-transparent-table">{self.paras(s)}{cards}'
                        f'{self.table_html(rows, "", "همه ارقام مستقیماً از تعرفه رسمی ثبت‌شده آموزشگاه (ریال ÷ ۱۰ = تومان)")}'
                        f'<p class="tuition-note">هیچ هزینه پنهانی وجود ندارد؛ موارد جانبی مانند کتاب و آزمون '
                        f'در جلسه مشاوره شفاف اعلام می‌شود.</p></div>')
        elif ui == "syllabus_term_timeline":
            steps = []
            for st in s.get("steps", []):
                mods = "".join(f'<li class="specialty-pill">{e(m)}</li>' for m in st.get("modules_fa", []))
                mods_html = '<ul class="syllabus-step__modules">' + mods + '</ul>' if mods else ''
                steps.append(f'<li class="syllabus-step"><p class="syllabus-step__level">{e(st["level_fa"])}</p>'
                             f'<p class="syllabus-step__term">{e(st["term_fa"])}</p><p>{e(st["description_fa"])}</p>'
                             f'{mods_html}</li>')
            body.append(f'<ol class="syllabus-term-timeline">{"".join(steps)}</ol>')
        elif ui == "kids_pedagogy_cards":
            body.append(self.paras(s))
            cards = [("گروه سنی و تعیین سطح", s.get("g6_bluf", "")),
                     ("روش آموزش کودک‌محور", "بازی، تکرار کوتاه، تشویق مرحله‌ای و تمرین خانگی سبک."),
                     ("حضور والدین", "امکان حضور والدین در جلسه اول برای آشنایی با فضا و استاد.")]
            body.append('<div class="kids-pedagogy-cards">' + "".join(
                f'<div class="kids-card"><h3>{e(t)}</h3><p>{e(d)}</p></div>' for t, d in cards if d) + "</div>")
            if s.get("links"):
                body.append('<ul class="related-links">' + "".join(
                    f'<li><a href="{attr(x)}">{e(self.title_of.get(x, x))}</a></li>' for x in s["links"]) + "</ul>")
        elif ui in ("art_cafe_stage_banner", "cafe_recital_cards"):
            evs = s.get("events", [])
            cards = "".join(
                f'<div class="cafe-night-card"><p class="cafe-night-card__title">{e(ev["title_fa"])}</p>'
                f'<div class="cafe-night-card__meta"><span><b>روزها:</b> {e(ev["days_of_week_fa"])}</span>'
                f'<span><b>ساعت:</b> {e(ev["time_range_fa"])}</span>'
                f'<span><b>نوازنده:</b> {e(ev["performer_name_fa"])}</span>'
                f'<span><b>رزرو میز:</b> {"الزامی" if ev["reservation_required"] == "true" else "اختیاری"}</span></div>'
                f'<p><a class="btn btn--ghost btn--sm" href="{attr(ev["linked_course_slug"])}">'
                f'یادگیری این ساز</a></p></div>' for ev in evs)
            link = s.get("link", "/art-cafe/")
            extra = "".join(f'<li><a href="{attr(x)}">{e(self.title_of.get(x, x))}</a></li>' for x in s.get("links", []))
            grid_html = '<div class="cafe-live-schedule-grid">' + cards + '</div>' if cards else ''
            extra_html = '<ul class="related-links">' + extra + '</ul>' if extra else ''
            body.append(f'<div class="art-cafe-stage-banner"><p>{e(s.get("g6_bluf", ""))}</p>'
                        f'{grid_html}'
                        f'<p style="margin-block-start:var(--space-lg)"><a class="btn btn--accent" href="{attr(link)}">'
                        f'{e(s.get("g7_cta", "مشاهده کافه هنر"))}</a></p>'
                        f'{extra_html}</div>')
        elif ui == "cafe_live_schedule_grid":
            evs = s.get("events", [])
            if evs:
                cards = "".join(
                    f'<div class="cafe-night-card"><p class="cafe-night-card__title">{e(ev["title_fa"])}</p>'
                    f'<div class="cafe-night-card__meta"><span><b>روزها:</b> {e(ev["days_of_week_fa"])}</span>'
                    f'<span><b>ساعت:</b> {e(ev["time_range_fa"])}</span>'
                    f'<span><b>نوازنده:</b> {e(ev["performer_name_fa"])}</span>'
                    f'<span><b>رزرو میز:</b> {"الزامی" if ev["reservation_required"] == "true" else "اختیاری"}</span>'
                    f'</div></div>' for ev in evs)
                body.append(f'<div class="cafe-live-schedule-grid">{cards}</div>')
            else:
                body.append(self.gap_box({"data_gap": True, "note": "برنامه اجرای این ساز هنوز تأیید نشده است."}))
            if s.get("link"):
                body.append(f'<p><a class="btn btn--accent" href="{attr(s["link"])}">'
                            f'آموزش {e(s.get("instrument_fa", ""))} در آموزشگاه آنک</a></p>')
        elif ui == "menu_table_rtl":
            body.append(self.gap_box(s))
        elif ui in ("fardis_commuter_box", "fardis_commuter_route_matrix"):
            routes = "".join(f"<li>{e(r)}</li>" for r in s.get("routes", []))
            lm = "".join(f"<li>{e(x)}</li>" for x in s.get("landmarks", []))
            shifts = ('<ul class="shift-badges"><li class="badge">شیفت فشرده پنجشنبه</li>'
                      '<li class="badge">شیفت فشرده جمعه</li>'
                      '<li class="badge badge--teal">۵ دقیقه پیاده از مترو کرج</li></ul>')
            route_html = f'<ul class="route-matrix">{routes}</ul>' if routes else ""
            lm_html = f'<ul class="landmark-list">{lm}</ul>' if lm else ""
            link_html = (f'<p><a class="btn btn--primary" href="{attr(s["link"])}">'
                         f'مشاهده راهنمای کامل هنرجویان فردیس</a></p>') if s.get("link") else ""
            body.append(f'<div class="fardis-commuter-box">{self.paras(s)}'
                        f'<p>{e(s.get("g6_bluf", ""))}</p>'
                        f'{route_html}{lm_html}{shifts}{link_html}</div>')
        elif ui == "audition_step_cards":
            steps = s.get("steps", [])
            if steps:
                cs = "".join(f'<div class="audition-step-card"><div class="audition-step-card__n" aria-hidden="true">'
                             f'{L.to_persian_digits(i + 1)}</div><h3>{e(st["level_fa"])}</h3>'
                             f'<p>{e(st["description_fa"])}</p>'
                             f'<p class="tuition-note">{e(st["term_fa"])}</p></div>'
                             for i, st in enumerate(steps))
                body.append(f'<div class="audition-step-cards">{cs}</div>')
            else:
                body.append(f'<div class="bridge-callout"><p>{e(s.get("g6_bluf", ""))}</p>'
                            f'<a class="btn btn--accent" href="{attr(s.get("link", "/acting-audition/"))}">'
                            f'{e(s.get("g7_cta", "ثبت‌نام تست بازیگری"))}</a></div>')
        elif ui == "audition_booking_form":
            ch = s["channels"]
            body.append(f"""<div class="contact-channel-cards">
  <a class="channel-card" href="tel:{attr(ch['phone_e164'])}"><span class="channel-card__label">تماس تلفنی</span>
    <span class="channel-card__value">{e(ch['phone'])}</span></a>
  <a class="channel-card" href="{attr(ch['whatsapp'])}" rel="noopener"><span class="channel-card__label">واتساپ</span>
    <span class="channel-card__value">{e(ch['mobile'])}</span></a>
  <a class="channel-card" href="{attr(ch['instagram'])}" rel="noopener"><span class="channel-card__label">اینستاگرام</span>
    <span class="channel-card__value">دایرکت رزرو نوبت</span></a>
</div>""")
        elif ui == "campus_map_and_nap_card":
            body.append(self.paras(s))
            body.append(self.nap_html(s))
            if s.get("fardis_status"):
                body.append('<p class="tuition-note">آموزشگاه آنک یک پردیس مرکزی در کرج دارد و شعبه مستقل '
                            'فردیس ندارد؛ برای شفافیت هیچ آدرس خیابانی دیگری اعلام نمی‌شود.</p>')
        elif ui == "contact_channel_cards":
            ch = s["channels"]
            body.append(f"""<div class="contact-channel-cards">
  <a class="channel-card" href="tel:{attr(ch['phone_e164'])}"><span class="channel-card__label">تلفن ثابت</span>
    <span class="channel-card__value">{e(ch['phone'])}</span></a>
  <a class="channel-card" href="{attr(ch['whatsapp'])}" rel="noopener"><span class="channel-card__label">واتساپ و موبایل</span>
    <span class="channel-card__value">{e(ch['mobile'])}</span></a>
  <a class="channel-card" href="{attr(ch['instagram'])}" rel="noopener"><span class="channel-card__label">اینستاگرام</span>
    <span class="channel-card__value">@aanak.94</span></a>
  <a class="channel-card" href="mailto:{attr(ch['email'])}"><span class="channel-card__label">ایمیل</span>
    <span class="channel-card__value">{e(ch['email'])}</span></a>
</div>""")
        elif ui == "opening_hours_table":
            body.append(f'<div class="opening-hours-table"><table><thead><tr><th scope="col">روزها</th>'
                        f'<th scope="col">ساعات</th><th scope="col">توضیح</th></tr></thead><tbody>'
                        f'<tr><td data-label="روزها">شنبه تا جمعه</td><td data-label="ساعات">۱۰:۰۰ تا ۲۰:۰۰</td>'
                        f'<td data-label="توضیح">حضوری در پردیس کرج</td></tr>'
                        f'<tr><td data-label="روزها">روزهای تعطیل</td><td data-label="ساعات">پاسخ‌گویی پیام</td>'
                        f'<td data-label="توضیح">واتساپ و تلگرام</td></tr></tbody></table>'
                        f'<p class="tuition-note">{e(s.get("hours_raw", ""))}</p></div>')
        elif ui == "instructor_filter_bar":
            f = s["filters"]
            chips = []
            for g in f["gender"]:
                chips.append(f'<button class="filter-chip" type="button" aria-pressed="false" data-filter-key="gender" '
                             f'data-filter-value="{"female" if "خانم" in g else "male"}">{e(g)}</button>')
            body.append(f'<div class="instructor-filter-bar"><span class="filter-group__label">فیلتر جنسیت استاد:</span>'
                        f'{"".join(chips)}</div>{self.paras(s)}'
                        f'<p class="tuition-note">دانشکده‌ها: {e("، ".join(f["departments"]))} · '
                        f'گروه‌های سنی: {e("، ".join(f["age_groups"]))}</p>')
        elif ui in ("course_navigation_grid", "fardis_program_cards", "interactive_course_finder"):
            body.append(self.paras(s))
            if ui == "interactive_course_finder":
                body.append(self.course_finder(s))
            elif ui == "fardis_program_cards":
                cs = "".join(
                    f'<a class="course-card" href="{attr(c["slug"])}"><span class="course-card__title">'
                    f'{e(c["heading_fa"])}</span>'
                    f'<span class="course-card__meta">{e("، ".join(c["keywords"]))}</span></a>'
                    for c in s["cards"])
                body.append(f'<div class="course-navigation-grid">{cs}</div>')
            else:
                cs = []
                for c in s["cards"]:
                    ages = "، ".join({"kids": "کودکان", "teens": "نوجوانان", "adults": "بزرگسالان"}[a]
                                     for a in c.get("age_groups", []))
                    subs = "، ".join(c.get("sub_specialties_fa", []))
                    subs_html = f'<span class="course-card__meta">{e(subs)}</span>' if subs else ''
                    cs.append(f'<a class="course-card" href="{attr(c["slug"])}">'
                              f'<span class="course-card__title">{e(c["name_fa"])}</span>'
                              f'<span class="course-card__meta"><span>{e(ages)}</span>'
                              f'<span>{L.to_persian_digits(c.get("instructor_count", 0))} استاد ثبت‌شده</span></span>'
                              f'<span class="course-card__price">شروع از {e(c["tuition_group_toman_fa"])} تومان</span>'
                              f'{subs_html}</a>')
                body.append(f'<div class="course-navigation-grid">{"".join(cs)}</div>')
        elif ui == "hero_multifaculty_portal":
            pass
        elif ui == "trust_badges_grid":
            items = [s.get("license_fa", "")] + s.get("guarantees", [])
            body.append('<div class="trust-badges-grid">' + "".join(
                f'<div class="trust-badge"><span>{e(x)}</span></div>' for x in items if x) + "</div>")
        elif ui == "schedule_cards":
            body.append(f'<div class="fardis-commuter-box"><p>{e(s.get("g6_bluf", ""))}</p>'
                        '<ul class="shift-badges"><li class="badge">پنجشنبه صبح و بعدازظهر</li>'
                        '<li class="badge">جمعه صبح</li>'
                        '<li class="badge badge--teal">تعیین سطح رایگان پیش از شروع</li></ul></div>')
        elif ui == "faq_accordion_rtl":
            body.append(self.paras(s))
            body.append(self.faq_html(s.get("faq", [])))
        else:
            body.append(self.paras(s))

        if s.get("faq") and ui != "faq_accordion_rtl":
            body.append(self.faq_html(s["faq"]))
        if s.get("link") and ui not in ("fardis_commuter_box", "fardis_commuter_route_matrix",
                                        "art_cafe_stage_banner", "cafe_recital_cards",
                                        "cafe_live_schedule_grid", "audition_step_cards"):
            body.append(f'<p class="related-links"><a href="{attr(s["link"])}">'
                        f'{e(self.title_of.get(s["link"], s["link"]))}</a></p>')
        body.append(self.cta(s, "btn--accent" if "کافه" in (s.get("g7_cta") or "") else "btn--primary"))

        return f"""<{tag} class="section{alt_cls}" id="{attr(anchor)}">
  <div class="wrap">
    <div class="section__head"><{htag}>{e(s['heading_fa'])}</{htag}></div>
    {''.join(x for x in body if x)}
  </div>
</{tag}>"""

    def course_finder(self, s):
        cards = s["cards"]
        depts = sorted({c["department_id"] for c in cards})
        chips = ['<span class="filter-group__label">دانشکده:</span>']
        for d in depts:
            chips.append(f'<button class="filter-chip" type="button" aria-pressed="false" '
                         f'data-filter-key="dept" data-filter-value="{attr(d)}">'
                         f'{e(L.DEPARTMENTS[d]["name_fa"])}</button>')
        chips2 = ['<span class="filter-group__label">گروه سنی:</span>']
        for a, lab in (("kids", "کودکان"), ("teens", "نوجوانان"), ("adults", "بزرگسالان")):
            chips2.append(f'<button class="filter-chip" type="button" aria-pressed="false" '
                          f'data-filter-key="ages" data-filter-value="{a}">{e(lab)}</button>')
        chips3 = ['<span class="filter-group__label">فرمت و استاد:</span>']
        for v, lab in (("private", "خصوصی"), ("group", "گروهی")):
            chips3.append(f'<button class="filter-chip" type="button" aria-pressed="false" '
                          f'data-filter-key="formats" data-filter-value="{v}">{e(lab)}</button>')
        chips3.append('<button class="filter-chip" type="button" aria-pressed="false" '
                      'data-filter-key="female" data-filter-value="yes">حضور استاد خانم</button>')
        cs = []
        for c in cards:
            cs.append(f'<a class="course-card" data-filter-card href="{attr(c["slug"])}" '
                      f'data-dept="{attr(c["department_id"])}" data-ages="{attr(" ".join(c["age_groups"]))}" '
                      f'data-formats="{attr(" ".join(c["formats"]))}" '
                      f'data-female="{"yes" if c["has_female_instructor"] else "no"}">'
                      f'<span class="course-card__title">{e(c["name_fa"])}</span>'
                      f'<span class="course-card__price">شروع از {e(c["tuition_group_toman_fa"])} تومان</span></a>')
        return (f'<div data-filter-root><div class="course-finder__filters">'
                f'<div class="filter-row">{"".join(chips)}</div>'
                f'<div class="filter-row">{"".join(chips2)}</div>'
                f'<div class="filter-row">{"".join(chips3)}</div></div>'
                f'<div class="course-navigation-grid">{"".join(cs)}</div>'
                f'<p class="finder-empty data-gap">با این فیلترها دوره‌ای پیدا نشد؛ فیلترها را بردارید یا '
                f'برای مشاوره تماس بگیرید.</p></div>')

    def render_hero(self, entry, s):
        slug = entry["url_slug"]
        dark = " section--cafe-dark" if entry["tier"] == "3" else ""
        badges = "".join(f'<li><span class="badge">{e(b)}</span></li>' for b in s.get("badges", []))
        pills = "".join(f'<li><a href="{attr(h)}">{e(t)}</a></li>' for t, h in s.get("jump_pills", []))
        if not pills:
            pills = "".join(f'<li><a href="#{attr(x["anchor"])}">{e(x["heading_fa"][:26])}</a></li>'
                            for x in entry["sections"][1:7])
        hero_img = self.hero_img_for(entry)
        ortho = entry.get("orthographic_variants_assigned") or []
        alt = (f"{entry['primary_keyword']} — {self.p['brand_fa']}"
               + (f" ({ortho[0]})" if ortho else ""))
        cta2 = ""
        if entry["tier"] == "3":
            cta1 = f'<a class="btn btn--accent" href="#reservation">{e(s.get("g7_cta", "رزرو میز"))}</a>'
            cta2 = f'<a class="btn btn--ghost" href="tel:{attr(self.p["phone_e164"])}">تماس برای رزرو</a>'
        else:
            cta1 = (f'<button class="btn btn--primary" type="button" data-dialog-open="#consult-dialog">'
                    f'{e(s.get("g7_cta", "رزرو مشاوره و تعیین سطح رایگان"))}</button>')
            cta2 = f'<a class="btn btn--ghost" href="tel:{attr(self.p["phone_e164"])}">تماس: {e(self.p["phone_display"])}</a>'
        portal = ""
        if s.get("portal_cards"):
            portal = '<div class="portal-grid" style="margin-block-start:var(--space-xl)">' + "".join(
                f'<a class="portal-card{" portal-card--cafe" if "cafe" in c["slug"] else ""}" '
                f'href="{attr(c["slug"])}"><span class="portal-card__title">{e(c["title_fa"])}</span></a>'
                for c in s["portal_cards"]) + "</div>"
        return f"""<header class="compact-course-hero{dark}" id="{attr(s['anchor'])}">
  <div class="wrap">
    {self.breadcrumb_html(entry)}
    <div class="compact-course-hero__grid">
      <div>
        <h1>{e(s['heading_fa'])}</h1>
        <p class="bluf">{e(s.get('g6_bluf', ''))}</p>
        {f'<ul class="stat-badges">{badges}</ul>' if badges else ''}
        {self.paras(s)}
        <div class="hero__cta">{cta1}{cta2}</div>
        <ul class="jump-pills">{pills}</ul>
      </div>
      <div class="hero__media">{self.img(hero_img, alt, 1200, 675, eager=True)}</div>
    </div>
    {portal}
  </div>
</header>"""

    # -------------------------------------------------------------- page
    def related_block(self, entry):
        pm = self.pm_by_slug[entry["url_slug"]]
        links = [x for x in pm["internal_links_to"] if x != entry["url_slug"]]
        if not links:
            return ""
        items = "".join(f'<li><a href="{attr(x)}">{e(self.title_of.get(x, x))}</a></li>' for x in links)
        return f"""<section class="section section--alt" id="related">
  <div class="wrap">
    <div class="section__head"><h2>مسیرهای مرتبط در آموزشگاه آنک کرج</h2></div>
    <ul class="related-links">{items}</ul>
  </div>
</section>"""

    def render_page(self, entry):
        slug = entry["url_slug"]
        canonical = self.domain + slug
        ld = json.dumps(self.schema["pages"][slug]["json_ld"], ensure_ascii=False, separators=(",", ":"))
        secs = "".join(self.render_section(entry, s, i) for i, s in enumerate(entry["sections"]))
        og_img = self.domain + "/assets/img/" + self.hero_img_for(entry)
        ortho = entry.get("orthographic_variants_assigned") or []
        ortho_meta = (f'\n  <meta name="keywords" content="{attr("، ".join([entry["primary_keyword"]] + ortho[:6]))}">'
                      if ortho else "")
        return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl" class="no-js">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(entry['meta_title'])}</title>
  <meta name="description" content="{attr(entry['meta_description'])}">
  <link rel="canonical" href="{attr(canonical)}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
  <meta name="theme-color" content="#141B2D">
  <meta name="author" content="{attr(self.p['brand_fa'])}">
  <meta name="geo.region" content="IR-32">
  <meta name="geo.placename" content="کرج">{ortho_meta}
  <meta property="og:type" content="website">
  <meta property="og:locale" content="fa_IR">
  <meta property="og:site_name" content="{attr(self.p['brand_fa'])}">
  <meta property="og:title" content="{attr(entry['meta_title'])}">
  <meta property="og:description" content="{attr(entry['meta_description'])}">
  <meta property="og:url" content="{attr(canonical)}">
  <meta property="og:image" content="{attr(og_img)}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="/assets/css/design-system.css">
  <script type="application/ld+json">{ld}</script>
</head>
<body>
  <a class="skip-link" href="#main">پرش به محتوای اصلی</a>
  {self.header(slug)}
  <main id="main">
    {secs}
    {self.related_block(entry)}
  </main>
  {self.footer()}
  {self.mobile_bar(slug)}
  {self.dialogs()}
  <script src="/assets/js/app.js" defer></script>
</body>
</html>
"""

    def build(self):
        write_images()
        written = []
        for entry in self.plan["pages"]:
            slug = entry["url_slug"]
            rel = "index.html" if slug == "/" else slug.strip("/") + "/index.html"
            path = os.path.join(DIST, rel)
            L.ensure_dirs(os.path.dirname(path))
            L.write_text(path, self.render_page(entry))
            written.append((slug, path))
        # ---- sitemap + robots
        today = date.today().isoformat()
        prio = {"0": "1.0", "1": "0.9", "2": "0.8", "3": "0.8", "4": "0.7"}
        urls = "".join(
            f"\n  <url>\n    <loc>{self.domain}{p['url_slug']}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            f"    <changefreq>{'weekly' if p['tier'] in ('0', '3') else 'monthly'}</changefreq>\n"
            f"    <priority>{prio.get(p['tier'], '0.7')}</priority>\n  </url>"
            for p in self.page_map["pages"])
        L.write_text(os.path.join(DIST, "sitemap.xml"),
                     '<?xml version="1.0" encoding="UTF-8"?>\n'
                     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + "\n</urlset>\n")
        L.write_text(os.path.join(DIST, "robots.txt"),
                     "User-agent: *\nAllow: /\nDisallow: /assets/data/\n"
                     f"Sitemap: {self.domain}/sitemap.xml\n")
        return written


def main():
    b = Builder()
    written = b.build()
    total = sum(os.path.getsize(p) for _, p in written)
    L.update_progress("CODER_PHASE_2", "COMPLETE",
                      ["dist/**/index.html", "dist/sitemap.xml", "dist/robots.txt"],
                      {"D2_1_all_pages_written": len(written) == len(b.page_map["pages"]),
                       "D2_2_sitemap_and_robots": os.path.exists(os.path.join(DIST, "sitemap.xml"))
                       and os.path.exists(os.path.join(DIST, "robots.txt"))},
                      "CODER_PHASE_3_AUDIT")
    print("=" * 74)
    print("CODER PHASE 2 (PRODUCTION BUILD) — COMPLETE")
    print("=" * 74)
    print(f"  pages written : {len(written)}")
    print(f"  total html    : {total:,} bytes")
    print(f"  sitemap.xml   : {len(b.page_map['pages'])} urls")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
