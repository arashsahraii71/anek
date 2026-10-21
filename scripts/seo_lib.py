#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO DOMINATOR AGENT — SHARED LIBRARY
Loaders, Persian orthographic normalisation engine and the deterministic
6-dimensional keyword classifier used by Unified Phases 0 → 4 and by the
Designer/Coder Agent.

Single source of truth: every phase imports this module, so the silo
assignment used in Phase 1 is byte-identical to the one used by the HTML
builder in Designer Phase 2 and by the final audit.
"""
from __future__ import annotations

import csv
import json
import os
import re
import time
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT = os.path.join(ROOT, "input")
OUTPUT = os.path.join(ROOT, "output")
SILOS = os.path.join(OUTPUT, "silos")
DOSSIERS = os.path.join(ROOT, "seo_dossiers")
DESIGN = os.path.join(ROOT, "design_system")
DIST = os.path.join(ROOT, "dist")

DOMAIN = "https://aanak.ir"


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ensure_dirs(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)


def write_json(path: str, data) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def read_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path: str, text: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


# ==============================================================================
# 1. PERSIAN ORTHOGRAPHIC NORMALISATION ENGINE
# ==============================================================================
ZWNJ = "\u200c"

MADDAH_MAP = OrderedDict([
    ("اموزشگاه", "آموزشگاه"),
    ("اموزش", "آموزش"),
    ("اواز", "آواز"),
    ("ادرس", "آدرس"),
    ("اکادمی", "آکادمی"),
    ("اساتید", "اساتید"),  # no maddah needed, kept for clarity
])

SPACING_VARIANTS = {
    "کلاسهای": "کلاس های",
    "کلاس‌های": "کلاس های",
    "سه‌تار": "سه تار",
    "هنگ‌درام": "هنگ درام",
    "خانم‌ها": "خانم ها",
}


def normalize_persian(text: str) -> str:
    """Arabic Yeh/Kaf → Persian, ZWNJ → space, maddah restoration, space collapse."""
    t = text.strip()
    t = t.replace("ي", "ی").replace("ك", "ک").replace("ۀ", "ه").replace("ة", "ه")
    t = t.replace("\u064a", "ی").replace("\u0643", "ک")
    t = t.replace(ZWNJ, " ")
    for old, new in SPACING_VARIANTS.items():
        t = t.replace(old, new)
    for old, new in MADDAH_MAP.items():
        t = t.replace(old, new)
    t = re.sub(r"[\u064B-\u065F\u0670]", "", t)  # harakat
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def is_no_maddah_variant(raw: str) -> bool:
    r = raw.replace(ZWNJ, " ")
    return any(re.search(r"(?<![آ-ی])" + v, r) for v in ("اموزش", "اموزشگاه", "اواز", "ادرس", "اکادمی"))


def is_spacing_variant(raw: str) -> bool:
    return ("کلاسهای" in raw) or (ZWNJ in raw)


PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def to_persian_digits(value) -> str:
    s = str(value)
    return "".join(PERSIAN_DIGITS[int(c)] if c.isdigit() else c for c in s)


def group_number(n: int) -> str:
    return f"{n:,}".replace(",", "٬")


def irr_to_toman_fa(irr) -> str:
    """Verbatim IRR value from courses.csv rendered as Persian Toman (1 Toman = 10 IRR)."""
    try:
        v = int(str(irr).strip() or 0)
    except ValueError:
        return ""
    if v <= 0:
        return ""
    return to_persian_digits(group_number(v // 10))


def irr_fa(irr) -> str:
    try:
        v = int(str(irr).strip() or 0)
    except ValueError:
        return ""
    if v <= 0:
        return ""
    return to_persian_digits(group_number(v))


# ==============================================================================
# 2. INPUT LOADERS
# ==============================================================================
def load_keywords() -> list:
    path = os.path.join(INPUT, "keywords.txt")
    with open(path, "r", encoding="utf-8-sig") as f:
        return [ln.strip() for ln in f.read().replace("\r\n", "\n").split("\n") if ln.strip()]


def load_csv(name: str) -> list:
    path = os.path.join(INPUT, name)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def load_courses() -> list:
    return load_csv("courses.csv")


def load_instructors() -> list:
    return load_csv("instructors.csv")


def load_cafe_events() -> list:
    return load_csv("cafe_events.csv")


def load_academy_data() -> dict:
    """Parses input/academy_data.txt into a dict of scalars + list blocks."""
    path = os.path.join(INPUT, "academy_data.txt")
    raw = open(path, "r", encoding="utf-8-sig").read().replace("\r\n", "\n")
    data, lists, current = {}, defaultdict(list), None
    for line in raw.split("\n"):
        line = line.rstrip()
        if not line.strip():
            continue
        if line.startswith("- "):
            item = line[2:].strip()
            m = re.match(r"^([A-Z0-9_]+):\s*(.*)$", item)
            if m and current in (None, "CONTACT_CHANNELS"):
                data[m.group(1)] = m.group(2).strip()
            elif current:
                lists[current].append(item)
            continue
        m = re.match(r"^([A-Z0-9_]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            current = key
            if val:
                data[key] = val
            continue
    data["_lists"] = {k: v for k, v in lists.items()}
    return data


def load_serp_matrix() -> dict:
    for p in (os.path.join(INPUT, "serp_algorithm_matrix.json"),
              os.path.join(OUTPUT, "serp_algorithm_matrix.json")):
        if os.path.exists(p):
            return read_json(p, {}) or {}
    return {}


# ==============================================================================
# 3. SILO / ENTITY REGISTRY
# ==============================================================================
DEPARTMENTS = OrderedDict([
    ("DEPT_MUSIC", {
        "entity_id": "E_DEPT_MUSIC", "silo_id": "SILO_DEPT_01_MUSIC", "slug": "/music/",
        "name_fa": "دانشکده موسیقی و آواز",
        "title_fa": "آموزشگاه موسیقی در کرج",
        "breadcrumb_fa": "دانشکده موسیقی",
    }),
    ("DEPT_PERFORMING", {
        "entity_id": "E_DEPT_PERFORMING", "silo_id": "SILO_DEPT_02_PERFORMING", "slug": "/performing-arts/",
        "name_fa": "دانشکده بازیگری، فن بیان و گویندگی",
        "title_fa": "آموزشگاه بازیگری، فن بیان و گویندگی در کرج",
        "breadcrumb_fa": "بازیگری و فن بیان",
    }),
    ("DEPT_CINEMA", {
        "entity_id": "E_DEPT_CINEMA", "silo_id": "SILO_DEPT_03_CINEMA", "slug": "/cinema-media/",
        "name_fa": "دانشکده سینما، عکاسی، تدوین و گریم",
        "title_fa": "آموزشگاه سینمایی، عکاسی و گریم در کرج",
        "breadcrumb_fa": "سینما و رسانه",
    }),
    ("DEPT_VISUAL", {
        "entity_id": "E_DEPT_VISUAL", "silo_id": "SILO_DEPT_04_VISUAL", "slug": "/visual-arts/",
        "name_fa": "دانشکده هنرهای تجسمی و خوشنویسی",
        "title_fa": "آموزشگاه طراحی، نقاشی و خوشنویسی در کرج",
        "breadcrumb_fa": "هنرهای تجسمی",
    }),
])

# course_id → silo_id
COURSE_SILO = {
    "CRS_PIANO": "SILO_CRS_PIANO", "CRS_GUITAR": "SILO_CRS_GUITAR", "CRS_VIOLIN": "SILO_CRS_VIOLIN",
    "CRS_VOCALS": "SILO_CRS_VOCALS", "CRS_TAR_SETAR": "SILO_CRS_TAR_SETAR", "CRS_SANTOOR": "SILO_CRS_SANTOOR",
    "CRS_TONBAK": "SILO_CRS_TONBAK", "CRS_DAF": "SILO_CRS_DAF", "CRS_KAMANCHEH": "SILO_CRS_KAMANCHEH",
    "CRS_TANBOUR": "SILO_CRS_TANBOUR", "CRS_FLUTE": "SILO_CRS_FLUTE", "CRS_HANGDRUM": "SILO_CRS_HANGDRUM",
    "CRS_ORGAN": "SILO_CRS_ORGAN", "CRS_KIDS_MUSIC": "SILO_CRS_KIDS_MUSIC", "CRS_ACTING": "SILO_CRS_ACTING",
    "CRS_KIDS_ACTING": "SILO_CRS_KIDS_ACTING", "CRS_SPEECH": "SILO_CRS_SPEECH",
    "CRS_VOICE_DUBBING": "SILO_CRS_VOICE_DUBBING", "CRS_PHOTOGRAPHY": "SILO_CRS_PHOTOGRAPHY",
    "CRS_FILM_EDITING": "SILO_CRS_FILM_EDITING", "CRS_DIRECTING_SCRIPT": "SILO_CRS_DIRECTING_SCRIPT",
    "CRS_MAKEUP": "SILO_CRS_MAKEUP", "CRS_PAINTING": "SILO_CRS_PAINTING", "CRS_CALLIGRAPHY": "SILO_CRS_CALLIGRAPHY",
}
SILO_COURSE = {v: k for k, v in COURSE_SILO.items()}

SPECIAL_SILOS = {
    "SILO_00": {"slug": "/", "entity_id": "E_ACADEMY_ROOT", "name_fa": "صفحه اصلی آموزشگاه و برند"},
    "SILO_CAFE_01": {"slug": "/art-cafe/", "entity_id": "E_CAFE_VENUE", "name_fa": "کافه هنر و موسیقی زنده"},
    "SILO_GEO_FARDIS": {"slug": "/fardis-branch/", "entity_id": "E_GEO_FARDIS", "name_fa": "هاب هنرجویان فردیس کرج"},
    "SILO_CONV_AUDITION": {"slug": "/acting-audition/", "entity_id": "E_HUB_AUDITION", "name_fa": "تست بازیگری و تعیین سطح"},
}

# Cafe keyword → instrument + linked course slug
CAFE_INSTRUMENTS = [
    ("پیانو", "SEC_CAFE_LIVE_PIANO", "/music/piano/", "CRS_PIANO", "cafe-piano"),
    ("گیتار", "SEC_CAFE_LIVE_GUITAR", "/music/guitar/", "CRS_GUITAR", "cafe-guitar"),
    ("سنتور", "SEC_CAFE_LIVE_SANTOOR", "/music/santoor/", "CRS_SANTOOR", "cafe-santoor"),
    ("سه تار", "SEC_CAFE_LIVE_SETAR", "/music/tar-setar/", "CRS_TAR_SETAR", "cafe-setar"),
    ("ارگ", "SEC_CAFE_LIVE_ORGAN", "/music/keyboard-organ/", "CRS_ORGAN", "cafe-organ"),
]

# Fardis demanded programme → course
FARDIS_PROGRAMS = [
    ("موسیقی", "CRS_KIDS_MUSIC", "/music/", "DEPT_MUSIC"),
]

# ==============================================================================
# 4. DETERMINISTIC KEYWORD CLASSIFIER (6 DIMENSIONS)
# ==============================================================================
# Rule order matters: first match wins. Compound/hospitality/geo intents are
# evaluated BEFORE discipline stems so `کافه گیتار کرج` never lands in the
# guitar classroom silo.
SILO_RULES = [
    ("SILO_CAFE_01", r"کافه|رستوران"),
    ("SILO_CONV_AUDITION", r"تست بازیگری"),
    ("SILO_GEO_FARDIS", r"فردیس"),
    ("SILO_CRS_PIANO", r"پیانو"),
    ("SILO_CRS_GUITAR", r"گیتار"),
    ("SILO_CRS_VIOLIN", r"ویولن|ویلن"),
    ("SILO_CRS_SANTOOR", r"سنتور"),
    ("SILO_CRS_TAR_SETAR", r"سه تار|(?<![\u0600-\u06FF])تار(?![\u0600-\u06FF])"),
    ("SILO_CRS_TONBAK", r"تنبک"),
    ("SILO_CRS_TANBOUR", r"تنبور"),
    ("SILO_CRS_DAF", r"(?<![\u0600-\u06FF])دف(?![\u0600-\u06FF])|دف زنی|دف نوازی"),
    ("SILO_CRS_KAMANCHEH", r"کمانچه"),
    ("SILO_CRS_FLUTE", r"فلوت"),
    ("SILO_CRS_HANGDRUM", r"هنگ درام"),
    ("SILO_CRS_ORGAN", r"(?<![\u0600-\u06FF])ارگ(?![\u0600-\u06FF])|کیبورد"),
    ("SILO_CRS_KIDS_MUSIC", r"موسیقی.*(کودک|نوجوان)|(کودک|نوجوان).*موسیقی"),
    ("SILO_CRS_VOCALS", r"آواز|خوانندگی"),
    ("SILO_CRS_VOICE_DUBBING", r"گویندگی|دوبله|دوبلاژ|دوبلور"),
    ("SILO_CRS_SPEECH", r"فن بیان|سخنوری|مجری"),
    ("SILO_DEPT_01_MUSIC", r"موسیقی"),
    ("SILO_CRS_KIDS_ACTING", r"(بازیگری|تئاتر|نمایش خلاق).*(کودک|نوجوان)|(کودک|نوجوان).*(بازیگری|تئاتر|نمایش خلاق)|نمایش خلاق"),
    ("SILO_CRS_ACTING", r"بازیگری|تئاتر"),
    ("SILO_CRS_PHOTOGRAPHY", r"عکاسی|فیلمبرداری"),
    ("SILO_CRS_FILM_EDITING", r"تدوین|ادیت"),
    ("SILO_CRS_DIRECTING_SCRIPT", r"کارگردانی|فیلمنامه"),
    ("SILO_CRS_MAKEUP", r"گریم|میکاپ|چهره پردازی"),
    ("SILO_CRS_PAINTING", r"نقاشی|طراحی"),
    ("SILO_CRS_CALLIGRAPHY", r"خوشنویسی|خطاطی|(?<![\u0600-\u06FF])خط(?![\u0600-\u06FF])"),
]

INTENT_RULES = [
    ("CAFE_LIVE_MUSIC", r"کافه|رستوران"),
    ("AUDITION_TEST", r"تست بازیگری"),
    ("FEMALE_SPECIFIC", r"خانم|بانوان"),
    ("TUITION_COST", r"قیمت|شهریه|هزینه"),
    ("LOCATION_DIRECTION", r"آدرس|کجاست"),
    ("KIDS_TEENS_SPECIFIC", r"کودک|نوجوان"),
    ("INSTRUCTOR_SEEKING", r"استاد|اساتید|مدرس|معلم|تدریس"),
    ("SUPERLATIVE_COMPARISON", r"بهترین|خوب"),
    ("COURSE_ENROLLMENT", r".*"),
]

# section_target canonical enum (Unified Phase 1 · Step 7)
SECTION_RULES = [
    ("SEC_CAFE_STAGE_MENU", r"کافه|رستوران"),
    ("SEC_FEMALE_INSTRUCTORS", r"خانم|بانوان"),
    ("SEC_PRIVATE_VS_GROUP_FORMAT", r"خصوصی|گروهی|حضوری"),
    ("SEC_TUITION_TABLE", r"قیمت|شهریه|هزینه"),
    ("SEC_CAMPUS_MAP_DIRECTIONS", r"آدرس|کجاست"),
    ("SEC_KIDS_TEENS_TRACK", r"کودک|نوجوان"),
    ("SEC_INSTRUCTOR_ROSTER", r"استاد|اساتید|مدرس|معلم|تدریس"),
    ("SEC_HERO_OVERVIEW", r".*"),
]

SUB_SPECIALTY_RULES = [
    ("ELECTRIC_GUITAR", r"گیتار الکتریک|گیتار برقی"),
    ("CELLO", r"ویولن سل"),
    ("PAN_FLUTE", r"پن فلوت"),
    ("LAKOTA_FLUTE", r"فلوت لاکوتا"),
    ("VOCALS_SONNATI", r"آواز سنتی"),
    ("VOCALS_POP", r"آواز پاپ"),
    ("VOCALS_GROUP_CHOIR", r"آواز گروهی"),
    ("BALLPOINT_CALLIGRAPHY", r"خوشنویسی با خودکار|خط تحریری"),
    ("MOBILE_PHOTOGRAPHY", r"عکاسی با موبایل"),
    ("VIDEOGRAPHY", r"فیلمبرداری"),
    ("KIDS_MAKEUP", r"گریم کودک"),
    ("CINEMATIC_MAKEUP", r"گریم سینمایی"),
    ("BEAUTY_MAKEUP", r"میکاپ"),
    ("STAGE_HOSTING", r"مجری"),
    ("DUBBING", r"دوبله|دوبلاژ|دوبلور"),
    ("SCREENWRITING", r"فیلمنامه"),
    ("DIRECTING", r"کارگردانی"),
    ("MUSIC_THEORY", r"تئوری موسیقی"),
    ("VIDEO_EDITING_REELS", r"ادیت"),
    ("KHAT_TAHRIRI", r"خطاطی"),
    ("DAF_ZANI", r"دف زنی"),
]

FARDIS_ROUTING = [
    (r"موسیقی.*(کودک|کودکان)|(کودک|کودکان).*موسیقی", "SILO_CRS_KIDS_MUSIC", "/music/kids/"),
    (r"آواز|خوانندگی", "SILO_CRS_VOCALS", "/music/vocals/"),
    (r"بازیگری|تئاتر", "SILO_CRS_ACTING", "/performing-arts/acting/"),
    (r"فن بیان|سخنوری", "SILO_CRS_SPEECH", "/performing-arts/public-speaking/"),
    (r"گویندگی|دوبله", "SILO_CRS_VOICE_DUBBING", "/performing-arts/voice-acting-dubbing/"),
    (r"خوشنویسی|خطاطی", "SILO_CRS_CALLIGRAPHY", "/visual-arts/calligraphy/"),
    (r"موسیقی", "SILO_DEPT_01_MUSIC", "/music/"),
]


def _first_match(rules, text, default=None):
    for key, pattern in rules:
        if re.search(pattern, text):
            return key
    return default


def classify_keyword(raw: str) -> dict:
    """6-dimensional classification of a single raw keyword line."""
    norm = normalize_persian(raw)
    silo = _first_match(SILO_RULES, norm, "SILO_00")
    intent = _first_match(INTENT_RULES, norm, "COURSE_ENROLLMENT")
    section = _first_match(SECTION_RULES, norm, "SEC_HERO_OVERVIEW")
    geo = "FARDIS_KARAJ" if "فردیس" in norm else "KARAJ"

    subs = [name for name, pat in SUB_SPECIALTY_RULES if re.search(pat, norm)]

    # notes
    notes = []
    if is_no_maddah_variant(raw):
        notes.append("ORTHO_VARIANT_NO_MADDAH")
    if is_spacing_variant(raw):
        notes.append("ORTHO_VARIANT_SPACING")
    for s in subs:
        notes.append(f"SUB_SPECIALTY:{s}")

    # dual-intent routing
    dual = None
    if silo == "SILO_GEO_FARDIS":
        for pat, target_silo, slug in FARDIS_ROUTING:
            if re.search(pat, norm):
                dual = target_silo
                break
        section = "SEC_HERO_OVERVIEW" if section == "SEC_HERO_OVERVIEW" else section
    elif silo == "SILO_CAFE_01":
        for fa, sec, slug, cid, anchor in CAFE_INSTRUMENTS:
            if fa in norm:
                dual = COURSE_SILO[cid]
                section = "SEC_CAFE_STAGE_MENU"
                notes.append(f"CAFE_NIGHT:{sec}")
                break
    elif silo == "SILO_CONV_AUDITION":
        dual = "SILO_CRS_ACTING"
    elif section == "SEC_CAMPUS_MAP_DIRECTIONS":
        dual = "SILO_00"

    if dual:
        notes.append(f"DUAL_INTENT:{dual}")

    # funnel stage
    if intent in ("TUITION_COST", "LOCATION_DIRECTION", "AUDITION_TEST", "FEMALE_SPECIFIC"):
        funnel = "decision"
    elif section == "SEC_PRIVATE_VS_GROUP_FORMAT":
        funnel = "decision"
    elif intent in ("INSTRUCTOR_SEEKING", "SUPERLATIVE_COMPARISON", "KIDS_TEENS_SPECIFIC", "CAFE_LIVE_MUSIC"):
        funnel = "consideration"
    else:
        funnel = "awareness"

    # mapped entity
    if silo in SILO_COURSE:
        entity = "E_" + SILO_COURSE[silo]
    elif silo in SPECIAL_SILOS:
        entity = SPECIAL_SILOS[silo]["entity_id"]
    else:
        entity = {d["silo_id"]: d["entity_id"] for d in DEPARTMENTS.values()}.get(silo, "E_ACADEMY_ROOT")

    dept = None
    if silo in SILO_COURSE:
        dept = COURSE_DEPT.get(SILO_COURSE[silo])
    elif silo in [d["silo_id"] for d in DEPARTMENTS.values()]:
        dept = [k for k, v in DEPARTMENTS.items() if v["silo_id"] == silo][0]

    return {
        "raw_keyword": raw,
        "normalized_keyword": norm,
        "orthographic_variant": bool(is_no_maddah_variant(raw) or is_spacing_variant(raw)),
        "silo_id": silo,
        "mapped_department": dept or ("E_CAFE_VENUE" if silo == "SILO_CAFE_01" else "ACADEMY_ROOT"),
        "mapped_course_or_hub": entity,
        "geo_target": geo,
        "intent_vector": intent,
        "funnel_stage": funnel,
        "section_target": section,
        "sub_specialties": subs,
        "dual_intent": dual,
        "notes": ";".join(notes) if notes else "NONE",
    }


COURSE_DEPT = {}  # filled on first load_course_index() call


def load_course_index() -> dict:
    """course_id → enriched course record (slug, silo, department, tuition, …)."""
    global COURSE_DEPT
    idx = OrderedDict()
    for row in load_courses():
        cid = row["course_id"].strip()
        dept = row["department_id"].strip()
        COURSE_DEPT[cid] = dept
        parent = row["parent_hub_slug"].strip()
        slug = parent + row["url_slug"].strip() + "/"
        idx[cid] = {
            "course_id": cid,
            "department_id": dept,
            "name_fa": row["name_fa"].strip(),
            "slug": slug,
            "parent_hub_slug": parent,
            "sub_specialties_fa": [s for s in row["sub_specialties_fa"].split("|") if s.strip()],
            "formats_offered": [s for s in row["formats_offered"].split("|") if s.strip()],
            "age_groups": [s for s in row["age_groups"].split("|") if s.strip()],
            "has_female_instructor": row["has_female_instructor"].strip().lower() == "true",
            "tuition_private_irr": int(row["tuition_private_irr"] or 0),
            "tuition_group_irr": int(row["tuition_group_irr"] or 0),
            "sessions_per_term": int(row["sessions_per_term"] or 0),
            "session_duration_min": int(row["session_duration_min"] or 0),
            "certificate_type": row["certificate_type"].strip(),
            "performed_in_cafe": row["performed_in_cafe"].strip().lower() == "true",
            "fardis_high_demand": row["fardis_high_demand"].strip().lower() == "true",
            "status": row["status"].strip(),
            "silo_id": COURSE_SILO.get(cid, ""),
        }
    return idx


def instructors_for(course_id: str, instructors: list) -> list:
    out = []
    for i in instructors:
        ids = [c.strip() for c in i.get("course_ids", "").split("|") if c.strip()]
        if course_id in ids:
            out.append(i)
    return out


def is_placeholder_instructor(i: dict) -> bool:
    return i.get("status", "").strip() != "verified" or "[" in i.get("name_fa", "")


def classify_all() -> list:
    load_course_index()
    return [classify_keyword(k) for k in load_keywords()]


def silo_registry(records: list) -> "OrderedDict":
    """silo_id → {keywords: [record...], slug, …} for every silo that exists."""
    courses = load_course_index()
    reg = OrderedDict()

    def add(silo_id, slug, name_fa, kind, department_id=None, course_id=None):
        reg[silo_id] = {"silo_id": silo_id, "target_slug": slug, "name_fa": name_fa,
                        "kind": kind, "department_id": department_id, "course_id": course_id,
                        "keywords": []}

    add("SILO_00", "/", "برند، ناوبری و پردیس مرکزی کرج", "brand")
    for dkey, d in DEPARTMENTS.items():
        add(d["silo_id"], d["slug"], d["name_fa"], "department", department_id=dkey)
    for cid, c in courses.items():
        add(c["silo_id"], c["slug"], c["name_fa"], "course", department_id=c["department_id"], course_id=cid)
    add("SILO_CAFE_01", "/art-cafe/", "کافه هنر و موسیقی زنده", "cafe")
    add("SILO_GEO_FARDIS", "/fardis-branch/", "دسترسی هنرجویان فردیس کرج", "geo")
    add("SILO_CONV_AUDITION", "/acting-audition/", "تست بازیگری و تعیین سطح در کرج", "conversion")

    for r in records:
        reg[r["silo_id"]]["keywords"].append(r)
    return reg


# ==============================================================================
# 5. ACADEMY CONSTANTS DERIVED FROM academy_data.txt
# ==============================================================================
def academy_profile() -> dict:
    a = load_academy_data()
    lists = a.get("_lists", {})
    return {
        "brand_fa": a.get("BRAND_NAME", ""),
        "brand_en": a.get("BRAND_NAME_EN", ""),
        "tagline_fa": a.get("TAGLINE", ""),
        "license_fa": a.get("OFFICIAL_LICENSE", ""),
        "year_founded": a.get("YEAR_FOUNDED", ""),
        "years_in_operation": a.get("YEARS_IN_OPERATION", ""),
        "language": a.get("SITE_LANGUAGE", "fa"),
        "direction": a.get("SITE_DIRECTION", "rtl"),
        "city": a.get("PRIMARY_CITY", "کرج"),
        "province": a.get("PROVINCE", ""),
        "postal_code": a.get("POSTAL_CODE", ""),
        "domain": a.get("DOMAIN", DOMAIN),
        "location_model": a.get("BUSINESS_LOCATION_MODEL", ""),
        "address_fa": a.get("EXACT_ADDRESS", ""),
        "geo": a.get("GEO_COORDINATES_GOOGLE", ""),
        "geo_routing": a.get("GEO_COORDINATES_ROUTING", ""),
        "service_radius_m": a.get("SERVICE_RADIUS_METERS", ""),
        "served_cities": [s.strip() for s in a.get("SERVED_CITIES", "").split("،") if s.strip()],
        "served_neighborhoods": [s.strip() for s in a.get("SERVED_NEIGHBORHOODS", "").split("،") if s.strip()],
        "landmarks": lists.get("NEARBY_LANDMARKS", []),
        "transit_routes": lists.get("TRANSIT_AND_COMMUTER_ROUTES", []),
        "guarantees": lists.get("GUARANTEES_AND_PROOF", []),
        "cafe_lines": lists.get("ART_CAFE_VENUE", []),
        "phone_display": a.get("PRIMARY_PHONE_DISPLAY", ""),
        "phone_e164": a.get("PRIMARY_PHONE_E164", ""),
        "mobile_whatsapp": a.get("MOBILE_AND_WHATSAPP", ""),
        "whatsapp_url": a.get("WHATSAPP_URL", ""),
        "instagram_url": a.get("INSTAGRAM_URL", ""),
        "email": a.get("PUBLIC_EMAIL", ""),
        "opening_hours": a.get("OPENING_HOURS", ""),
        "maps_url": a.get("GOOGLE_MAPS_URL", ""),
        "neshan_url": a.get("NESHAN_URL", ""),
        "balad_url": a.get("BALAD_URL", ""),
        "waze_url": a.get("WAZE_URL", ""),
        "raw": a,
    }


def fardis_status(profile: dict) -> str:
    """Truth gate: PHYSICAL_BRANCH only if a distinct Fardis street address exists."""
    addr = profile.get("address_fa", "")
    if re.search(r"فردیس", addr):
        return "PHYSICAL_BRANCH"
    return "SERVICE_AREA_COMMUTER_HUB"


# ==============================================================================
# 6. PROGRESS TRACKER
# ==============================================================================
PROGRESS_PATH = os.path.join(OUTPUT, "progress_seo.json")


def update_progress(phase_id: str, status: str, artifacts: list, gates: dict, next_phase: str):
    prog = read_json(PROGRESS_PATH, None) or {
        "project": "SEO DOMINATOR AGENT — آموزشگاه سینمایی و بازیگری آنک (کرج)",
        "created_at": now_iso(),
        "current_phase": phase_id,
        "phases": {},
    }
    prog["updated_at"] = now_iso()
    prog["current_phase"] = next_phase
    prog["phases"][phase_id] = {
        "status": status,
        "completed_at": now_iso(),
        "artifacts": artifacts,
        "gates": gates,
        "gates_passed": all(bool(v) for v in gates.values()) if gates else True,
    }
    write_json(PROGRESS_PATH, prog)
    return prog
