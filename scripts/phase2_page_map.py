#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIFIED PHASE 2 — SIX-TIER PAGE MAP, ANTI-CANNIBALISATION & HUB-SPOKE ENGINE
Artifact: output/page_map.json
"""
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_lib as L  # noqa: E402

# ------------------------------------------------------------------ helpers
SUB_MODULE_LABELS = {
    "ELECTRIC_GUITAR": ("MOD_SUB_ELECTRIC_GUITAR", "آموزش گیتار الکتریک و برقی در کرج"),
    "CELLO": ("MOD_SUB_CELLO", "کلاس ویولن سل (چلو) در کرج"),
    "PAN_FLUTE": ("MOD_SUB_PAN_FLUTE", "آموزش پن فلوت در کرج"),
    "LAKOTA_FLUTE": ("MOD_SUB_LAKOTA_FLUTE", "آموزش فلوت لاکوتا در کرج"),
    "VOCALS_SONNATI": ("MOD_SUB_SONNATI", "آموزش آواز سنتی در کرج"),
    "VOCALS_POP": ("MOD_SUB_POP", "کلاس آواز پاپ در کرج"),
    "VOCALS_GROUP_CHOIR": ("MOD_SUB_GROUP_CHOIR", "کلاس آواز گروهی و کر در کرج"),
    "BALLPOINT_CALLIGRAPHY": ("MOD_SUB_BALLPOINT_CALLIGRAPHY", "آموزش خوشنویسی با خودکار (خط تحریری) در کرج"),
    "MOBILE_PHOTOGRAPHY": ("MOD_SUB_MOBILE_PHOTO", "دوره عکاسی با موبایل در کرج"),
    "VIDEOGRAPHY": ("MOD_SUB_VIDEOGRAPHY", "آموزش عکاسی و فیلمبرداری در کرج"),
    "KIDS_MAKEUP": ("MOD_SUB_KIDS_MAKEUP", "آموزش گریم کودک در کرج"),
    "CINEMATIC_MAKEUP": ("MOD_SUB_CINEMATIC_MAKEUP", "آموزش گریم سینمایی در کرج"),
    "BEAUTY_MAKEUP": ("MOD_SUB_BEAUTY_MAKEUP", "آموزش میکاپ و گریم تخصصی در کرج"),
    "STAGE_HOSTING": ("MOD_SUB_STAGE_HOSTING", "کلاس مجری‌گری استیج و تلویزیون در کرج"),
    "DUBBING": ("MOD_SUB_DUBBING", "آموزش دوبلاژ، دوبله و دوبلوری در کرج"),
    "SCREENWRITING": ("MOD_SUB_SCREENWRITING", "کلاس فیلمنامه‌نویسی در کرج"),
    "DIRECTING": ("MOD_SUB_DIRECTING", "کلاس کارگردانی سینما در کرج"),
    "MUSIC_THEORY": ("MOD_SUB_MUSIC_THEORY", "آموزش تئوری موسیقی و سلفژ در کرج"),
    "VIDEO_EDITING_REELS": ("MOD_SUB_EDIT_REELS", "کلاس ادیت ویدیو و ریلز در کرج"),
    "KHAT_TAHRIRI": ("MOD_SUB_KHATATI", "کلاس خطاطی در کرج"),
    "DAF_ZANI": ("MOD_SUB_DAF_ZANI", "کلاس دف‌زنی در کرج"),
}


# Head-term overrides: where several stems co-exist in one silo, the Persian
# head term (highest demand + broadest stem) is locked as the page primary.
PRIMARY_OVERRIDE = {
    "SILO_CRS_CALLIGRAPHY": "کلاس خوشنویسی در کرج",
    "SILO_CRS_VOICE_DUBBING": "کلاس گویندگی در کرج",
    "SILO_CRS_FILM_EDITING": "کلاس تدوین در کرج",
    "SILO_CRS_KIDS_ACTING": "کلاس بازیگری کودکان در کرج",
    "SILO_CRS_KIDS_MUSIC": "آموزشگاه موسیقی کودک کرج",
    "SILO_CAFE_01": "کافه پیانو کرج",
    "SILO_GEO_FARDIS": "کلاس موسیقی در فردیس کرج",
    "SILO_CRS_TAR_SETAR": "کلاس سه تار کرج",
}


def pick_primary(records, fallback="", silo_id=None):
    """Highest-commercial-value keyword of a silo (never an orthographic typo variant)."""
    if not records:
        return fallback, []
    def score(r):
        n, s = r["normalized_keyword"], 0
        if r["orthographic_variant"]:
            s -= 8
        if re.search(r"(?<![\u0600-\u06FF])کلاس", n):
            s += 4
        if "در کرج" in n:
            s += 3
        elif "کرج" in n:
            s += 2
        if r["intent_vector"] == "COURSE_ENROLLMENT":
            s += 3
        if r["intent_vector"] in ("CAFE_LIVE_MUSIC", "AUDITION_TEST"):
            s += 3
        if "بهترین" in n or "خوب" in n:
            s -= 2
        if any(x in n for x in ("قیمت", "شهریه", "هزینه", "آدرس", "کجاست")):
            s -= 3
        s -= len(n) / 100.0
        return s
    ordered = sorted(records, key=score, reverse=True)
    primary = ordered[0]["raw_keyword"]
    override = PRIMARY_OVERRIDE.get(silo_id or "")
    if override and any(r["raw_keyword"] == override for r in records):
        primary = override
    secondary = [r["raw_keyword"] for r in ordered if r["raw_keyword"] != primary]
    return primary, secondary


def count_words(text):
    return len([w for w in re.split(r"\s+", text.strip()) if w])


def bluf_for_course(c, kws, instr_verified, female_ok):
    """Builds a Persian BLUF answer inside the mandatory 40-55 word window."""
    name = (c["name_fa"].replace("کلاس و آموزش ", "").replace("کلاس آموزش ", "")
            .replace("آموزشگاه و کلاس ", "").replace("کلاس ", ""))
    formats = []
    if "private" in c["formats_offered"]:
        formats.append("خصوصی")
    if "group" in c["formats_offered"]:
        formats.append("گروهی")
    ages = []
    if "kids" in c["age_groups"]:
        ages.append("کودکان")
    if "teens" in c["age_groups"]:
        ages.append("نوجوانان")
    if "adults" in c["age_groups"]:
        ages.append("بزرگسالان")
    t_group = L.irr_to_toman_fa(c["tuition_group_irr"])
    t_priv = L.irr_to_toman_fa(c["tuition_private_irr"])
    teachers = "اساتید مجرب خانم و آقا" if female_ok else "اساتید مجرب"

    clauses = [
        f"کلاس {name} در کرج در آموزشگاه سینمایی و بازیگری آنک با {teachers} و به‌صورت "
        f"{' و '.join(formats)} ویژه {'، '.join(ages)} برگزار می‌شود.",
        f"هر ترم {L.to_persian_digits(c['sessions_per_term'])} جلسه "
        f"{L.to_persian_digits(c['session_duration_min'])} دقیقه‌ای است"
        + (f" و شهریه گروهی از {t_group} تومان و خصوصی از {t_priv} تومان شروع می‌شود." if t_group and t_priv else "."),
        f"پایان دوره {c['certificate_type']} ارائه می‌شود.",
        "مشاوره و تعیین سطح رایگان است؛ پردیس مرکزی کرج، ۵ دقیقه تا مترو و دسترسی مستقیم از فردیس.",
    ]
    text = ""
    for cl in clauses:
        candidate = (text + " " + cl).strip()
        if count_words(candidate) > 55 and count_words(text) >= 40:
            break
        text = candidate
    # top-up if still short
    extras = ["ثبت‌نام حضوری و واتساپی انجام می‌شود.", "ظرفیت هر ترم محدود است."]
    i = 0
    while count_words(text) < 40 and i < len(extras):
        text = (text + " " + extras[i]).strip()
        i += 1
    return re.sub(r"\s+", " ", text).strip()


def main():
    L.ensure_dirs(L.OUTPUT)
    profile = L.academy_profile()
    courses = L.load_course_index()
    instructors = L.load_instructors()
    cafe_events = L.load_cafe_events()
    raw_keywords = L.load_keywords()
    records = [L.classify_keyword(k) for k in raw_keywords]
    reg = L.silo_registry(records)
    kmap = L.read_json(os.path.join(L.OUTPUT, "academy_keyword_map.json"), {})
    f_status = L.fardis_status(profile)
    serp = L.load_serp_matrix()

    fardis_slugs = kmap.get("fardis_geo_mapping", {}).get("demanded_courses_in_fardis", [])
    cafe_slugs = [slug for _, _, slug, _, _ in L.CAFE_INSTRUMENTS]

    pages = []
    links_to = defaultdict(list)

    def add_link(a, b):
        if b not in links_to[a] and a != b:
            links_to[a].append(b)

    dept_children = defaultdict(list)
    for cid, c in courses.items():
        dept_children[c["department_id"]].append(c)

    # ----------------------------------------------------------- TIER 0 HOME
    home_secondary = [r["raw_keyword"] for r in records if r["section_target"] == "SEC_CAMPUS_MAP_DIRECTIONS"]
    pages.append({
        "page_id": "HOME_ROOT", "tier": "0", "url_slug": "/", "build_status": "BUILD_HOME_MASTER",
        "silo_id": "SILO_00", "department_id": None, "course_id": None,
        "primary_keyword": profile["brand_fa"],
        "primary_keyword_source": "DERIVED_BRAND_TAXONOMY (academy_data.txt → BRAND_NAME)",
        "secondary_keywords": [],
        "dual_intent_supporting_keywords": home_secondary,
        "owned_dataset_keyword_count": 0,
        "orthographic_variants_assigned": [],
        "user_task": "انتخاب دانشکده/دوره مناسب از میان ۲۴ رشته، مشاهده کافه هنر، ثبت‌نام تست بازیگری و یافتن آدرس پردیس کرج در یک کلیک.",
        "search_intent": "brand_navigational_and_discovery", "funnel_stage": "awareness",
        "catalog_support": {"course_verified": True, "instructor_ids": [i["instructor_id"] for i in instructors if not L.is_placeholder_instructor(i)],
                            "cafe_verified": bool(profile["cafe_lines"]), "fardis_status": f_status},
        "required_onpage_modules": ["SEC_HOME_HERO_MULTIFACULTY", "SEC_COURSE_FINDER_24", "SEC_ART_CAFE_SHOWCASE",
                                    "SEC_FEATURED_INSTRUCTORS", "SEC_LICENSES_AND_FACILITIES",
                                    "SEC_CAMPUS_MAP_DIRECTIONS", "SEC_FARDIS_COMMUTER_ACCESS", "SEC_HOME_FAQ"],
        "information_gain_delta": {
            "unique_curriculum_facts": [f"۴ دانشکده و {L.to_persian_digits(len(courses))} دوره فعال",
                                        f"{L.to_persian_digits(len(cafe_events))} شب اجرای زنده تأییدشده در کافه هنر"],
            "unique_equipment_or_studio": profile["guarantees"][:2],
            "gain_score": "HIGH", "gain_percentage_estimate": 85},
        "serp_and_ai_targets": {
            "bluf_answer_target": (
                f"{profile['brand_fa']} با {profile['years_in_operation']} سابقه رسمی، در "
                f"{L.to_persian_digits(len(courses))} رشته موسیقی، بازیگری، فن بیان، گویندگی، عکاسی، تدوین، گریم، "
                "نقاشی و خوشنویسی در کرج آموزش می‌دهد و کافه هنر و موسیقی زنده اختصاصی دارد. "
                "مشاوره و تعیین سطح رایگان است و دسترسی مستقیم از فردیس، ملارد و تهران وجود دارد."),
            "featured_snippet_format": "multi_faculty_entity_summary"},
        "schema_types_planned": ["WebSite", "WebPage", "EducationalOrganization", "MusicSchool",
                                 "PerformingArtsTheater", "LocalBusiness", "CafeOrCoffeeShop", "BreadcrumbList"],
    })

    # -------------------------------------------------------- TIER 1 DEPT HUBS
    for dkey, d in L.DEPARTMENTS.items():
        s = reg[d["silo_id"]]
        primary, secondary = pick_primary(s["keywords"], fallback=d["title_fa"], silo_id=d["silo_id"])
        kids_music_slug = "/music/kids/"
        mods = ["SEC_HERO_BLUF_OVERVIEW", "SEC_COURSE_GRID_NAVIGATION", "SEC_TUITION_TABLE",
                "SEC_INSTRUCTOR_ROSTER", "SEC_CAMPUS_MAP_DIRECTIONS", "SEC_DEPT_FAQ"]
        if dkey == "DEPT_MUSIC":
            mods[2:2] = ["MOD_INST_GRID", "MOD_MUSIC_TUITION_MATRIX", "MOD_MUSIC_THEORY_SOLFEGE",
                         "MOD_CAFE_STAGE_CALLOUT"]
            mods.append("SEC_FARDIS_COMMUTER_ACCESS")
        if dkey == "DEPT_PERFORMING":
            mods.append("SEC_AUDITION_BRIDGE")
        pages.append({
            "page_id": f"{dkey}_HUB", "tier": "1", "url_slug": d["slug"],
            "build_status": "BUILD_DEPARTMENT_HUB" if s["keywords"] else "BUILD_DEPARTMENT_HUB_NAVIGATIONAL",
            "silo_id": d["silo_id"], "department_id": dkey, "course_id": None,
            "primary_keyword": primary,
            "primary_keyword_source": "DATASET" if s["keywords"] else "DERIVED_BRAND_TAXONOMY",
            "secondary_keywords": secondary,
            "owned_dataset_keyword_count": len({r['raw_keyword'] for r in s['keywords']}),
            "orthographic_variants_assigned": [r["raw_keyword"] for r in s["keywords"] if r["orthographic_variant"]],
            "user_task": f"مقایسه همه دوره‌های {d['name_fa']} در کرج، دیدن شهریه و اساتید و انتخاب رشته.",
            "search_intent": "category_commercial_investigation", "funnel_stage": "consideration",
            "catalog_support": {"course_verified": True,
                                "child_course_ids": [c["course_id"] for c in dept_children[dkey]],
                                "tuition_verified": all(c["tuition_private_irr"] > 0 for c in dept_children[dkey])},
            "required_onpage_modules": mods,
            "information_gain_delta": {
                "unique_curriculum_facts": [f"جدول مقایسه شهریه {L.to_persian_digits(len(dept_children[dkey]))} دوره در یک صفحه"],
                "unique_equipment_or_studio": [], "gain_score": "HIGH", "gain_percentage_estimate": 75},
            "serp_and_ai_targets": {
                "bluf_answer_target": "",
                "featured_snippet_format": "course_comparison_table"},
            "schema_types_planned": ["WebPage", "CollectionPage", "BreadcrumbList", "ItemList", "FAQPage"],
            "_children": [c["slug"] for c in dept_children[dkey]] + ([kids_music_slug] if dkey == "DEPT_MUSIC" else []),
        })

    # ------------------------------------------------------- TIER 2 COURSES
    for cid, c in courses.items():
        s = reg[c["silo_id"]]
        kws = s["keywords"]
        primary, secondary = pick_primary(kws, fallback=c["name_fa"] + " در کرج", silo_id=c["silo_id"])
        intent = Counter(r["intent_vector"] for r in kws)
        sections = Counter(r["section_target"] for r in kws)
        instrs = L.instructors_for(cid, instructors)
        verified = [i for i in instrs if not L.is_placeholder_instructor(i)]
        pending = [i for i in instrs if L.is_placeholder_instructor(i)]
        female_ok = c["has_female_instructor"]
        subs = sorted({x for r in kws for x in r["sub_specialties"]})

        mods = ["SEC_HERO_BLUF_OVERVIEW", "SEC_INSTRUCTOR_ROSTER"]
        if intent.get("FEMALE_SPECIFIC", 0) or female_ok:
            mods.append("SEC_FEMALE_INSTRUCTORS")
        mods.append("SEC_PRIVATE_VS_GROUP_FORMAT")
        sub_modules = []
        for sname in subs:
            if sname in SUB_MODULE_LABELS:
                sub_modules.append(SUB_MODULE_LABELS[sname][0])
        if not sub_modules and c["sub_specialties_fa"]:
            sub_modules.append("MOD_SUB_STYLE_TRACKS")
        if sub_modules:
            mods.append("SEC_SUBSTYLE_TABS")
        if "kids" in c["age_groups"] or intent.get("KIDS_TEENS_SPECIFIC", 0):
            mods.append("SEC_KIDS_TEENS_TRACK")
        mods += ["SEC_TUITION_TABLE", "SEC_SYLLABUS_ROADMAP"]
        if c["performed_in_cafe"]:
            mods.append("SEC_CAFE_PERFORMANCE_BRIDGE")
        if c["slug"] in fardis_slugs or c["fardis_high_demand"]:
            mods.append("SEC_FARDIS_COMMUTER_ACCESS")
        if cid in ("CRS_ACTING", "CRS_KIDS_ACTING"):
            mods.append("SEC_AUDITION_BRIDGE")
        mods += ["SEC_CAMPUS_MAP_DIRECTIONS", "SEC_COURSE_FAQ"]

        unique_facts = list(c["sub_specialties_fa"])
        gain = 40
        gain += 6 if c["sub_specialties_fa"] else 0
        gain += 6 if c["tuition_private_irr"] > 0 else 0
        gain += 8 if verified else 0
        gain += 6 if c["performed_in_cafe"] else 0
        gain += 5 if "SEC_FARDIS_COMMUTER_ACCESS" in mods else 0
        gain += 6 if sub_modules else 0
        gain += 5 if c["certificate_type"] else 0
        gain += 5 if "kids" in c["age_groups"] else 0
        gain = min(gain, 95)

        pages.append({
            "page_id": cid, "tier": "2", "url_slug": c["slug"],
            "build_status": "BUILD_COURSE_MEGA" if len(kws) >= 10 else "BUILD_COURSE_STANDARD",
            "silo_id": c["silo_id"], "department_id": c["department_id"], "course_id": cid,
            "primary_keyword": primary, "primary_keyword_source": "DATASET" if kws else "DERIVED",
            "secondary_keywords": secondary,
            "owned_dataset_keyword_count": len({r["raw_keyword"] for r in kws}),
            "orthographic_variants_assigned": [r["raw_keyword"] for r in kws if r["orthographic_variant"]],
            "user_task": (f"مقایسه اساتید (از جمله استاد خانم)، فرمت خصوصی/گروهی، مسیر کودکان و بزرگسالان و "
                          f"شهریه شفاف {c['name_fa']} در کرج و رزرو جلسه تعیین سطح رایگان."),
            "search_intent": "transactional_enrollment", "funnel_stage": "decision",
            "catalog_support": {
                "course_verified": c["status"] == "active",
                "instructor_ids": [i["instructor_id"] for i in verified],
                "pending_instructor_placeholders": [i["instructor_id"] for i in pending],
                "has_female_instructor": female_ok,
                "female_instructor_name_verified": any(i["gender"] == "female" for i in verified),
                "has_private_classes": "private" in c["formats_offered"],
                "has_group_classes": "group" in c["formats_offered"],
                "has_kids_track": "kids" in c["age_groups"],
                "tuition_verified": c["tuition_private_irr"] > 0,
                "performed_in_art_cafe": c["performed_in_cafe"],
                "fardis_demand_linked": c["slug"] in fardis_slugs or c["fardis_high_demand"],
            },
            "required_onpage_modules": mods,
            "sub_specialty_modules": [{"module_id": SUB_MODULE_LABELS[x][0], "heading_fa": SUB_MODULE_LABELS[x][1],
                                       "keywords": [r["raw_keyword"] for r in kws if x in r["sub_specialties"]]}
                                      for x in subs if x in SUB_MODULE_LABELS],
            "section_target_breakdown": dict(sections),
            "information_gain_delta": {
                "unique_curriculum_facts": unique_facts,
                "unique_equipment_or_studio": [c["certificate_type"]] if c["certificate_type"] else [],
                "gain_score": "HIGH" if gain >= 70 else ("MEDIUM" if gain >= 30 else "LOW"),
                "gain_percentage_estimate": gain},
            "serp_and_ai_targets": {
                "bluf_answer_target": bluf_for_course(c, kws, verified, female_ok),
                "featured_snippet_format": "tuition_and_format_comparison_table"},
            "schema_types_planned": ["WebPage", "Course", "CourseInstance", "Person (Instructors)",
                                     "FAQPage", "BreadcrumbList"] + (
                                        ["Offer"] if c["tuition_private_irr"] > 0 else []),
        })

    # ------------------------------------------------------- TIER 3 ART CAFE
    cafe_kws = reg["SILO_CAFE_01"]["keywords"]
    cafe_primary, cafe_secondary = pick_primary(cafe_kws, "کافه پیانو کرج", silo_id="SILO_CAFE_01")
    pages.append({
        "page_id": "CAFE_VENUE_HUB", "tier": "3", "url_slug": "/art-cafe/", "build_status": "BUILD_VENUE_HUB",
        "silo_id": "SILO_CAFE_01", "department_id": None, "course_id": None,
        "primary_keyword": cafe_primary, "primary_keyword_source": "DATASET",
        "secondary_keywords": cafe_secondary,
        "owned_dataset_keyword_count": len(cafe_kws),
        "orthographic_variants_assigned": [],
        "user_task": "دیدن برنامه شب‌های اجرای زنده پیانو، گیتار، سنتور، سه‌تار و ارگ و رزرو میز در کافه هنر آنک کرج.",
        "search_intent": "local_hospitality_live_music", "funnel_stage": "consideration",
        "catalog_support": {"cafe_verified": bool(profile["cafe_lines"]),
                            "verified_event_ids": [e["event_id"] for e in cafe_events],
                            "menu_verified": False,
                            "menu_status": "[INTERNAL_DATA_NEEDED]"},
        "required_onpage_modules": ["SEC_CAFE_HERO", "SEC_LIVE_NIGHTS_BY_INSTRUMENT", "SEC_CAFE_MENU",
                                    "SEC_STUDENT_RECITAL_STAGE", "SEC_CAFE_RESERVATION_MAP", "SEC_CAFE_FAQ"],
        "cafe_instrument_blocks": [
            {"anchor": anchor, "section_id": sec, "instrument_fa": fa, "linked_course_slug": slug,
             "keywords": [r["raw_keyword"] for r in cafe_kws if fa in r["normalized_keyword"]],
             "verified_events": [e for e in cafe_events
                                 if fa.replace(" ", "") in e["instrument_focus_fa"].replace("‌", "").replace(" ", "")]}
            for fa, sec, slug, cid, anchor in L.CAFE_INSTRUMENTS],
        "information_gain_delta": {
            "unique_curriculum_facts": [f"{L.to_persian_digits(len(cafe_events))} شب اجرای زنده تأییدشده با نام نوازنده و ساعت دقیق"],
            "unique_equipment_or_studio": profile["cafe_lines"],
            "gain_score": "HIGH", "gain_percentage_estimate": 80},
        "serp_and_ai_targets": {
            "bluf_answer_target": (
                "کافه هنر و موسیقی آموزشگاه آنک در کرج، فضای کافه هنری داخل مجموعه است که میزبان اجرای زنده "
                "پیانو، گیتار، سنتور، سه‌تار و ارگ توسط اساتید و هنرجویان است؛ رزرو میز شب‌های موسیقی زنده با "
                "تماس یا واتساپ و دسترسی از مرکز کرج و فردیس."),
            "featured_snippet_format": "weekly_live_music_schedule_table"},
        "schema_types_planned": ["WebPage", "CafeOrCoffeeShop", "EventVenue", "MusicEvent", "BreadcrumbList", "FAQPage"],
    })

    # ------------------------------------------- TIER 4 LOCAL & CONVERSION HUBS
    fardis_kws = reg["SILO_GEO_FARDIS"]["keywords"]
    f_primary, f_secondary = pick_primary(fardis_kws, "کلاس موسیقی در فردیس کرج", silo_id="SILO_GEO_FARDIS")
    pages.append({
        "page_id": "GEO_FARDIS_HUB", "tier": "4", "url_slug": "/fardis-branch/", "build_status": "BUILD_HYPERLOCAL_HUB",
        "silo_id": "SILO_GEO_FARDIS", "department_id": None, "course_id": None,
        "primary_keyword": f_primary, "primary_keyword_source": "DATASET", "secondary_keywords": f_secondary,
        "owned_dataset_keyword_count": len(fardis_kws),
        "orthographic_variants_assigned": [r["raw_keyword"] for r in fardis_kws if r["orthographic_variant"]],
        "user_task": "فهمیدن دقیق مسیر و زمان رسیدن از فردیس به پردیس کرج، دیدن ۷ رشته پرتقاضای فردیس و شیفت‌های فشرده آخر هفته.",
        "search_intent": "hyperlocal_commercial", "funnel_stage": "decision",
        "catalog_support": {"fardis_campus_status": f_status,
                            "nap_rule": "NEVER_EMIT_FARDIS_STREET_ADDRESS" if f_status == "SERVICE_AREA_COMMUTER_HUB" else "EMIT_BRANCH_NAP",
                            "verified_transit_routes": len(profile["transit_routes"])},
        "required_onpage_modules": ["SEC_FARDIS_HERO", "SEC_FARDIS_DEMANDED_PROGRAMS", "SEC_FARDIS_ROUTE_MATRIX",
                                    "SEC_FARDIS_WEEKEND_COMPACT_SHIFTS", "SEC_CAMPUS_MAP_DIRECTIONS", "SEC_FARDIS_FAQ"],
        "fardis_program_cards": [{"course_slug": slug,
                                  "keywords": [x["keyword"] for x in kmap["fardis_geo_mapping"]["dual_intent_routes"]
                                               if x["course_slug"] == slug]}
                                 for slug in fardis_slugs],
        "information_gain_delta": {
            "unique_curriculum_facts": [f"{L.to_persian_digits(len(profile['transit_routes']))} مسیر رفت‌وآمد تأییدشده از academy_data.txt"],
            "unique_equipment_or_studio": [], "gain_score": "HIGH", "gain_percentage_estimate": 72},
        "serp_and_ai_targets": {
            "bluf_answer_target": (
                "هنرجویان فردیس کرج با مترو کرج تنها ۵ دقیقه پیاده تا پردیس مرکزی آموزشگاه سینمایی و بازیگری "
                "آنک فاصله دارند. کلاس موسیقی، موسیقی کودک، آواز و خوانندگی، بازیگری، فن بیان، گویندگی و "
                "خوشنویسی با شیفت‌های فشرده پنجشنبه و جمعه ویژه هنرجویان فردیس برگزار می‌شود و مشاوره و "
                "تعیین سطح آن رایگان است."),
            "featured_snippet_format": "commuter_route_and_time_matrix"},
        "schema_types_planned": ["WebPage", "BreadcrumbList", "FAQPage"],
    })

    aud_kws = reg["SILO_CONV_AUDITION"]["keywords"]
    a_primary, a_secondary = pick_primary(aud_kws, "تست بازیگری در کرج", silo_id="SILO_CONV_AUDITION")
    pages.append({
        "page_id": "CONV_AUDITION_HUB", "tier": "4", "url_slug": "/acting-audition/", "build_status": "BUILD_CONVERSION_HUB",
        "silo_id": "SILO_CONV_AUDITION", "department_id": "DEPT_PERFORMING", "course_id": None,
        "primary_keyword": a_primary, "primary_keyword_source": "DATASET", "secondary_keywords": a_secondary,
        "owned_dataset_keyword_count": len(aud_kws), "orthographic_variants_assigned": [],
        "user_task": "فهمیدن اینکه تست بازیگری در کرج کجاست، چه مراحلی دارد و رزرو نوبت تست و تعیین سطح.",
        "search_intent": "action_audition_booking", "funnel_stage": "decision",
        "catalog_support": {"judging_faculty": [i["instructor_id"] for i in instructors
                                                if not L.is_placeholder_instructor(i)
                                                and ("CRS_ACTING" in i["course_ids"] or "CRS_KIDS_ACTING" in i["course_ids"])]},
        "required_onpage_modules": ["SEC_AUDITION_HERO", "SEC_AUDITION_PROCESS_STEPS", "SEC_AUDITION_AGE_CRITERIA",
                                    "SEC_AUDITION_PREP_GUIDE", "SEC_JUDGING_PANEL", "SEC_AUDITION_BOOKING_FORM",
                                    "SEC_CAMPUS_MAP_DIRECTIONS", "SEC_AUDITION_FAQ"],
        "information_gain_delta": {
            "unique_curriculum_facts": ["۴ مرحله تست و تعیین سطح با داوری اساتید تأییدشده بازیگری"],
            "unique_equipment_or_studio": [], "gain_score": "HIGH", "gain_percentage_estimate": 70},
        "serp_and_ai_targets": {
            "bluf_answer_target": (
                "تست بازیگری در کرج در پردیس آموزشگاه سینمایی و بازیگری آنک، خیابان دانشکده جنوبی روبروی "
                "کتابخانه امیرکبیر برگزار می‌شود؛ شامل مصاحبه اولیه، اجرای مونولوگ، تست مقابل دوربین و "
                "تعیین سطح رایگان برای کودکان، نوجوانان و بزرگسالان با داوری اساتید تأییدشده بازیگری و "
                "امکان رزرو نوبت با واتساپ."),
            "featured_snippet_format": "step_by_step_audition_process"},
        "schema_types_planned": ["WebPage", "BreadcrumbList", "FAQPage", "Event"],
    })

    pages.append({
        "page_id": "HUB_INSTRUCTORS", "tier": "4", "url_slug": "/instructors/", "build_status": "BUILD_TRUST_HUB",
        "silo_id": "SILO_00", "department_id": None, "course_id": None,
        "primary_keyword": "اساتید آموزشگاه آنک کرج", "primary_keyword_source": "DERIVED_BRAND_TAXONOMY",
        "secondary_keywords": [], "owned_dataset_keyword_count": 0, "orthographic_variants_assigned": [],
        "user_task": "بررسی سوابق، مدارک و رشته تدریس همه اساتید و انتخاب استاد مناسب (خانم/آقا).",
        "search_intent": "trust_eeat", "funnel_stage": "consideration",
        "catalog_support": {"verified_instructors": [i["instructor_id"] for i in instructors if not L.is_placeholder_instructor(i)],
                            "pending_placeholders": [i["instructor_id"] for i in instructors if L.is_placeholder_instructor(i)]},
        "required_onpage_modules": ["SEC_INSTRUCTOR_ROSTER", "SEC_FEMALE_INSTRUCTORS", "SEC_INSTRUCTOR_FILTERS"],
        "information_gain_delta": {"unique_curriculum_facts": ["مدارک و افتخارات verbatim از instructors.csv"],
                                   "unique_equipment_or_studio": [], "gain_score": "MEDIUM", "gain_percentage_estimate": 60},
        "serp_and_ai_targets": {"bluf_answer_target": "", "featured_snippet_format": "faculty_directory"},
        "schema_types_planned": ["WebPage", "CollectionPage", "Person", "BreadcrumbList"],
    })

    pages.append({
        "page_id": "HUB_CONTACT", "tier": "4", "url_slug": "/contact/", "build_status": "BUILD_CONTACT_HUB",
        "silo_id": "SILO_00", "department_id": None, "course_id": None,
        "primary_keyword": "آدرس و تماس آموزشگاه آنک کرج", "primary_keyword_source": "DERIVED_BRAND_TAXONOMY",
        "secondary_keywords": [], "owned_dataset_keyword_count": 0, "orthographic_variants_assigned": [],
        "user_task": "یافتن آدرس دقیق، ساعات کاری، مسیر مترو/خودرو و تماس فوری یا واتساپ برای ثبت‌نام.",
        "search_intent": "local_contact", "funnel_stage": "decision",
        "catalog_support": {"nap_verified": True},
        "required_onpage_modules": ["SEC_CAMPUS_MAP_DIRECTIONS", "SEC_CONTACT_CHANNELS", "SEC_OPENING_HOURS",
                                    "SEC_FARDIS_COMMUTER_ACCESS", "SEC_TUITION_TABLE"],
        "information_gain_delta": {"unique_curriculum_facts": profile["landmarks"],
                                   "unique_equipment_or_studio": [], "gain_score": "MEDIUM", "gain_percentage_estimate": 55},
        "serp_and_ai_targets": {"bluf_answer_target": "", "featured_snippet_format": "nap_and_hours_card"},
        "schema_types_planned": ["WebPage", "ContactPage", "LocalBusiness", "BreadcrumbList"],
    })

    # --------------------------------------------------- INTERNAL LINK GRAPH
    by_slug = {p["url_slug"]: p for p in pages}
    course_slugs = [c["slug"] for c in courses.values()]

    for d in L.DEPARTMENTS.values():
        add_link("/", d["slug"])
    for extra in ("/art-cafe/", "/acting-audition/", "/fardis-branch/", "/instructors/", "/contact/"):
        add_link("/", extra)
    for cs in course_slugs:
        add_link("/", cs)  # homepage 24-course finder grid → click depth 1

    for dkey, d in L.DEPARTMENTS.items():
        add_link(d["slug"], "/")
        for c in dept_children[dkey]:
            add_link(d["slug"], c["slug"])
        add_link(d["slug"], "/instructors/")
        add_link(d["slug"], "/contact/")
        if dkey == "DEPT_MUSIC":
            add_link(d["slug"], "/art-cafe/")
            add_link(d["slug"], "/fardis-branch/")
        if dkey == "DEPT_PERFORMING":
            add_link(d["slug"], "/acting-audition/")
            add_link(d["slug"], "/fardis-branch/")

    for dkey, kids in dept_children.items():
        hub = L.DEPARTMENTS[dkey]["slug"]
        n = len(kids)
        for i, c in enumerate(kids):
            add_link(c["slug"], hub)
            add_link(c["slug"], kids[(i + 1) % n]["slug"])
            add_link(c["slug"], kids[(i + 2) % n]["slug"])
            add_link(c["slug"], "/instructors/")
            add_link(c["slug"], "/contact/")
            if c["performed_in_cafe"]:
                add_link(c["slug"], "/art-cafe/")
            if c["slug"] in fardis_slugs or c["fardis_high_demand"]:
                add_link(c["slug"], "/fardis-branch/")
            if c["course_id"] in ("CRS_ACTING", "CRS_KIDS_ACTING"):
                add_link(c["slug"], "/acting-audition/")
            if c["course_id"] in ("CRS_PIANO", "CRS_VOCALS", "CRS_VIOLIN", "CRS_GUITAR"):
                add_link(c["slug"], "/music/kids/")

    for fa, sec, slug, cid, anchor in L.CAFE_INSTRUMENTS:
        add_link("/art-cafe/", slug)
    add_link("/art-cafe/", "/music/")
    add_link("/art-cafe/", "/")
    add_link("/art-cafe/", "/contact/")

    for slug in fardis_slugs:
        add_link("/fardis-branch/", slug)
    add_link("/fardis-branch/", "/")
    add_link("/fardis-branch/", "/contact/")

    for slug in ("/performing-arts/acting/", "/performing-arts/kids-acting-drama/", "/performing-arts/", "/instructors/"):
        add_link("/acting-audition/", slug)

    for d in L.DEPARTMENTS.values():
        add_link("/instructors/", d["slug"])
    add_link("/instructors/", "/")
    add_link("/instructors/", "/contact/")

    for slug in ("/", "/fardis-branch/", "/art-cafe/", "/acting-audition/", "/instructors/"):
        add_link("/contact/", slug)

    links_from = defaultdict(list)
    for src, targets in links_to.items():
        for t in targets:
            links_from[t].append(src)

    for p in pages:
        p["internal_links_to"] = sorted(links_to[p["url_slug"]])
        p["internal_links_from"] = sorted(links_from[p["url_slug"]])
        p.pop("_children", None)

    # click depth
    depth = {"/": 0}
    frontier = ["/"]
    while frontier:
        nxt = []
        for s in frontier:
            for t in links_to[s]:
                if t not in depth:
                    depth[t] = depth[s] + 1
                    nxt.append(t)
        frontier = nxt
    for p in pages:
        p["click_depth_from_home"] = depth.get(p["url_slug"], 99)

    # ------------------------------------------------------- ACCOUNTABILITY
    tier_kw = Counter()
    assigned = set()
    for p in pages:
        n = p["owned_dataset_keyword_count"]
        tier_kw[p["tier"]] += n
    for r in records:
        assigned.add(r["raw_keyword"])

    orphan_warnings = [p["url_slug"] for p in pages
                       if len(p["internal_links_from"]) < 2 or len(p["internal_links_to"]) < 2]
    cannibal_warnings = []
    seen_primary = {}
    for p in pages:
        pk = L.normalize_persian(p["primary_keyword"])
        if pk in seen_primary:
            cannibal_warnings.append({"keyword": p["primary_keyword"],
                                      "pages": [seen_primary[pk], p["url_slug"]]})
        seen_primary[pk] = p["url_slug"]

    page_map = {
        "generated_at": L.now_iso(),
        "phase": "PHASE_2",
        "domain": profile["domain"],
        "serp_evidence_mode": serp.get("serp_evidence_mode", "NOT_PROVIDED"),
        "total_raw_keyword_lines": len(raw_keywords),
        "total_distinct_keywords": len(assigned),
        "total_buildable_pages": len(pages),
        "tier_summary": {
            "tier_0_home": sum(1 for p in pages if p["tier"] == "0"),
            "tier_1_department_hubs": sum(1 for p in pages if p["tier"] == "1"),
            "tier_2_course_pages": sum(1 for p in pages if p["tier"] == "2"),
            "tier_3_art_cafe_hub": sum(1 for p in pages if p["tier"] == "3"),
            "tier_4_local_and_conversion_hubs": sum(1 for p in pages if p["tier"] == "4"),
            "tier_5_editorial_guides": 0,
            "excluded_unserved_courses": 0,
        },
        "pages": pages,
        "keyword_accountability": {
            "tier_0_home": tier_kw["0"], "tier_1_department_hubs": tier_kw["1"],
            "tier_2_course_pages": tier_kw["2"], "tier_3_art_cafe": tier_kw["3"],
            "tier_4_fardis_and_audition": tier_kw["4"], "tier_5_editorial": 0,
            "excluded_unserved": 0,
            "total_keywords_accounted": sum(tier_kw.values()),
            "total_distinct_keywords": len(assigned),
            "balanced": sum(tier_kw.values()) == len(assigned),
        },
        "bidirectional_bridges": {
            "art_cafe": [{"cafe": "/art-cafe/", "course": slug,
                          "cafe_links_to_course": slug in links_to["/art-cafe/"],
                          "course_links_to_cafe": "/art-cafe/" in links_to[slug],
                          "course_has_bridge_module": "SEC_CAFE_PERFORMANCE_BRIDGE" in by_slug[slug]["required_onpage_modules"]}
                         for _, _, slug, _, _ in L.CAFE_INSTRUMENTS],
            "fardis": [{"hub": "/fardis-branch/", "course": slug,
                        "hub_links_to_course": slug in links_to["/fardis-branch/"],
                        "course_links_to_hub": "/fardis-branch/" in links_to[slug],
                        "course_has_module": "SEC_FARDIS_COMMUTER_ACCESS" in by_slug[slug]["required_onpage_modules"]}
                       for slug in fardis_slugs],
            "audition": [{"hub": "/acting-audition/", "course": slug,
                          "hub_links_to_course": slug in links_to["/acting-audition/"],
                          "course_links_to_hub": "/acting-audition/" in links_to[slug]}
                         for slug in ("/performing-arts/acting/", "/performing-arts/kids-acting-drama/")],
        },
        "orphan_page_warnings": orphan_warnings,
        "cannibalization_warnings": cannibal_warnings,
        "max_click_depth": max(p["click_depth_from_home"] for p in pages),
    }
    L.write_json(os.path.join(L.OUTPUT, "page_map.json"), page_map)

    b = page_map["bidirectional_bridges"]
    gates = {
        "G2_1_keyword_accountability_balanced": page_map["keyword_accountability"]["balanced"],
        "G2_2_zero_primary_cannibalization": len(cannibal_warnings) == 0,
        "G2_3_cafe_bidirectional_bridge": all(x["cafe_links_to_course"] and x["course_links_to_cafe"]
                                              and x["course_has_bridge_module"] for x in b["art_cafe"]),
        "G2_4_fardis_hub_and_course_bridge": all(x["hub_links_to_course"] and x["course_links_to_hub"]
                                                 and x["course_has_module"] for x in b["fardis"]),
        "G2_5_audition_bridge": all(x["hub_links_to_course"] and x["course_links_to_hub"] for x in b["audition"]),
        "G2_6_information_gain_min_30": all(p["information_gain_delta"]["gain_percentage_estimate"] >= 30
                                            and p["information_gain_delta"]["gain_score"] in ("HIGH", "MEDIUM")
                                            for p in pages),
        "G2_7_zero_orphan_pages": len(orphan_warnings) == 0,
    }
    L.update_progress("PHASE_2", "COMPLETE", ["output/page_map.json"], gates, "PHASE_3")

    print("=" * 74)
    print("UNIFIED PHASE 2 — COMPLETE")
    print("=" * 74)
    print(f"  buildable pages : {len(pages)}  {dict(page_map['tier_summary'])}")
    print(f"  keywords mapped : {page_map['keyword_accountability']['total_keywords_accounted']}/{len(assigned)}")
    print(f"  max click depth : {page_map['max_click_depth']}")
    print(f"  orphan warnings : {orphan_warnings}")
    for k, v in gates.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    return all(gates.values())


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
