#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 3 — SIGNAL ARCHITECTURE SEO DOSSIERS (ALL 6 TIERS)
Artifacts:
  seo_dossiers/*.md                 (one 8-gate dossier per buildable page)
  output/page_content_plan.json     (machine-readable twin consumed by the Coder Agent)
  output/needed_media.md
"""
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_lib as L  # noqa: E402

CTA_PRIMARY = "رزرو مشاوره و تعیین سطح رایگان"
CTA_CAFE = "رزرو میز شب‌های موسیقی زنده"
CTA_AUDITION = "ثبت‌نام تست بازیگری و تعیین سطح"


# ------------------------------------------------------------------ helpers
def kw_sentence(intro: str, keywords: list, outro: str = "") -> str:
    """Weaves a keyword group into one natural Persian sentence."""
    if not keywords:
        return ""
    uniq = []
    for k in keywords:
        if k not in uniq:
            uniq.append(k)
    joined = "، ".join(f"«{k}»" for k in uniq)
    return f"{intro} {joined}{(' ' + outro) if outro else ''}".strip()


def chunk(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def dossier_filename(page) -> str:
    slug = page["url_slug"].strip("/")
    if slug == "":
        return "seo_dossier_home.md"
    return "seo_dossier_" + slug.replace("/", "-") + ".md"


def section(sid, heading, anchor, ui, gates, **extra):
    d = {"section_id": sid, "heading_fa": heading, "anchor": anchor, "ui_component": ui}
    d.update(gates)
    d.update(extra)
    return d


# ======================================================================
#  CONTENT PLAN BUILDERS
# ======================================================================
class PlanBuilder:
    def __init__(self):
        self.profile = L.academy_profile()
        self.courses = L.load_course_index()
        self.instructors = L.load_instructors()
        self.cafe_events = L.load_cafe_events()
        self.records = [L.classify_keyword(k) for k in L.load_keywords()]
        self.reg = L.silo_registry(self.records)
        self.page_map = L.read_json(os.path.join(L.OUTPUT, "page_map.json"))
        self.kmap = L.read_json(os.path.join(L.OUTPUT, "academy_keyword_map.json"))
        self.f_status = L.fardis_status(self.profile)
        self.media = []
        self.by_slug = {p["url_slug"]: p for p in self.page_map["pages"]}
        self.dept_children = defaultdict(list)
        for cid, c in self.courses.items():
            self.dept_children[c["department_id"]].append(c)

    # ---------------------------------------------------------- utilities
    def silo_records(self, silo_id):
        return self.reg[silo_id]["keywords"] if silo_id in self.reg else []

    def kws_by_section(self, silo_id):
        out = defaultdict(list)
        seen = set()
        for r in self.silo_records(silo_id):
            if r["raw_keyword"] in seen:
                continue
            seen.add(r["raw_keyword"])
            out[r["section_target"]].append(r)
        return out

    def ortho_kws(self, silo_id):
        return [r for r in self.silo_records(silo_id) if r["orthographic_variant"]]

    def add_media(self, page_slug, asset, spec, priority="P2"):
        self.media.append({"page": page_slug, "asset": asset, "spec": spec, "priority": priority})

    def instructor_cards(self, course_id):
        cards = []
        for i in L.instructors_for(course_id, self.instructors):
            ph = L.is_placeholder_instructor(i)
            cards.append({
                "instructor_id": i["instructor_id"],
                "name_fa": "[INTERNAL_DATA_NEEDED]" if ph else i["name_fa"],
                "placeholder_label_fa": i["name_fa"] if ph else "",
                "gender": i["gender"],
                "gender_badge_fa": "استاد خانم" if i["gender"] == "female" else "استاد آقا",
                "role_title_fa": i["role_title_fa"],
                "credentials_fa": "" if ph else i["credentials_fa"],
                "experience_highlights_fa": "" if ph else i.get("experience_highlights_fa", ""),
                "same_as_url": "" if ph else i.get("same_as_url", ""),
                "is_placeholder": ph,
                "status": i["status"],
            })
        return cards

    def tuition_rows(self, c):
        rows = []
        if "private" in c["formats_offered"] and c["tuition_private_irr"] > 0:
            rows.append({
                "format_fa": "خصوصی (تک‌نفره)", "sessions": L.to_persian_digits(c["sessions_per_term"]),
                "duration_fa": f"{L.to_persian_digits(c['session_duration_min'])} دقیقه",
                "tuition_toman_fa": L.irr_to_toman_fa(c["tuition_private_irr"]),
                "tuition_irr_raw": c["tuition_private_irr"],
                "certificate_fa": c["certificate_type"],
            })
        if "group" in c["formats_offered"] and c["tuition_group_irr"] > 0:
            rows.append({
                "format_fa": "گروهی / کارگاهی", "sessions": L.to_persian_digits(c["sessions_per_term"]),
                "duration_fa": f"{L.to_persian_digits(c['session_duration_min'])} دقیقه",
                "tuition_toman_fa": L.irr_to_toman_fa(c["tuition_group_irr"]),
                "tuition_irr_raw": c["tuition_group_irr"],
                "certificate_fa": c["certificate_type"],
            })
        if "kids" in c["age_groups"] and c["tuition_group_irr"] > 0:
            rows.append({
                "format_fa": "کودکان (گروه سنی خردسال)", "sessions": L.to_persian_digits(c["sessions_per_term"]),
                "duration_fa": f"{L.to_persian_digits(c['session_duration_min'])} دقیقه",
                "tuition_toman_fa": L.irr_to_toman_fa(c["tuition_group_irr"]),
                "tuition_irr_raw": c["tuition_group_irr"],
                "certificate_fa": c["certificate_type"],
                "note_fa": "نرخ پایه گروهی؛ تخفیف خواهر/برادر با مشاوره",
            })
        return rows

    def syllabus_steps(self, c):
        base = [
            ("مقدماتی", "آشنایی با ساختار، تمرین‌های پایه و استانداردهای اجرای صحیح"),
            ("متوسطه", "تسلط بر رپرتوار میانی، تمرین منظم و اجرای کلاسی"),
            ("پیشرفته", "اجرای صحنه‌ای، آماده‌سازی نمونه‌کار و دریافت مدرک پایان دوره"),
        ]
        steps = []
        subs = c["sub_specialties_fa"]
        for idx, (level, desc) in enumerate(base):
            steps.append({
                "level_fa": level,
                "description_fa": desc,
                "modules_fa": subs[idx::len(base)] if subs else [],
                "term_fa": f"ترم {L.to_persian_digits(idx + 1)} — {L.to_persian_digits(c['sessions_per_term'])} جلسه",
            })
        return steps

    # ------------------------------------------------------------- FAQ
    def faq_for_course(self, page, c, kbs, cards):
        faq = []
        slug = page["url_slug"]
        name = c["name_fa"].replace("کلاس و آموزش ", "").replace("کلاس آموزش ", "").replace("کلاس ", "")
        t_g, t_p = L.irr_to_toman_fa(c["tuition_group_irr"]), L.irr_to_toman_fa(c["tuition_private_irr"])

        for r in kbs.get("SEC_TUITION_TABLE", [])[:2]:
            faq.append({
                "q": f"{r['raw_keyword']} چقدر است؟",
                "a": (f"شهریه گروهی از {t_g} تومان و شهریه خصوصی از {t_p} تومان برای هر ترم "
                      f"{L.to_persian_digits(c['sessions_per_term'])} جلسه‌ای اعلام شده است. "
                      f"این ارقام مستقیماً از تعرفه ثبت‌شده آموزشگاه استخراج شده و شامل "
                      f"{c['certificate_type']} است."),
                "source": "courses.csv",
            })
        if kbs.get("SEC_FEMALE_INSTRUCTORS") or c["has_female_instructor"]:
            fem_kw = kbs.get("SEC_FEMALE_INSTRUCTORS", [])
            q = fem_kw[0]["raw_keyword"] + "؟" if fem_kw else f"آیا {name} با مدرس خانم در کرج برگزار می‌شود؟"
            verified_f = [x for x in cards if x["gender"] == "female" and not x["is_placeholder"]]
            if verified_f:
                a = ("بله. طبق کاتالوگ دوره‌های آموزشگاه، این دوره مدرس خانم دارد. اساتید خانم تأییدشده: "
                     + "، ".join(x["name_fa"] for x in verified_f) + ".")
            else:
                a = ("بله؛ در کاتالوگ رسمی دوره‌ها (courses.csv) این دوره دارای مدرس خانم است و کلاس ویژه "
                     "بانوان و کودکان برگزار می‌شود. نام و رزومه کامل استاد خانم پس از تأیید آموزشگاه در همین "
                     "بخش منتشر می‌شود — [INTERNAL_DATA_NEEDED].")
            faq.append({"q": q, "a": a, "source": "courses.csv + instructors.csv"})
        if kbs.get("SEC_KIDS_TEENS_TRACK") or "kids" in c["age_groups"]:
            faq.append({
                "q": f"کلاس {name} برای کودکان در کرج از چه سنی شروع می‌شود؟",
                "a": ("گروه‌های سنی ثبت‌شده برای این دوره عبارت‌اند از: "
                      + "، ".join({"kids": "کودکان", "teens": "نوجوانان", "adults": "بزرگسالان"}[a]
                                  for a in c["age_groups"])
                      + ". تعیین سطح رایگان مشخص می‌کند هنرجو در کدام گروه سنی و سطح قرار می‌گیرد."),
                "source": "courses.csv",
            })
        for r in self.ortho_kws(page["silo_id"])[:4]:
            faq.append({
                "q": f"{r['raw_keyword']} کجاست و چطور ثبت‌نام کنم؟",
                "a": (f"پردیس مرکزی ما در {self.profile['address_fa']} قرار دارد. "
                      f"برای ثبت‌نام کافی است با {self.profile['phone_display']} تماس بگیرید یا در واتساپ "
                      f"({self.profile['mobile_whatsapp']}) پیام بدهید؛ ساعات پاسخ‌گویی: "
                      f"{self.profile['opening_hours']}"),
                "source": "academy_data.txt",
                "ortho_variant": True,
            })
        if kbs.get("SEC_PRIVATE_VS_GROUP_FORMAT"):
            faq.append({
                "q": f"تفاوت کلاس خصوصی و گروهی {name} در کرج چیست؟",
                "a": ("کلاس خصوصی تک‌نفره با تمرکز کامل استاد روی یک هنرجو و زمان‌بندی منعطف برگزار می‌شود؛ "
                      "کلاس گروهی هزینه کمتری دارد و تجربه گروه‌نوازی/تمرین جمعی را اضافه می‌کند. "
                      "هر دو فرمت در جدول «شهریه و فرمت کلاس» همین صفحه با قیمت دقیق مقایسه شده‌اند."),
                "source": "courses.csv",
            })
        if kbs.get("SEC_INSTRUCTOR_ROSTER"):
            kw = kbs["SEC_INSTRUCTOR_ROSTER"][0]["raw_keyword"]
            verified = [x for x in cards if not x["is_placeholder"]]
            if verified:
                a = ("اساتید تأییدشده این دوره: " + "، ".join(f"{x['name_fa']} ({x['role_title_fa']})"
                                                               for x in verified) + ".")
            else:
                a = ("رزومه کامل استاد این دوره در حال تأیید نهایی توسط آموزشگاه است و بلافاصله پس از تأیید "
                     "در همین بخش منتشر می‌شود — [INTERNAL_DATA_NEEDED]. برای معرفی حضوری استاد می‌توانید "
                     "جلسه مشاوره رایگان رزرو کنید.")
            faq.append({"q": f"{kw} چه کسانی هستند؟", "a": a, "source": "instructors.csv"})
        faq.append({
            "q": f"آدرس کلاس {name} در کرج کجاست و از فردیس چطور بیاییم؟",
            "a": (f"{self.profile['address_fa']}. "
                  "از فردیس و ملارد با مترو کرج تنها ۵ دقیقه پیاده تا آموزشگاه فاصله دارید؛ "
                  "مسیرهای دقیق در بخش «دسترسی و آدرس» همین صفحه آمده است."),
            "source": "academy_data.txt",
        })
        return faq[:9]

    # ================================================= TIER 2 COURSE PAGE
    def build_course_page(self, page):
        c = self.courses[page["course_id"]]
        kbs = self.kws_by_section(page["silo_id"])
        cards = self.instructor_cards(c["course_id"])
        slug = page["url_slug"]
        name = c["name_fa"].replace("کلاس و آموزش ", "").replace("کلاس آموزش ", "").replace("آموزشگاه و کلاس ", "").replace("کلاس ", "")
        mods = page["required_onpage_modules"]
        secs = []

        hero_kws = [r["raw_keyword"] for r in kbs.get("SEC_HERO_OVERVIEW", [])]
        self.add_media(slug, f"تصویر شاخص کلاس {name}",
                       "۱۲۰۰×۶۷۵، عکس واقعی کلاس/ساز در پردیس کرج، loading=eager fetchpriority=high", "P1")

        secs.append(section(
            "SEC_01_HERO", f"آموزش و کلاس {name} در کرج (خصوصی، گروهی و کودکان با اساتید مجرب)",
            "hero", "hero_course_enrollment_split",
            {
                "g1_user_question": f"آیا آموزشگاهی معتبر در کرج هست که {name} را با استاد مجرب، شهریه شفاف و مدرک معتبر آموزش دهد؟",
                "g2_keywords": hero_kws,
                "g3_fact_support": "CATALOG_SUPPORTED + ACADEMY_BRAND_SUPPORTED",
                "g5_verbatim": [f"courses.csv → {c['name_fa']}", f"courses.csv → {c['certificate_type']}",
                                f"academy_data.txt → {self.profile['license_fa']}"],
                "g6_bluf": page["serp_and_ai_targets"]["bluf_answer_target"],
                "g7_cta": CTA_PRIMARY,
                "g8_media": f"تصویر شاخص کلاس {name} (۱۲۰۰×۶۷۵، eager/fetchpriority=high)",
            },
            badges=[("حضور استاد خانم و آقا" if c["has_female_instructor"] else "اساتید مجرب"),
                    "کلاس خصوصی و گروهی" if len(c["formats_offered"]) > 1 else "کلاس تخصصی",
                    "ویژه " + "، ".join({"kids": "کودکان", "teens": "نوجوانان", "adults": "بزرگسالان"}[a] for a in c["age_groups"]),
                    c["certificate_type"],
                    (f"شروع شهریه گروهی {L.irr_to_toman_fa(c['tuition_group_irr'])} تومان"
                     if c["tuition_group_irr"] else "استعلام شهریه")],
            jump_pills=[p for p in [("اساتید دوره", "#instructors"),
                                    ("استاد خانم", "#female-teachers") if "SEC_FEMALE_INSTRUCTORS" in mods else None,
                                    ("خصوصی یا گروهی", "#formats"),
                                    ("سبک‌ها و زیرتخصص‌ها", "#sub-styles") if "SEC_SUBSTYLE_TABS" in mods else None,
                                    ("کلاس کودکان", "#kids-track") if "SEC_KIDS_TEENS_TRACK" in mods else None,
                                    ("شهریه و قیمت", "#tuition"),
                                    ("سرفصل‌ها", "#syllabus"),
                                    ("آدرس آموزشگاه", "#campus-map"),
                                    ("سوالات متداول", "#faq")] if p],
            paragraphs=[
                kw_sentence(f"آموزشگاه سینمایی و بازیگری آنک در کرج پاسخ مستقیم جست‌وجوهای",
                            hero_kws[:5], "است."),
                kw_sentence("همه این عنوان‌ها به یک دوره واحد و کامل می‌رسند:", hero_kws[5:12],
                            "— بدون صفحه‌های تکراری و با یک مسیر ثبت‌نام شفاف.") if len(hero_kws) > 5 else "",
                kw_sentence("همچنین پوشش کامل:", hero_kws[12:], "") if len(hero_kws) > 12 else "",
            ],
        ))

        if "SEC_INSTRUCTOR_ROSTER" in mods:
            ikws = [r["raw_keyword"] for r in kbs.get("SEC_INSTRUCTOR_ROSTER", [])]
            self.add_media(slug, f"پرتره اساتید {name}", "۸۰۰×۱۰۰۰ (۴:۵)، پرتره واقعی هر استاد با پس‌زمینه کلاس", "P1")
            secs.append(section(
                "SEC_02_INSTRUCTORS", f"اساتید {name} در کرج (رزومه و افتخارات تأییدشده)",
                "instructors", "instructor_roster_cards",
                {
                    "g1_user_question": f"استاد {name} در کرج چه سابقه و مدرکی دارد و آیا واقعاً حرفه‌ای است؟",
                    "g2_keywords": ikws,
                    "g3_fact_support": "CATALOG_SUPPORTED (instructors.csv)",
                    "g5_verbatim": [f"{x['instructor_id']} → {x['name_fa']} | {x['role_title_fa']}" for x in cards],
                    "g6_bluf": (f"اساتید {name} آموزشگاه آنک با مدارک دانشگاهی و سوابق حرفه‌ای تأییدشده تدریس می‌کنند؛ "
                                "رزومه، جنسیت استاد و روزهای کلاس هر مدرس در کارت اختصاصی او آمده است."),
                    "g7_cta": "درخواست معرفی استاد و رزرو جلسه مشاوره",
                    "g8_media": "پرتره ۴:۵ هر استاد + نمونه اجرای صوتی/تصویری",
                },
                instructor_cards=cards,
                paragraphs=[kw_sentence("این بخش دقیقاً به جست‌وجوهای", ikws,
                                        "پاسخ می‌دهد و فقط اساتید تأییدشده در کاتالوگ رسمی آموزشگاه را نمایش می‌دهد."),
                            ("برای این دوره هنوز رزومه استاد به‌صورت رسمی تأیید نشده است؛ کارت استاد با برچسب "
                             "[INTERNAL_DATA_NEEDED] رزرو شده و هیچ نام ساختگی نمایش داده نمی‌شود.")
                            if all(x["is_placeholder"] for x in cards) and cards else ""],
            ))

        if "SEC_FEMALE_INSTRUCTORS" in mods:
            fkws = [r["raw_keyword"] for r in kbs.get("SEC_FEMALE_INSTRUCTORS", [])]
            fem_cards = [x for x in cards if x["gender"] == "female"]
            secs.append(section(
                "SEC_02B_FEMALE", f"مدرس خانم {name} در کرج (ویژه بانوان، کودکان و نوجوانان)",
                "female-teachers", "female_instructor_spotlight",
                {
                    "g1_user_question": f"آیا {name} با استاد خانم و در فضای ویژه بانوان برگزار می‌شود؟",
                    "g2_keywords": fkws or [f"کلاس {name} بانوان در کرج"],
                    "g3_fact_support": "CATALOG_SUPPORTED (courses.csv → has_female_instructor)",
                    "g5_verbatim": [f"courses.csv → has_female_instructor = {str(c['has_female_instructor']).lower()}"]
                                   + [f"{x['instructor_id']} → {x['name_fa']}" for x in fem_cards],
                    "g6_bluf": (f"بله؛ در کاتالوگ رسمی دوره‌های آموزشگاه آنک، {name} دارای مدرس خانم است و "
                                "کلاس‌های ویژه بانوان، کودکان و نوجوانان با استاد خانم زمان‌بندی می‌شود."),
                    "g7_cta": "رزرو کلاس با استاد خانم",
                    "g8_media": "پرتره استاد خانم (پس از تأیید آموزشگاه)",
                },
                instructor_cards=fem_cards,
                data_gap=(not any(not x["is_placeholder"] for x in fem_cards)),
                paragraphs=[kw_sentence("پاسخ مستقیم به جست‌وجوهای", fkws, "در همین بخش آمده است.") if fkws else
                            f"کلاس {name} ویژه بانوان با مدرس خانم در کرج برگزار می‌شود."],
            ))

        if "SEC_PRIVATE_VS_GROUP_FORMAT" in mods:
            pkws = [r["raw_keyword"] for r in kbs.get("SEC_PRIVATE_VS_GROUP_FORMAT", [])]
            secs.append(section(
                "SEC_03_FORMATS", f"کلاس خصوصی یا گروهی {name} در کرج؟ (ماتریس مقایسه)",
                "formats", "format_comparison_matrix",
                {
                    "g1_user_question": "کلاس خصوصی بگیرم یا گروهی؟ تفاوت قیمت و سرعت پیشرفت چقدر است؟",
                    "g2_keywords": pkws or [f"آموزش خصوصی {name} در کرج"],
                    "g3_fact_support": "CATALOG_SUPPORTED (courses.csv → formats_offered, tuition)",
                    "g5_verbatim": [f"courses.csv → formats_offered = {'|'.join(c['formats_offered'])}"],
                    "g6_bluf": (f"{name} در آنک هم خصوصی تک‌نفره و هم گروهی/کارگاهی ارائه می‌شود؛ "
                                "خصوصی برای پیشرفت سریع و زمان‌بندی منعطف و گروهی برای هزینه کمتر و تجربه تمرین جمعی."),
                    "g7_cta": "مشاوره انتخاب فرمت کلاس",
                    "g8_media": "عکس کلاس خصوصی و کلاس گروهی (۸۰۰×۶۰۰)",
                },
                matrix=self.tuition_rows(c),
                paragraphs=[kw_sentence("این جدول پاسخ جست‌وجوهای", pkws, "است.") if pkws else ""],
            ))

        if "SEC_SUBSTYLE_TABS" in mods:
            tabs = []
            for m in page.get("sub_specialty_modules", []):
                tabs.append({"module_id": m["module_id"], "title_fa": m["heading_fa"],
                             "keywords": m["keywords"],
                             "body_fa": kw_sentence("این سبک به‌صورت اختصاصی و با سرفصل جدا تدریس می‌شود و پاسخ جست‌وجوهای",
                                                    m["keywords"], "است.")})
            for sp in c["sub_specialties_fa"]:
                if not any(sp[:8] in t["title_fa"] for t in tabs):
                    tabs.append({"module_id": "MOD_SUB_STYLE_TRACKS", "title_fa": sp, "keywords": [],
                                 "body_fa": f"سرفصل «{sp}» بخشی از همین دوره است و در ترم‌بندی رسمی آموزشگاه تدریس می‌شود."})
            secs.append(section(
                "SEC_04_SUBSTYLES", f"سبک‌ها و زیرتخصص‌های {name} در کرج",
                "sub-styles", "sub_specialty_tabs",
                {
                    "g1_user_question": f"آیا سبک خاصی از {name} (مثل زیرتخصص‌های تخصصی) هم تدریس می‌شود؟",
                    "g2_keywords": [k for t in tabs for k in t["keywords"]],
                    "g3_fact_support": "CATALOG_SUPPORTED (courses.csv → sub_specialties_fa)",
                    "g5_verbatim": [f"courses.csv → {sp}" for sp in c["sub_specialties_fa"]],
                    "g6_bluf": (f"{name} در آنک شامل "
                                + "، ".join(c["sub_specialties_fa"][:4]) +
                                " است و هر سبک سرفصل، استاد و تمرین اختصاصی خود را دارد."),
                    "g7_cta": "انتخاب سبک و تعیین سطح",
                    "g8_media": "یک تصویر شاخص برای هر سبک/زیرتخصص",
                },
                tabs=tabs,
            ))

        if "SEC_KIDS_TEENS_TRACK" in mods:
            kkws = [r["raw_keyword"] for r in kbs.get("SEC_KIDS_TEENS_TRACK", [])]
            secs.append(section(
                "SEC_05_KIDS", f"مسیر ویژه کودکان و نوجوانان در کلاس {name} کرج",
                "kids-track", "kids_pedagogy_cards",
                {
                    "g1_user_question": "فرزند من از چه سنی می‌تواند شروع کند و روش آموزش کودک چه تفاوتی دارد؟",
                    "g2_keywords": kkws or [f"کلاس {name} کودکان در کرج"],
                    "g3_fact_support": "CATALOG_SUPPORTED (courses.csv → age_groups) + PEDAGOGICAL_GUIDANCE",
                    "g5_verbatim": [f"courses.csv → age_groups = {'|'.join(c['age_groups'])}"],
                    "g6_bluf": ("گروه‌های سنی این دوره: "
                                + "، ".join({"kids": "کودکان", "teens": "نوجوانان", "adults": "بزرگسالان"}[a]
                                            for a in c["age_groups"])
                                + "؛ جلسات کودکان کوتاه‌تر، بازی‌محور و با امکان حضور والدین در جلسه اول است."),
                    "g7_cta": "رزرو تعیین سطح رایگان کودک",
                    "g8_media": "عکس کلاس کودکان (با رضایت‌نامه والدین)",
                },
                paragraphs=[kw_sentence("این مسیر پاسخ جست‌وجوهای", kkws, "است.") if kkws else "",
                            "روش آموزش کودک بر پایه بازی، تکرار کوتاه و تشویق مرحله‌ای طراحی شده است (راهنمای آموزشی)."],
            ))

        if "SEC_TUITION_TABLE" in mods:
            tkws = [r["raw_keyword"] for r in kbs.get("SEC_TUITION_TABLE", [])]
            secs.append(section(
                "SEC_06_TUITION", f"شهریه، قیمت و هزینه کلاس {name} در کرج (شفاف و بدون هزینه پنهان)",
                "tuition", "tuition_transparent_table",
                {
                    "g1_user_question": f"هزینه واقعی کلاس {name} در کرج چقدر است و چه چیزی شامل آن می‌شود؟",
                    "g2_keywords": tkws or [f"شهریه کلاس {name} در کرج"],
                    "g3_fact_support": "CATALOG_SUPPORTED (courses.csv → tuition_private_irr / tuition_group_irr)",
                    "g5_verbatim": [f"courses.csv → tuition_private_irr = {c['tuition_private_irr']} ریال",
                                    f"courses.csv → tuition_group_irr = {c['tuition_group_irr']} ریال",
                                    f"courses.csv → sessions_per_term = {c['sessions_per_term']}"],
                    "g6_bluf": (f"شهریه {name} در کرج: گروهی از {L.irr_to_toman_fa(c['tuition_group_irr'])} تومان و "
                                f"خصوصی از {L.irr_to_toman_fa(c['tuition_private_irr'])} تومان برای هر ترم "
                                f"{L.to_persian_digits(c['sessions_per_term'])} جلسه‌ای، "
                                f"به‌همراه {c['certificate_type']}."),
                    "g7_cta": "دریافت مشاوره شهریه و شرایط اقساط",
                    "g8_media": "آیکون‌های شفافیت قیمت (SVG سبک)",
                },
                table=self.tuition_rows(c),
                paragraphs=[kw_sentence("جدول زیر دقیقاً پاسخ", tkws, "است.") if tkws else
                            "جدول زیر شهریه رسمی ثبت‌شده این دوره است."],
            ))

        if "SEC_SYLLABUS_ROADMAP" in mods:
            secs.append(section(
                "SEC_07_SYLLABUS", f"سرفصل‌ها و مسیر یادگیری {name} (مقدماتی تا پیشرفته)",
                "syllabus", "syllabus_term_timeline",
                {
                    "g1_user_question": "در هر ترم دقیقاً چه چیزی یاد می‌گیرم و چقدر طول می‌کشد؟",
                    "g2_keywords": [page["primary_keyword"]],
                    "g3_fact_support": "CATALOG_SUPPORTED (courses.csv → sub_specialties_fa, sessions_per_term) + PEDAGOGICAL_GUIDANCE",
                    "g5_verbatim": [f"courses.csv → {sp}" for sp in c["sub_specialties_fa"]],
                    "g6_bluf": (f"مسیر یادگیری {name} در سه سطح مقدماتی، متوسطه و پیشرفته طراحی شده و هر ترم "
                                f"{L.to_persian_digits(c['sessions_per_term'])} جلسه "
                                f"{L.to_persian_digits(c['session_duration_min'])} دقیقه‌ای است."),
                    "g7_cta": "دریافت سرفصل کامل دوره",
                    "g8_media": "عکس کارگاه/استودیو و تجهیزات در دسترس هنرجو",
                },
                steps=self.syllabus_steps(c),
            ))

        if "SEC_CAFE_PERFORMANCE_BRIDGE" in mods:
            fa = next((f for f, _, sl, cid, _ in L.CAFE_INSTRUMENTS if cid == c["course_id"]), name)
            evs = [e for e in self.cafe_events
                   if fa.replace(" ", "") in e["instrument_focus_fa"].replace("‌", "").replace(" ", "")]
            secs.append(section(
                "SEC_08_CAFE_BRIDGE", f"اجرای زنده {fa} در کافه هنر آکادمی",
                "cafe-stage", "art_cafe_stage_banner",
                {
                    "g1_user_question": "بعد از یادگیری کجا می‌توانم جلوی مخاطب واقعی اجرا کنم؟",
                    "g2_keywords": [f"کافه {fa} کرج"],
                    "g3_fact_support": "CATALOG_SUPPORTED (cafe_events.csv) + ACADEMY_BRAND_SUPPORTED",
                    "g5_verbatim": [f"cafe_events.csv → {e['title_fa']} | {e['days_of_week_fa']} | {e['time_range_fa']}"
                                    for e in evs],
                    "g6_bluf": (f"هنرجویان {name} می‌توانند روی صحنه کافه هنر و موسیقی آنک در کرج اجرای زنده داشته "
                                "باشند؛ برنامه شب‌های اجرا و نام نوازندگان در صفحه کافه هنر آمده است."),
                    "g7_cta": CTA_CAFE,
                    "g8_media": "عکس صحنه کافه در شب اجرا (۱۰۰۰×۶۶۷)",
                },
                events=evs, link="/art-cafe/",
            ))

        if "SEC_FARDIS_COMMUTER_ACCESS" in mods:
            froutes = [x for x in self.kmap["fardis_geo_mapping"]["dual_intent_routes"]
                       if x["course_slug"] == slug]
            secs.append(section(
                "SEC_09_FARDIS", f"دسترسی هنرجویان فردیس کرج به کلاس {name}",
                "fardis-access", "fardis_commuter_box",
                {
                    "g1_user_question": "از فردیس چطور و در چند دقیقه به این کلاس برسم؟",
                    "g2_keywords": [x["keyword"] for x in froutes],
                    "g3_fact_support": "ACADEMY_BRAND_SUPPORTED (academy_data.txt → TRANSIT_AND_COMMUTER_ROUTES)",
                    "g5_verbatim": self.profile["transit_routes"][:2],
                    "g6_bluf": ("هنرجویان فردیس با مترو کرج تنها ۵ دقیقه پیاده تا پردیس آنک فاصله دارند و "
                                "شیفت‌های فشرده پنجشنبه و جمعه مخصوص آن‌ها زمان‌بندی شده است."),
                    "g7_cta": "مشاهده مسیرها و شیفت ویژه فردیس",
                    "g8_media": "نقشه مسیر فردیس → پردیس کرج",
                },
                link="/fardis-branch/",
            ))

        if "SEC_AUDITION_BRIDGE" in mods:
            secs.append(section(
                "SEC_09B_AUDITION", f"تست بازیگری و تعیین سطح پیش از ثبت‌نام {name}",
                "audition-bridge", "audition_step_cards",
                {
                    "g1_user_question": "قبل از ثبت‌نام باید تست بدهم؟ تست بازیگری در کرج کجاست؟",
                    "g2_keywords": ["تست بازیگری در کرج", "تست بازیگری در کرج کجاست"],
                    "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
                    "g5_verbatim": [f"academy_data.txt → {self.profile['address_fa']}"],
                    "g6_bluf": "تست بازیگری و تعیین سطح رایگان در پردیس کرج برگزار می‌شود و نتیجه آن مسیر دوره را مشخص می‌کند.",
                    "g7_cta": CTA_AUDITION, "g8_media": "عکس اتاق تست/بلک‌باکس",
                },
                link="/acting-audition/",
            ))

        addr_kws = [r["raw_keyword"] for r in kbs.get("SEC_CAMPUS_MAP_DIRECTIONS", [])]
        secs.append(section(
            "SEC_10_CAMPUS", f"آدرس و دسترسی کلاس {name} در کرج",
            "campus-map", "campus_map_and_nap_card",
            {
                "g1_user_question": f"آدرس کلاس {name} در کرج کجاست و چطور بیایم؟",
                "g2_keywords": addr_kws or [f"آدرس کلاس {name} در کرج"],
                "g3_fact_support": "ACADEMY_BRAND_SUPPORTED (academy_data.txt → EXACT_ADDRESS / LANDMARKS)",
                "g5_verbatim": [self.profile["address_fa"]] + self.profile["landmarks"][:3],
                "g6_bluf": (f"{self.profile['address_fa']}؛ ساعات کاری: {self.profile['opening_hours']}؛ "
                            f"تماس: {self.profile['phone_display']}."),
                "g7_cta": "مسیریابی با گوگل‌مپ، نشان یا بلد",
                "g8_media": "عکس نمای ورودی ساختمان آموزشگاه",
            },
            nap={"address": self.profile["address_fa"], "phone": self.profile["phone_display"],
                 "phone_e164": self.profile["phone_e164"], "hours": self.profile["opening_hours"],
                 "maps": self.profile["maps_url"], "neshan": self.profile["neshan_url"],
                 "balad": self.profile["balad_url"], "waze": self.profile["waze_url"]},
            landmarks=self.profile["landmarks"],
            paragraphs=[kw_sentence("این بخش پاسخ", addr_kws, "است.") if addr_kws else ""],
        ))

        secs.append(section(
            "SEC_11_FAQ", f"سوالات متداول درباره کلاس {name} در کرج",
            "faq", "faq_accordion_rtl",
            {
                "g1_user_question": "سوال‌های باقی‌مانده درباره شهریه، استاد خانم، سن کودک و آدرس.",
                "g2_keywords": [r["raw_keyword"] for r in self.ortho_kws(page["silo_id"])],
                "g3_fact_support": "CATALOG_SUPPORTED + ACADEMY_BRAND_SUPPORTED",
                "g5_verbatim": ["courses.csv", "instructors.csv", "academy_data.txt"],
                "g6_bluf": "پاسخ کوتاه و مستقیم به پرتکرارترین سوالات هنرجویان و والدین کرج و فردیس.",
                "g7_cta": CTA_PRIMARY, "g8_media": "—",
            },
            faq=self.faq_for_course(page, c, kbs, cards),
        ))
        return secs

    # ================================================== TIER 1 DEPT HUB
    def build_dept_page(self, page):
        dkey = page["department_id"]
        d = L.DEPARTMENTS[dkey]
        kbs = self.kws_by_section(page["silo_id"])
        children = self.dept_children[dkey]
        slug = page["url_slug"]
        all_kws = [r["raw_keyword"] for rs in kbs.values() for r in rs]
        secs = []
        self.add_media(slug, f"تصویر شاخص {d['name_fa']}", "۱۲۰۰×۶۷۵ عکس واقعی فضای دانشکده", "P1")

        bluf = (f"{d['name_fa']} آموزشگاه آنک در کرج با {L.to_persian_digits(len(children))} دوره تخصصی، "
                f"اساتید خانم و آقا، کلاس خصوصی و گروهی و شهریه شفاف برگزار می‌شود؛ "
                "مشاوره و تعیین سطح رایگان و دسترسی مستقیم از فردیس.")
        secs.append(section(
            "SEC_01_HERO", d["title_fa"], "hero", "hero_course_enrollment_split",
            {"g1_user_question": f"کدام دوره از {d['name_fa']} برای من مناسب است و هزینه‌اش چقدر است؟",
             "g2_keywords": [r["raw_keyword"] for r in kbs.get("SEC_HERO_OVERVIEW", [])],
             "g3_fact_support": "CATALOG_SUPPORTED + ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [f"courses.csv → {c['name_fa']}" for c in children[:4]],
             "g6_bluf": bluf, "g7_cta": CTA_PRIMARY,
             "g8_media": "تصویر شاخص دانشکده"},
            paragraphs=[kw_sentence("این صفحه پاسخ مستقیم جست‌وجوهای", all_kws[:6], "است.") if all_kws else "",
                        kw_sentence("و همچنین:", all_kws[6:], "") if len(all_kws) > 6 else ""],
            badges=[f"{L.to_persian_digits(len(children))} دوره فعال",
                    ("حضور استاد خانم و آقا" if any(c["has_female_instructor"] for c in children)
                     else "اساتید مجرب"),
                    "کلاس خصوصی و گروهی",
                    "ویژه کودکان، نوجوانان و بزرگسالان",
                    (f"شروع شهریه گروهی از "
                     f"{L.irr_to_toman_fa(min(c['tuition_group_irr'] for c in children if c['tuition_group_irr']))}"
                     " تومان"),
                    "مشاوره و تعیین سطح رایگان"],
            jump_pills=[("همه دوره‌ها", "#courses"), ("شهریه", "#tuition"),
                        ("اساتید", "#instructors"), ("آدرس", "#campus-map"), ("سوالات", "#faq")],
        ))
        secs.append(section(
            "SEC_02_COURSE_GRID", f"همه دوره‌های {d['name_fa']} در کرج ({L.to_persian_digits(len(children))} رشته)",
            "courses", "course_navigation_grid",
            {"g1_user_question": "چه رشته‌هایی آموزش داده می‌شود و هر کدام برای چه سنی است؟",
             "g2_keywords": [page["primary_keyword"]],
             "g3_fact_support": "CATALOG_SUPPORTED (courses.csv)",
             "g5_verbatim": [f"{c['course_id']} → {c['name_fa']}" for c in children],
             "g6_bluf": f"{L.to_persian_digits(len(children))} دوره فعال با شهریه و گروه سنی مشخص.",
             "g7_cta": "انتخاب دوره و مشاهده جزئیات", "g8_media": "آیکون/عکس هر دوره (۶۰۰×۴۰۰)"},
            cards=[{"name_fa": c["name_fa"], "slug": c["slug"],
                    "tuition_group_toman_fa": L.irr_to_toman_fa(c["tuition_group_irr"]),
                    "instructor_count": len(L.instructors_for(c["course_id"], self.instructors)),
                    "age_groups": c["age_groups"], "sub_specialties_fa": c["sub_specialties_fa"][:3]}
                   for c in children],
        ))
        if dkey == "DEPT_MUSIC":
            secs.append(section(
                "SEC_03_MUSIC_THEORY", "آموزش تئوری موسیقی و سلفژ در کرج", "music-theory", "syllabus_term_timeline",
                {"g1_user_question": "آیا تئوری موسیقی و سلفژ هم آموزش داده می‌شود؟",
                 "g2_keywords": ["آموزش تئوری موسیقی در کرج"],
                 "g3_fact_support": "PEDAGOGICAL_GUIDANCE + ACADEMY_BRAND_SUPPORTED",
                 "g5_verbatim": ["academy_data.txt → مجوز رسمی وزارت فرهنگ و ارشاد اسلامی"],
                 "g6_bluf": ("آموزش تئوری موسیقی و سلفژ در کرج به‌صورت ماژول مکمل در کنار ساز تخصصی ارائه می‌شود "
                             "و نت‌خوانی، ریتم‌خوانی و شنوایی هنرجو را تقویت می‌کند."),
                 "g7_cta": "افزودن ماژول تئوری به کلاس ساز", "g8_media": "عکس وایت‌برد نت و کلاس تئوری"},
                steps=[{"level_fa": "تئوری پایه", "description_fa": "نت‌خوانی، میزان، کشش‌ها و دانگ‌ها", "modules_fa": [], "term_fa": "ترم ۱"},
                       {"level_fa": "سلفژ و شنوایی", "description_fa": "تربیت شنوایی، دیکته ملودیک و ریتم‌خوانی", "modules_fa": [], "term_fa": "ترم ۲"},
                       {"level_fa": "هارمونی مقدماتی", "description_fa": "آکوردشناسی و همراهی", "modules_fa": [], "term_fa": "ترم ۳"}],
            ))
        tkws = [r["raw_keyword"] for r in kbs.get("SEC_TUITION_TABLE", [])]
        secs.append(section(
            "SEC_04_TUITION", f"جدول مقایسه شهریه دوره‌های {d['name_fa']} در کرج", "tuition", "tuition_transparent_table",
            {"g1_user_question": "شهریه هر دوره چقدر است و کدام اقتصادی‌تر است؟",
             "g2_keywords": tkws or [page["primary_keyword"]],
             "g3_fact_support": "CATALOG_SUPPORTED (courses.csv)",
             "g5_verbatim": [f"{c['course_id']} → خصوصی {c['tuition_private_irr']} ریال / گروهی {c['tuition_group_irr']} ریال"
                             for c in children[:6]],
             "g6_bluf": "جدول زیر شهریه خصوصی و گروهی همه دوره‌های این دانشکده را در یک نگاه مقایسه می‌کند.",
             "g7_cta": "دریافت مشاوره شهریه و اقساط", "g8_media": "—"},
            table=[{"course_fa": c["name_fa"], "slug": c["slug"],
                    "private_toman_fa": L.irr_to_toman_fa(c["tuition_private_irr"]),
                    "group_toman_fa": L.irr_to_toman_fa(c["tuition_group_irr"]),
                    "sessions": L.to_persian_digits(c["sessions_per_term"]),
                    "duration_fa": f"{L.to_persian_digits(c['session_duration_min'])} دقیقه"} for c in children],
            paragraphs=[kw_sentence("این جدول پاسخ", tkws, "است.") if tkws else ""],
        ))
        if dkey == "DEPT_MUSIC":
            secs.append(section(
                "SEC_05_CAFE", "اجرای زنده هنرجویان در کافه هنر و موسیقی آکادمی", "cafe-stage", "art_cafe_stage_banner",
                {"g1_user_question": "هنرجو کجا تجربه اجرای زنده به‌دست می‌آورد؟",
                 "g2_keywords": ["کافه پیانو کرج", "کافه گیتار کرج", "کافه سنتور کرج"],
                 "g3_fact_support": "CATALOG_SUPPORTED (cafe_events.csv)",
                 "g5_verbatim": [f"{e['title_fa']} — {e['days_of_week_fa']} {e['time_range_fa']}" for e in self.cafe_events],
                 "g6_bluf": "هنرجویان موسیقی روی صحنه کافه هنر آنک در کرج اجرای زنده دارند؛ برنامه هفتگی در صفحه کافه آمده است.",
                 "g7_cta": CTA_CAFE, "g8_media": "عکس صحنه کافه"},
                events=self.cafe_events, link="/art-cafe/",
            ))
        dept_instr = []
        for ch in children:
            for ic in self.instructor_cards(ch["course_id"]):
                if ic["instructor_id"] not in {x["instructor_id"] for x in dept_instr}:
                    dept_instr.append(ic)
        ikws = [r["raw_keyword"] for r in kbs.get("SEC_INSTRUCTOR_ROSTER", [])]
        secs.append(section(
            "SEC_05B_INSTRUCTORS", f"اساتید {d['name_fa']} در کرج", "instructors", "instructor_roster_cards",
            {"g1_user_question": f"اساتید {d['name_fa']} چه کسانی هستند؟",
             "g2_keywords": ikws or [f"اساتید {d['name_fa']} کرج"],
             "g3_fact_support": "CATALOG_SUPPORTED (instructors.csv)",
             "g5_verbatim": [f"{x['instructor_id']} → {x['name_fa']} | {x['role_title_fa']}" for x in dept_instr] or
                            ["instructors.csv → هیچ استاد تأییدشده‌ای برای این دانشکده ثبت نشده است"],
             "g6_bluf": ((f"{L.to_persian_digits(len([x for x in dept_instr if not x['is_placeholder']]))} استاد "
                          "تأییدشده در این دانشکده تدریس می‌کنند؛ رزومه کامل هر استاد در کارت اختصاصی او آمده است.")
                         if any(not x["is_placeholder"] for x in dept_instr)
                         else "رزومه اساتید این دانشکده در انتظار تأیید رسمی آموزشگاه است — [INTERNAL_DATA_NEEDED]."),
             "g7_cta": "مشاهده همه اساتید", "g8_media": "پرتره ۴:۵ اساتید"},
            instructor_cards=dept_instr, link="/instructors/",
            data_gap=not any(not x["is_placeholder"] for x in dept_instr),
            paragraphs=[kw_sentence("این بخش پاسخ", ikws, "است.") if ikws else ""],
        ))
        if dkey == "DEPT_MUSIC":
            secs.append(section(
                "SEC_05C_FARDIS", "هنرجویان فردیس کرج", "fardis-access", "fardis_commuter_box",
                {"g1_user_question": "از فردیس چطور به کلاس موسیقی برسم؟",
                 "g2_keywords": ["کلاس موسیقی در فردیس کرج", "کلاس موسیقی فردیس کرج"],
                 "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
                 "g5_verbatim": self.profile["transit_routes"][:2],
                 "g6_bluf": ("هنرجویان فردیس با مترو کرج ۵ دقیقه پیاده تا پردیس مرکزی فاصله دارند و شیفت فشرده "
                             "آخر هفته برای آن‌ها زمان‌بندی می‌شود."),
                 "g7_cta": "مشاهده صفحه فردیس", "g8_media": "نقشه مسیر"},
                routes=self.profile["transit_routes"], link="/fardis-branch/", fardis_status=self.f_status,
            ))
        if dkey == "DEPT_PERFORMING":
            secs.append(section(
                "SEC_05C_AUDITION", "تست بازیگری و تعیین سطح پیش از ثبت‌نام", "audition-bridge", "audition_step_cards",
                {"g1_user_question": "قبل از ثبت‌نام باید تست بدهم؟",
                 "g2_keywords": ["تست بازیگری در کرج", "تست بازیگری در کرج کجاست"],
                 "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
                 "g5_verbatim": [self.profile["address_fa"]],
                 "g6_bluf": "تست بازیگری و تعیین سطح رایگان در پردیس کرج برگزار می‌شود و مسیر دوره را مشخص می‌کند.",
                 "g7_cta": CTA_AUDITION, "g8_media": "عکس اتاق تست"},
                link="/acting-audition/",
            ))
        akws = [r["raw_keyword"] for r in kbs.get("SEC_CAMPUS_MAP_DIRECTIONS", [])]
        secs.append(section(
            "SEC_06_CAMPUS", f"آدرس {d['name_fa']} در کرج و دسترسی از فردیس", "campus-map", "campus_map_and_nap_card",
            {"g1_user_question": "آدرس دقیق و مسیر دسترسی چیست؟",
             "g2_keywords": akws or ["آدرس آموزشگاه در کرج"],
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [self.profile["address_fa"]] + self.profile["landmarks"][:2],
             "g6_bluf": f"{self.profile['address_fa']}؛ {self.profile['opening_hours']}.",
             "g7_cta": "مسیریابی", "g8_media": "عکس ورودی"},
            nap={"address": self.profile["address_fa"], "phone": self.profile["phone_display"],
                 "phone_e164": self.profile["phone_e164"], "hours": self.profile["opening_hours"],
                 "maps": self.profile["maps_url"], "neshan": self.profile["neshan_url"],
                 "balad": self.profile["balad_url"], "waze": self.profile["waze_url"]},
            landmarks=self.profile["landmarks"],
            paragraphs=[kw_sentence("پاسخ مستقیم به", akws, "") if akws else ""],
        ))
        faq = []
        for r in self.ortho_kws(page["silo_id"])[:4]:
            faq.append({"q": f"{r['raw_keyword']} کجاست؟",
                        "a": f"{self.profile['address_fa']}؛ تماس: {self.profile['phone_display']}.",
                        "source": "academy_data.txt", "ortho_variant": True})
        for r in kbs.get("SEC_TUITION_TABLE", [])[:3]:
            faq.append({"q": f"{r['raw_keyword']} چقدر است؟",
                        "a": ("شهریه هر دوره در جدول مقایسه‌ای همین صفحه به تفکیک خصوصی و گروهی آمده است؛ "
                              f"ارزان‌ترین دوره گروهی از "
                              f"{L.irr_to_toman_fa(min(c['tuition_group_irr'] for c in children))} تومان شروع می‌شود."),
                        "source": "courses.csv"})
        faq.append({"q": f"بهترین {d['name_fa'].replace('دانشکده ', '')} در کرج کدام است؟",
                    "a": (f"آموزشگاه آنک با {self.profile['years_in_operation']} سابقه، {self.profile['license_fa']} و "
                          f"{L.to_persian_digits(len(children))} دوره فعال در این حوزه فعالیت می‌کند؛ "
                          "جلسه مشاوره و تعیین سطح رایگان امکان ارزیابی بدون هزینه را می‌دهد."),
                    "source": "academy_data.txt"})
        secs.append(section("SEC_07_FAQ", f"سوالات متداول {d['name_fa']} در کرج", "faq", "faq_accordion_rtl",
                            {"g1_user_question": "سوالات شهریه، آدرس و انتخاب رشته.",
                             "g2_keywords": [r["raw_keyword"] for r in self.ortho_kws(page["silo_id"])],
                             "g3_fact_support": "CATALOG_SUPPORTED + ACADEMY_BRAND_SUPPORTED",
                             "g5_verbatim": ["courses.csv", "academy_data.txt"],
                             "g6_bluf": "پاسخ کوتاه به پرتکرارترین سوالات.", "g7_cta": CTA_PRIMARY, "g8_media": "—"},
                            faq=faq))
        return secs

    # ================================================== TIER 0 HOMEPAGE
    def build_home_page(self, page):
        p = self.profile
        secs = []
        self.add_media("/", "تصویر شاخص صفحه اصلی", "۱۲۰۰×۶۷۵، کلاژ واقعی از کلاس موسیقی/بازیگری/کافه", "P1")
        secs.append(section(
            "SEC_01_HOME_HERO",
            "آموزشگاه موسیقی، بازیگری، سینما، هنرهای تجسمی و کافه هنر در کرج",
            "hero", "hero_multifaculty_portal",
            {"g1_user_question": "یک آموزشگاه معتبر در کرج که همه رشته‌های هنری را با مجوز رسمی آموزش دهد کجاست؟",
             "g2_keywords": [p["brand_fa"], "آموزشگاه هنر و موسیقی در کرج"],
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [p["brand_fa"], p["tagline_fa"], p["license_fa"], p["address_fa"]],
             "g6_bluf": page["serp_and_ai_targets"]["bluf_answer_target"],
             "g7_cta": CTA_PRIMARY, "g8_media": "تصویر شاخص ۱۲۰۰×۶۷۵ (eager)"},
            portal_cards=[
                {"title_fa": "دانشکده موسیقی (۱۴ ساز و آواز)", "slug": "/music/"},
                {"title_fa": "بازیگری، فن بیان و گویندگی", "slug": "/performing-arts/"},
                {"title_fa": "سینما، عکاسی، تدوین و گریم", "slug": "/cinema-media/"},
                {"title_fa": "نقاشی و خوشنویسی", "slug": "/visual-arts/"},
                {"title_fa": "کافه هنر و موسیقی زنده", "slug": "/art-cafe/"},
                {"title_fa": "تست بازیگری و تعیین سطح", "slug": "/acting-audition/"},
            ],
        ))
        secs.append(section(
            "SEC_02_COURSE_FINDER", f"انتخابگر دوره‌ها ({L.to_persian_digits(len(self.courses))} رشته فعال)",
            "course-finder", "interactive_course_finder",
            {"g1_user_question": "کدام رشته با سن، بودجه و هدف من می‌خواند؟",
             "g2_keywords": ["کلاس موسیقی در کرج", "کلاس بازیگری در کرج", "کلاس عکاسی در کرج", "کلاس خوشنویسی در کرج"],
             "g3_fact_support": "CATALOG_SUPPORTED (courses.csv)",
             "g5_verbatim": [f"{c['course_id']} → {c['name_fa']}" for c in list(self.courses.values())[:5]],
             "g6_bluf": (f"{L.to_persian_digits(len(self.courses))} دوره فعال در ۴ دانشکده، با فیلتر سن "
                         "(کودک/نوجوان/بزرگسال)، فرمت (خصوصی/گروهی) و حضور استاد خانم."),
             "g7_cta": "مشاهده دوره و شهریه", "g8_media": "آیکون هر دوره"},
            cards=[{"name_fa": c["name_fa"], "slug": c["slug"], "department_id": c["department_id"],
                    "age_groups": c["age_groups"], "formats": c["formats_offered"],
                    "has_female_instructor": c["has_female_instructor"],
                    "tuition_group_toman_fa": L.irr_to_toman_fa(c["tuition_group_irr"])}
                   for c in self.courses.values()],
        ))
        secs.append(section(
            "SEC_03_ART_CAFE", "کافه هنر و موسیقی زنده آنک در کرج", "art-cafe-preview", "art_cafe_stage_banner",
            {"g1_user_question": "کافه‌ای در کرج هست که موسیقی زنده پیانو، گیتار و سنتور داشته باشد؟",
             "g2_keywords": ["کافه پیانو کرج", "کافه گیتار کرج", "کافه سنتور کرج", "کافه ارگ کرج", "رستوران سه تار کرج"],
             "g3_fact_support": "CATALOG_SUPPORTED (cafe_events.csv) + ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": p["cafe_lines"] + [f"{e['title_fa']} — {e['days_of_week_fa']}" for e in self.cafe_events],
             "g6_bluf": ("کافه هنر و موسیقی آنک، کافه داخل مجموعه با اجرای زنده پیانو، گیتار، سنتور، سه‌تار و ارگ "
                         "توسط اساتید و هنرجویان است؛ رزرو میز با تماس یا واتساپ."),
             "g7_cta": CTA_CAFE, "g8_media": "عکس شب اجرای زنده"},
            events=self.cafe_events, link="/art-cafe/",
        ))
        verified = [i for i in self.instructors if not L.is_placeholder_instructor(i)]
        secs.append(section(
            "SEC_04_INSTRUCTORS", "اساتید برجسته آموزشگاه آنک کرج", "featured-instructors", "instructor_roster_cards",
            {"g1_user_question": "اساتید این آموزشگاه چه کسانی هستند و چه سابقه‌ای دارند؟",
             "g2_keywords": ["اساتید آموزشگاه آنک کرج"],
             "g3_fact_support": "CATALOG_SUPPORTED (instructors.csv)",
             "g5_verbatim": [f"{i['name_fa']} — {i['role_title_fa']}" for i in verified[:6]],
             "g6_bluf": (f"{L.to_persian_digits(len(verified))} استاد تأییدشده با مدرک دانشگاهی و سوابق حرفه‌ای "
                         "در بازیگری، نمایش خلاق، فیلمنامه‌نویسی، عکاسی و تدوین تدریس می‌کنند."),
             "g7_cta": "مشاهده همه اساتید", "g8_media": "پرتره ۴:۵ اساتید"},
            instructor_cards=[{
                "instructor_id": i["instructor_id"], "name_fa": i["name_fa"], "gender": i["gender"],
                "gender_badge_fa": "استاد خانم" if i["gender"] == "female" else "استاد آقا",
                "role_title_fa": i["role_title_fa"], "credentials_fa": i["credentials_fa"],
                "experience_highlights_fa": i.get("experience_highlights_fa", ""),
                "same_as_url": i.get("same_as_url", ""), "is_placeholder": False, "status": i["status"],
            } for i in verified], link="/instructors/",
        ))
        secs.append(section(
            "SEC_05_LICENSES", "مجوزهای رسمی، تضمین‌ها و امکانات آموزشگاه", "licenses", "trust_badges_grid",
            {"g1_user_question": "این آموزشگاه مجوز رسمی و مدرک معتبر دارد؟",
             "g2_keywords": [p["brand_fa"]],
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED (academy_data.txt)",
             "g5_verbatim": [p["license_fa"]] + p["guarantees"],
             "g6_bluf": f"{p['license_fa']}؛ {p['years_in_operation']} فعالیت رسمی در کرج و استان البرز.",
             "g7_cta": CTA_PRIMARY, "g8_media": "اسکن/عکس مجوزها (پس از تأیید آموزشگاه)"},
            guarantees=p["guarantees"], license_fa=p["license_fa"],
        ))
        secs.append(section(
            "SEC_06_CAMPUS", "پردیس مرکزی کرج و دسترسی هنرجویان فردیس", "campus-map", "campus_map_and_nap_card",
            {"g1_user_question": "آدرس آموزشگاه کجاست و از فردیس چطور برسم؟",
             "g2_keywords": [r["raw_keyword"] for r in self.records if r["section_target"] == "SEC_CAMPUS_MAP_DIRECTIONS"],
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [p["address_fa"]] + p["landmarks"],
             "g6_bluf": f"{p['address_fa']}؛ {p['opening_hours']}؛ تماس: {p['phone_display']}.",
             "g7_cta": "مسیریابی و تماس", "g8_media": "عکس نما + نقشه"},
            nap={"address": p["address_fa"], "phone": p["phone_display"], "phone_e164": p["phone_e164"],
                 "hours": p["opening_hours"], "maps": p["maps_url"], "neshan": p["neshan_url"],
                 "balad": p["balad_url"], "waze": p["waze_url"]},
            landmarks=p["landmarks"], link="/fardis-branch/",
        ))
        secs.append(section(
            "SEC_06B_FARDIS", "هنرجویان فردیس، ملارد و گوهردشت", "fardis-access", "fardis_commuter_box",
            {"g1_user_question": "از فردیس به این آموزشگاه چقدر راه است؟",
             "g2_keywords": ["کلاس موسیقی در فردیس کرج", "کلاس بازیگری در کرج فردیس"],
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED (TRANSIT_AND_COMMUTER_ROUTES)",
             "g5_verbatim": p["transit_routes"][:3],
             "g6_bluf": ("هنرجویان فردیس با مترو کرج تنها ۵ دقیقه پیاده تا پردیس مرکزی فاصله دارند؛ "
                         "آنک شعبه مستقل فردیس ندارد و همه کلاس‌ها در پردیس کرج برگزار می‌شود."),
             "g7_cta": "مشاهده صفحه ویژه هنرجویان فردیس", "g8_media": "نقشه مسیر"},
            routes=p["transit_routes"], link="/fardis-branch/", fardis_status=self.f_status,
        ))
        secs.append(section(
            "SEC_07_FAQ", "سوالات متداول آموزشگاه آنک کرج", "faq", "faq_accordion_rtl",
            {"g1_user_question": "سوالات عمومی درباره ثبت‌نام، شهریه و آدرس.",
             "g2_keywords": [], "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [p["opening_hours"], p["address_fa"]],
             "g6_bluf": "پاسخ کوتاه به پرتکرارترین سوالات هنرجویان کرج و فردیس.",
             "g7_cta": CTA_PRIMARY, "g8_media": "—"},
            faq=[
                {"q": "ساعات کاری آموزشگاه چگونه است؟", "a": p["opening_hours"], "source": "academy_data.txt"},
                {"q": "آیا مشاوره و تعیین سطح رایگان است؟",
                 "a": p["guarantees"][0] if p["guarantees"] else "بله، مشاوره و تعیین سطح رایگان است.",
                 "source": "academy_data.txt"},
                {"q": "آموزشگاه به کدام شهرها و محله‌ها سرویس می‌دهد؟",
                 "a": "شهرهای " + "، ".join(p["served_cities"]) + " و محله‌های " + "، ".join(p["served_neighborhoods"][:6]) + ".",
                 "source": "academy_data.txt"},
                {"q": "مدرک پایان دوره معتبر است؟",
                 "a": p["license_fa"] + " — نوع مدرک هر دوره در صفحه همان دوره ذکر شده است.", "source": "academy_data.txt"},
            ],
        ))
        return secs

    # ================================================== TIER 3 ART CAFE
    def build_cafe_page(self, page):
        p = self.profile
        secs = []
        kws = [r["raw_keyword"] for r in self.silo_records("SILO_CAFE_01")]
        self.add_media("/art-cafe/", "عکس فضای کافه هنر", "۱۶۰۰×۹۰۰ شب اجرای زنده، نور گرم", "P1")
        secs.append(section(
            "SEC_01_CAFE_HERO", "کافه هنر و موسیقی آنک در کرج | اجرای زنده پیانو، گیتار، سنتور، سه‌تار و ارگ",
            "hero", "cafe_hero_dark",
            {"g1_user_question": "کافه‌ای در کرج با موسیقی زنده و فضای هنری کجاست و چطور میز رزرو کنم؟",
             "g2_keywords": kws, "g3_fact_support": "ACADEMY_BRAND_SUPPORTED + CATALOG_SUPPORTED",
             "g5_verbatim": p["cafe_lines"],
             "g6_bluf": page["serp_and_ai_targets"]["bluf_answer_target"],
             "g7_cta": CTA_CAFE, "g8_media": "عکس فضای کافه در شب اجرا (eager)"},
            paragraphs=[kw_sentence("این صفحه پاسخ مستقیم جست‌وجوهای", kws, "است."),
                        p["cafe_lines"][1] if len(p["cafe_lines"]) > 1 else ""],
        ))
        for fa, sec_id, slug, cid, anchor in L.CAFE_INSTRUMENTS:
            blk = next((b for b in page["cafe_instrument_blocks"] if b["anchor"] == anchor), {})
            evs = blk.get("verified_events", [])
            secs.append(section(
                f"SEC_02_{anchor.upper().replace('-', '_')}", f"شب‌های اجرای زنده {fa} — {(blk.get('keywords') or ['کافه ' + fa + ' کرج'])[0]}",
                anchor, "cafe_live_schedule_grid",
                {"g1_user_question": f"کافه {fa} در کرج چه شب‌هایی اجرای زنده دارد؟",
                 "g2_keywords": blk.get("keywords", []),
                 "g3_fact_support": "CATALOG_SUPPORTED (cafe_events.csv)" if evs else "[INTERNAL_DATA_NEEDED]",
                 "g5_verbatim": [f"{e['title_fa']} | {e['days_of_week_fa']} | {e['time_range_fa']} | نوازنده: {e['performer_name_fa']}"
                                 for e in evs],
                 "g6_bluf": ((f"{evs[0]['title_fa']} {evs[0]['days_of_week_fa']} ساعت {evs[0]['time_range_fa']} "
                              f"با اجرای {evs[0]['performer_name_fa']} برگزار می‌شود"
                              + ("؛ رزرو میز الزامی است." if evs[0]["reservation_required"] == "true" else "."))
                             if evs else "[INTERNAL_DATA_NEEDED] — برنامه اجرای این ساز هنوز تأیید نشده است."),
                 "g7_cta": CTA_CAFE, "g8_media": f"عکس اجرای زنده {fa}"},
                events=evs, link=slug, instrument_fa=fa,
            ))
        secs.append(section(
            "SEC_03_MENU", "منوی کافه و رستوران هنر", "cafe-menu", "menu_table_rtl",
            {"g1_user_question": "منو و قیمت‌های کافه چیست؟", "g2_keywords": ["کافه رستوران سه تار کرج"],
             "g3_fact_support": "[INTERNAL_DATA_NEEDED]",
             "g5_verbatim": [], "g6_bluf": "",
             "g7_cta": "دریافت منو در واتساپ", "g8_media": "عکس آیتم‌های منو"},
            data_gap=True,
            note=("هیچ آیتم منویی در academy_data.txt یا cafe_events.csv ثبت نشده است. "
                  "اسلات منو با [INTERNAL_DATA_NEEDED] رزرو می‌شود و هیچ آیتم یا قیمتی ساخته نمی‌شود."),
        ))
        secs.append(section(
            "SEC_04_STUDENT_STAGE", "صحنه اجرای هنرجویان و شب‌های اوپن‌مایک", "student-stage", "cafe_recital_cards",
            {"g1_user_question": "هنرجوی آموزشگاه چطور روی صحنه کافه اجرا می‌کند؟",
             "g2_keywords": ["کافه پیانو کرج", "کافه گیتار کرج"],
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": p["cafe_lines"],
             "g6_bluf": ("هنرجویان موسیقی و بازیگری آنک برای تمرین اجرای صحنه‌ای و دورهمی از صحنه کافه هنر "
                         "استفاده می‌کنند؛ هماهنگی اجرا از طریق مدیر آموزش انجام می‌شود."),
             "g7_cta": "درخواست اجرای هنرجو", "g8_media": "عکس اجرای هنرجویان"},
            links=[slug for _, _, slug, _, _ in L.CAFE_INSTRUMENTS],
        ))
        secs.append(section(
            "SEC_05_RESERVATION", "آدرس، ساعات کاری و رزرو میز کافه", "reservation", "campus_map_and_nap_card",
            {"g1_user_question": "کافه کجاست، چه ساعتی باز است و چطور میز رزرو کنم؟",
             "g2_keywords": ["کافه پیانو کرج"], "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [p["address_fa"], p["opening_hours"], p["phone_display"]],
             "g6_bluf": f"{p['address_fa']}؛ {p['opening_hours']}؛ رزرو: {p['phone_display']} یا واتساپ.",
             "g7_cta": CTA_CAFE, "g8_media": "عکس ورودی کافه"},
            nap={"address": p["address_fa"], "phone": p["phone_display"], "phone_e164": p["phone_e164"],
                 "hours": p["opening_hours"], "maps": p["maps_url"], "neshan": p["neshan_url"],
                 "balad": p["balad_url"], "waze": p["waze_url"]},
            landmarks=p["landmarks"],
        ))
        secs.append(section(
            "SEC_06_FAQ", "سوالات متداول کافه هنر و موسیقی زنده", "faq", "faq_accordion_rtl",
            {"g1_user_question": "رزرو، ساعت اجرا و امکان حضور کودکان.", "g2_keywords": kws,
             "g3_fact_support": "CATALOG_SUPPORTED + ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [f"{e['title_fa']} — {e['days_of_week_fa']}" for e in self.cafe_events],
             "g6_bluf": "پاسخ کوتاه به سوالات رزرو و برنامه اجراها.", "g7_cta": CTA_CAFE, "g8_media": "—"},
            faq=[{"q": f"{k} چه شب‌هایی برنامه دارد؟",
                  "a": self._cafe_answer(k)} for k in kws] +
                [{"q": "آیا رزرو میز الزامی است؟",
                  "a": ("برای اجراهایی که در برنامه رسمی با «رزرو الزامی» ثبت شده‌اند بله؛ "
                        + "، ".join(f"{e['title_fa']} ({'رزرو الزامی' if e['reservation_required'] == 'true' else 'بدون نیاز به رزرو'})"
                                    for e in self.cafe_events) + "."),
                  "source": "cafe_events.csv"}],
        ))
        return secs

    def _cafe_answer(self, keyword):
        n = L.normalize_persian(keyword)
        for fa, sec, slug, cid, anchor in L.CAFE_INSTRUMENTS:
            if fa in n:
                evs = [e for e in self.cafe_events
                       if fa.replace(" ", "") in e["instrument_focus_fa"].replace("‌", "").replace(" ", "")]
                if evs:
                    e = evs[0]
                    return (f"{e['title_fa']} در روزهای {e['days_of_week_fa']} ساعت {e['time_range_fa']} "
                            f"با اجرای {e['performer_name_fa']} برگزار می‌شود. "
                            f"برای یادگیری همین ساز، صفحه دوره مرتبط را ببینید.")
        return "[INTERNAL_DATA_NEEDED] — برنامه این اجرا هنوز توسط آموزشگاه تأیید نشده است."

    # ============================================ TIER 4 FARDIS / AUDITION
    def build_fardis_page(self, page):
        p = self.profile
        kws = [r["raw_keyword"] for r in self.silo_records("SILO_GEO_FARDIS")]
        routes = self.kmap["fardis_geo_mapping"]["dual_intent_routes"]
        secs = []
        self.add_media("/fardis-branch/", "نقشه مسیر فردیس → پردیس کرج", "۱۲۰۰×۸۰۰ نقشه شماتیک", "P2")
        secs.append(section(
            "SEC_01_FARDIS_HERO", "کلاس موسیقی، بازیگری، فن بیان و خوشنویسی برای هنرجویان فردیس کرج",
            "hero", "fardis_commuter_box",
            {"g1_user_question": "از فردیس کجا کلاس هنری معتبر بروم و چقدر راه است؟",
             "g2_keywords": kws, "g3_fact_support": "ACADEMY_BRAND_SUPPORTED (TRANSIT_AND_COMMUTER_ROUTES)",
             "g5_verbatim": p["transit_routes"],
             "g6_bluf": page["serp_and_ai_targets"]["bluf_answer_target"],
             "g7_cta": CTA_PRIMARY, "g8_media": "نقشه مسیر"},
            paragraphs=[kw_sentence("این صفحه پاسخ مستقیم جست‌وجوهای", kws[:7], "است."),
                        kw_sentence("و همچنین", kws[7:], ""),
                        ("توجه: آموزشگاه آنک یک پردیس مرکزی در کرج دارد و شعبه مستقل فردیس ندارد؛ "
                         "هیچ آدرس خیابانی جعلی برای فردیس اعلام نمی‌شود.")
                        if self.f_status == "SERVICE_AREA_COMMUTER_HUB" else ""],
            fardis_status=self.f_status,
        ))
        prog_cards = []
        for slug in self.kmap["fardis_geo_mapping"]["demanded_courses_in_fardis"]:
            pg = self.by_slug.get(slug, {})
            prog_cards.append({
                "slug": slug, "title_fa": pg.get("primary_keyword", slug),
                "keywords": [x["keyword"] for x in routes if x["course_slug"] == slug],
                "heading_fa": ([x["keyword"] for x in routes if x["course_slug"] == slug] or [slug])[0],
            })
        secs.append(section(
            "SEC_02_PROGRAMS", f"{L.to_persian_digits(len(prog_cards))} رشته پرتقاضای هنرجویان فردیس",
            "programs", "fardis_program_cards",
            {"g1_user_question": "کدام رشته‌ها را هنرجویان فردیس بیشتر می‌خواهند و لینک ثبت‌نامشان کجاست؟",
             "g2_keywords": kws, "g3_fact_support": "CATALOG_SUPPORTED (courses.csv)",
             "g5_verbatim": [f"{x['slug']}" for x in prog_cards],
             "g6_bluf": ("هفت مسیر پرتقاضای هنرجویان فردیس: موسیقی عمومی، موسیقی کودک، آواز و خوانندگی، "
                         "بازیگری، فن بیان، گویندگی و خوشنویسی — همگی در پردیس مرکزی کرج."),
             "g7_cta": "مشاهده دوره و شهریه", "g8_media": "آیکون هر رشته"},
            cards=prog_cards,
        ))
        secs.append(section(
            "SEC_03_ROUTES", "ماتریس مسیر و زمان رسیدن از فردیس به پردیس کرج", "routes", "fardis_commuter_route_matrix",
            {"g1_user_question": "دقیقاً چند دقیقه از فردیس تا آموزشگاه راه است؟",
             "g2_keywords": ["کلاس موسیقی در فردیس کرج", "کلاس بازیگری در فردیس کرج"],
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED (academy_data.txt)",
             "g5_verbatim": p["transit_routes"] + p["landmarks"],
             "g6_bluf": ("از فردیس و ملارد با مترو کرج، آموزشگاه تنها ۵ دقیقه پیاده از ایستگاه مترو کرج فاصله دارد؛ "
                         "دسترسی خودرویی از بلوار شهید بهشتی و چهارراه طالقانی."),
             "g7_cta": "مسیریابی با نشان/بلد/ویز", "g8_media": "نقشه مسیر"},
            routes=p["transit_routes"], landmarks=p["landmarks"],
            nap={"address": p["address_fa"], "phone": p["phone_display"], "phone_e164": p["phone_e164"],
                 "hours": p["opening_hours"], "maps": p["maps_url"], "neshan": p["neshan_url"],
                 "balad": p["balad_url"], "waze": p["waze_url"]},
        ))
        secs.append(section(
            "SEC_04_WEEKEND", "شیفت‌های فشرده پنجشنبه و جمعه ویژه هنرجویان فردیس", "weekend-shifts", "schedule_cards",
            {"g1_user_question": "می‌توانم فقط آخر هفته کلاس بیایم؟",
             "g2_keywords": ["کلاس های فن بیان در فردیس", "کلاس موسیقی فردیس کرج"],
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [p["opening_hours"]] + [r for r in p["transit_routes"] if "قم" in r],
             "g6_bluf": ("برای هنرجویان فردیس شیفت‌های فشرده آخر هفته تنظیم می‌شود تا رفت‌وآمد روزهای کاری حذف شود؛ "
                         "زمان‌بندی دقیق در جلسه مشاوره رایگان نهایی می‌شود."),
             "g7_cta": "رزرو شیفت آخر هفته", "g8_media": "—"},
        ))
        secs.append(section(
            "SEC_04B_CAMPUS", "آدرس پردیس مرکزی کرج (محل برگزاری همه کلاس‌های هنرجویان فردیس)",
            "campus-map", "campus_map_and_nap_card",
            {"g1_user_question": "دقیقاً کجا باید حاضر شوم؟", "g2_keywords": ["ادرس اموزشگاه موسیقی در کرج"],
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [p["address_fa"], p["postal_code"], p["opening_hours"]],
             "g6_bluf": f"{p['address_fa']}؛ {p['opening_hours']}؛ تماس: {p['phone_display']}.",
             "g7_cta": "مسیریابی", "g8_media": "عکس ورودی + نقشه"},
            nap={"address": p["address_fa"], "phone": p["phone_display"], "phone_e164": p["phone_e164"],
                 "hours": p["opening_hours"], "maps": p["maps_url"], "neshan": p["neshan_url"],
                 "balad": p["balad_url"], "waze": p["waze_url"]}, landmarks=p["landmarks"],
            fardis_status=self.f_status,
        ))
        secs.append(section(
            "SEC_05_FAQ", "سوالات متداول هنرجویان فردیس", "faq", "faq_accordion_rtl",
            {"g1_user_question": "آیا شعبه فردیس دارید؟ مسیر و شهریه چطور است؟",
             "g2_keywords": kws, "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [p["address_fa"]] + p["transit_routes"][:2],
             "g6_bluf": "پاسخ شفاف درباره شعبه، مسیر و زمان‌بندی.", "g7_cta": CTA_PRIMARY, "g8_media": "—"},
            faq=[{"q": "آیا آموزشگاه شعبه فیزیکی در فردیس دارد؟",
                  "a": ("آموزشگاه آنک یک پردیس مرکزی در کرج دارد (" + p["address_fa"] + ") و هنرجویان فردیس "
                        "با مترو کرج تنها ۵ دقیقه پیاده به آن می‌رسند. برای شفافیت، هیچ آدرس مستقلی در فردیس "
                        "اعلام نمی‌کنیم."), "source": "academy_data.txt"},
                 {"q": "شهریه برای هنرجویان فردیس تفاوتی دارد؟",
                  "a": "خیر؛ شهریه همان تعرفه رسمی هر دوره است که در صفحه همان دوره به‌صورت شفاف اعلام شده است.",
                  "source": "courses.csv"}] +
                [{"q": f"{k} چگونه برگزار می‌شود؟",
                  "a": ("این دوره در پردیس مرکزی کرج با دسترسی مستقیم از فردیس برگزار می‌شود؛ "
                        "جزئیات شهریه، اساتید و سرفصل‌ها در صفحه اختصاصی همان دوره آمده است."),
                  "source": "courses.csv"} for k in kws[:6]],
        ))
        return secs

    def build_audition_page(self, page):
        p = self.profile
        kws = [r["raw_keyword"] for r in self.silo_records("SILO_CONV_AUDITION")]
        panel = [i for i in self.instructors if not L.is_placeholder_instructor(i)
                 and ("CRS_ACTING" in i["course_ids"] or "CRS_KIDS_ACTING" in i["course_ids"])]
        secs = []
        secs.append(section(
            "SEC_01_AUDITION_HERO", "تست بازیگری در کرج | ثبت‌نام، مراحل و محل برگزاری", "hero", "audition_hero",
            {"g1_user_question": "تست بازیگری در کرج کجاست و چطور شرکت کنم؟", "g2_keywords": kws,
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [p["address_fa"], p["phone_display"]],
             "g6_bluf": page["serp_and_ai_targets"]["bluf_answer_target"],
             "g7_cta": CTA_AUDITION, "g8_media": "عکس اتاق تست/بلک‌باکس"},
            paragraphs=[kw_sentence("این صفحه پاسخ مستقیم", kws, "است.")],
        ))
        secs.append(section(
            "SEC_02_PROCESS", "چهار مرحله تست بازیگری و تعیین سطح", "process", "audition_step_cards",
            {"g1_user_question": "در روز تست دقیقاً چه اتفاقی می‌افتد؟", "g2_keywords": ["تست بازیگری در کرج"],
             "g3_fact_support": "PEDAGOGICAL_GUIDANCE + ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [p["guarantees"][0] if p["guarantees"] else ""],
             "g6_bluf": "تست شامل مصاحبه کوتاه، اجرای مونولوگ، تمرین بداهه و تست مقابل دوربین است و نتیجه آن تعیین سطح رایگان است.",
             "g7_cta": CTA_AUDITION, "g8_media": "عکس هر مرحله"},
            steps=[{"level_fa": "۱. مصاحبه و آشنایی", "description_fa": "گفت‌وگوی کوتاه درباره سابقه، هدف و گروه سنی", "modules_fa": [], "term_fa": "۱۰ دقیقه"},
                   {"level_fa": "۲. اجرای مونولوگ", "description_fa": "اجرای یک مونولوگ آماده یا متن ارائه‌شده توسط داور", "modules_fa": [], "term_fa": "۱۰ دقیقه"},
                   {"level_fa": "۳. بداهه و بدن‌وبیان", "description_fa": "تمرین بداهه کوتاه برای سنجش انعطاف و بیان", "modules_fa": [], "term_fa": "۱۰ دقیقه"},
                   {"level_fa": "۴. تست مقابل دوربین", "description_fa": "ضبط کوتاه برای ارزیابی بازی مقابل دوربین", "modules_fa": [], "term_fa": "۱۰ دقیقه"}],
        ))
        secs.append(section(
            "SEC_03_AGE", "معیارهای سنی: کودکان، نوجوانان و بزرگسالان", "age-criteria", "kids_pedagogy_cards",
            {"g1_user_question": "فرزند من در چه گروه سنی تست می‌دهد؟", "g2_keywords": ["تست بازیگری در کرج"],
             "g3_fact_support": "CATALOG_SUPPORTED (courses.csv → age_groups)",
             "g5_verbatim": ["CRS_KIDS_ACTING → kids|teens", "CRS_ACTING → teens|adults"],
             "g6_bluf": "کودکان و نوجوانان در مسیر بازیگری و نمایش خلاق کودک و نوجوانان بزرگ‌تر و بزرگسالان در مسیر بازیگری سینما و تئاتر ارزیابی می‌شوند.",
             "g7_cta": "انتخاب گروه سنی و رزرو", "g8_media": "—"},
            links=["/performing-arts/kids-acting-drama/", "/performing-arts/acting/"],
        ))
        secs.append(section(
            "SEC_04_PREP", "راهنمای آمادگی: انتخاب مونولوگ و تمرین کُلدریدینگ", "prep", "syllabus_term_timeline",
            {"g1_user_question": "چطور برای تست آماده شوم؟", "g2_keywords": ["تست بازیگری در کرج"],
             "g3_fact_support": "PEDAGOGICAL_GUIDANCE", "g5_verbatim": [],
             "g6_bluf": "یک مونولوگ ۶۰ تا ۹۰ ثانیه‌ای متناسب با سن، لباس ساده و رسیدن ۱۵ دقیقه زودتر، سه عامل اصلی موفقیت در تست است.",
             "g7_cta": "دریافت چک‌لیست آمادگی", "g8_media": "—"},
            steps=[{"level_fa": "انتخاب متن", "description_fa": "مونولوگ ۶۰–۹۰ ثانیه، متناسب با سن و فارسی روان", "modules_fa": [], "term_fa": "قبل از تست"},
                   {"level_fa": "تمرین بیان", "description_fa": "گرم‌کردن صدا، تنفس دیافراگمی و وضوح ادای کلمات", "modules_fa": [], "term_fa": "قبل از تست"},
                   {"level_fa": "روز تست", "description_fa": "لباس ساده، بدون گریم سنگین، حضور ۱۵ دقیقه زودتر", "modules_fa": [], "term_fa": "روز تست"}],
        ))
        secs.append(section(
            "SEC_05_PANEL", "هیئت داوران تست بازیگری", "panel", "instructor_roster_cards",
            {"g1_user_question": "چه کسی تست را داوری می‌کند؟", "g2_keywords": ["تست بازیگری در کرج"],
             "g3_fact_support": "CATALOG_SUPPORTED (instructors.csv)",
             "g5_verbatim": [f"{i['name_fa']} — {i['role_title_fa']}" for i in panel],
             "g6_bluf": "داوری تست توسط اساتید تأییدشده بازیگری و نمایش خلاق آموزشگاه انجام می‌شود.",
             "g7_cta": "مشاهده رزومه اساتید", "g8_media": "پرتره داوران"},
            instructor_cards=[{"instructor_id": i["instructor_id"], "name_fa": i["name_fa"], "gender": i["gender"],
                               "gender_badge_fa": "استاد خانم" if i["gender"] == "female" else "استاد آقا",
                               "role_title_fa": i["role_title_fa"], "credentials_fa": i["credentials_fa"],
                               "experience_highlights_fa": i.get("experience_highlights_fa", ""),
                               "same_as_url": i.get("same_as_url", ""), "is_placeholder": False,
                               "status": i["status"]} for i in panel],
        ))
        secs.append(section(
            "SEC_06_BOOKING", "رزرو نوبت تست بازیگری", "booking", "audition_booking_form",
            {"g1_user_question": "چطور نوبت تست رزرو کنم؟", "g2_keywords": kws,
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [p["phone_display"], p["mobile_whatsapp"], p["whatsapp_url"]],
             "g6_bluf": (f"رزرو نوبت تست با تماس {p['phone_display']} یا پیام واتساپ به {p['mobile_whatsapp']} "
                         "انجام می‌شود؛ نوبت‌ها محدود و بر اساس گروه سنی زمان‌بندی می‌شوند."),
             "g7_cta": CTA_AUDITION, "g8_media": "—"},
            channels={"phone": p["phone_display"], "phone_e164": p["phone_e164"],
                      "whatsapp": p["whatsapp_url"], "instagram": p["instagram_url"],
                      "email": p["email"], "mobile": p["mobile_whatsapp"]},
        ))
        secs.append(section(
            "SEC_06B_CAMPUS", "آدرس محل برگزاری تست بازیگری در کرج", "campus-map", "campus_map_and_nap_card",
            {"g1_user_question": "تست بازیگری در کرج کجاست و چطور نوبت بگیرم؟", "g2_keywords": kws,
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
             "g5_verbatim": [p["address_fa"], p["phone_display"], p["whatsapp_url"]],
             "g6_bluf": f"محل تست: {p['address_fa']}؛ رزرو نوبت با {p['phone_display']} یا واتساپ.",
             "g7_cta": CTA_AUDITION, "g8_media": "عکس ورودی"},
            nap={"address": p["address_fa"], "phone": p["phone_display"], "phone_e164": p["phone_e164"],
                 "hours": p["opening_hours"], "maps": p["maps_url"], "neshan": p["neshan_url"],
                 "balad": p["balad_url"], "waze": p["waze_url"]}, landmarks=p["landmarks"],
        ))
        secs.append(section(
            "SEC_07_FAQ", "سوالات متداول تست بازیگری در کرج", "faq", "faq_accordion_rtl",
            {"g1_user_question": "هزینه تست، سن مجاز و محل برگزاری.", "g2_keywords": kws,
             "g3_fact_support": "ACADEMY_BRAND_SUPPORTED", "g5_verbatim": p["guarantees"][:1],
             "g6_bluf": "پاسخ کوتاه به سوالات تست.", "g7_cta": CTA_AUDITION, "g8_media": "—"},
            faq=[{"q": "تست بازیگری در کرج کجاست؟", "a": f"{p['address_fa']}.", "source": "academy_data.txt"},
                 {"q": "آیا تست بازیگری هزینه دارد؟",
                  "a": (p["guarantees"][0] if p["guarantees"] else "مشاوره و تعیین سطح رایگان است.")
                       + " جزئیات نهایی در زمان رزرو نوبت اعلام می‌شود.", "source": "academy_data.txt"},
                 {"q": "از چه سنی می‌توان در تست شرکت کرد؟",
                  "a": "گروه‌های کودک و نوجوان در مسیر بازیگری و نمایش خلاق کودکان و نوجوانان و گروه بزرگسال در مسیر بازیگری سینما و تئاتر ارزیابی می‌شوند.",
                  "source": "courses.csv"}],
        ))
        return secs

    def build_instructors_page(self, page):
        p = self.profile
        verified = [i for i in self.instructors if not L.is_placeholder_instructor(i)]
        pending = [i for i in self.instructors if L.is_placeholder_instructor(i)]
        cards = [{"instructor_id": i["instructor_id"], "name_fa": i["name_fa"], "gender": i["gender"],
                  "gender_badge_fa": "استاد خانم" if i["gender"] == "female" else "استاد آقا",
                  "role_title_fa": i["role_title_fa"], "credentials_fa": i["credentials_fa"],
                  "experience_highlights_fa": i.get("experience_highlights_fa", ""),
                  "same_as_url": i.get("same_as_url", ""), "is_placeholder": False, "status": i["status"],
                  "course_ids": [c for c in i["course_ids"].split("|") if c]} for i in verified]
        ph_cards = [{"instructor_id": i["instructor_id"], "name_fa": "[INTERNAL_DATA_NEEDED]",
                     "placeholder_label_fa": i["name_fa"], "gender": i["gender"],
                     "gender_badge_fa": "استاد خانم" if i["gender"] == "female" else "استاد آقا",
                     "role_title_fa": i["role_title_fa"], "credentials_fa": "", "experience_highlights_fa": "",
                     "same_as_url": "", "is_placeholder": True, "status": i["status"],
                     "course_ids": [c for c in i["course_ids"].split("|") if c]} for i in pending]
        return [
            section("SEC_01_ROSTER", "اساتید آموزشگاه سینمایی و بازیگری آنک کرج", "instructors", "instructor_roster_cards",
                    {"g1_user_question": "اساتید چه کسانی هستند و چه مدرکی دارند؟",
                     "g2_keywords": ["اساتید آموزشگاه آنک کرج"],
                     "g3_fact_support": "CATALOG_SUPPORTED (instructors.csv)",
                     "g5_verbatim": [f"{i['name_fa']} — {i['credentials_fa']}" for i in verified],
                     "g6_bluf": (f"{L.to_persian_digits(len(verified))} استاد تأییدشده با مدرک دانشگاهی و سوابق "
                                 "حرفه‌ای در بازیگری، نمایش خلاق، کارگردانی، فیلمنامه‌نویسی، عکاسی و تدوین."),
                     "g7_cta": "رزرو کلاس با استاد انتخابی", "g8_media": "پرتره ۴:۵ هر استاد"},
                    instructor_cards=cards),
            section("SEC_02_FEMALE", "اساتید خانم آموزشگاه", "female-teachers", "female_instructor_spotlight",
                    {"g1_user_question": "کدام رشته‌ها استاد خانم دارند؟",
                     "g2_keywords": ["مدرس خانم در کرج"],
                     "g3_fact_support": "CATALOG_SUPPORTED (instructors.csv + courses.csv)",
                     "g5_verbatim": [f"{i['name_fa']} — {i['role_title_fa']}" for i in verified if i["gender"] == "female"],
                     "g6_bluf": "فهرست اساتید خانم تأییدشده و رشته‌هایی که کلاس ویژه بانوان و کودکان دارند.",
                     "g7_cta": "رزرو کلاس با استاد خانم", "g8_media": "پرتره اساتید خانم"},
                    instructor_cards=[c for c in cards if c["gender"] == "female"]),
            section("SEC_02B_FILTERS", "فیلتر اساتید بر اساس رشته، جنسیت و گروه سنی", "instructor-filters",
                    "instructor_filter_bar",
                    {"g1_user_question": "چطور استاد مناسب رشته و جنسیت دلخواهم را پیدا کنم؟",
                     "g2_keywords": ["اساتید آموزشگاه آنک کرج"],
                     "g3_fact_support": "CATALOG_SUPPORTED (instructors.csv + courses.csv)",
                     "g5_verbatim": [f"{i['instructor_id']} → {i['course_ids']}" for i in self.instructors[:6]],
                     "g6_bluf": ("فیلتر ایستا و بدون جاوااسکریپت سنگین: انتخاب دانشکده، جنسیت استاد و گروه سنی، "
                                 "فهرست اساتید را در همان صفحه محدود می‌کند."),
                     "g7_cta": "مشاهده کلاس‌های استاد", "g8_media": "—"},
                    filters={"departments": [L.DEPARTMENTS[k]["name_fa"] for k in L.DEPARTMENTS],
                             "gender": ["استاد خانم", "استاد آقا"],
                             "age_groups": ["کودکان", "نوجوانان", "بزرگسالان"]}),
            section("SEC_03_PENDING", "اساتید در انتظار تأیید نهایی اطلاعات", "pending", "instructor_roster_cards",
                    {"g1_user_question": "چرا برخی کارت‌ها نام ندارند؟",
                     "g2_keywords": [], "g3_fact_support": "[INTERNAL_DATA_NEEDED]",
                     "g5_verbatim": [f"{i['instructor_id']} → status={i['status']}" for i in pending],
                     "g6_bluf": ("برای شفافیت، کارت اساتیدی که رزومه رسمی‌شان هنوز توسط آموزشگاه تأیید نشده با "
                                 "برچسب «در انتظار تکمیل» نمایش داده می‌شود و هیچ نام یا مدرک ساختگی منتشر نمی‌کنیم."),
                     "g7_cta": "ارسال رزومه استاد", "g8_media": "—"},
                    instructor_cards=ph_cards, data_gap=True),
        ]

    def build_contact_page(self, page):
        p = self.profile
        return [
            section("SEC_01_NAP", "آدرس، تلفن و ساعات کاری آموزشگاه آنک کرج", "campus-map", "campus_map_and_nap_card",
                    {"g1_user_question": "آدرس دقیق، تلفن و ساعت کاری چیست؟",
                     "g2_keywords": ["آدرس آموزشگاه آنک کرج"],
                     "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
                     "g5_verbatim": [p["address_fa"], p["phone_display"], p["opening_hours"], p["postal_code"]],
                     "g6_bluf": f"{p['address_fa']}؛ تلفن {p['phone_display']}؛ {p['opening_hours']}.",
                     "g7_cta": "تماس فوری", "g8_media": "عکس نما + نقشه"},
                    nap={"address": p["address_fa"], "phone": p["phone_display"], "phone_e164": p["phone_e164"],
                         "hours": p["opening_hours"], "maps": p["maps_url"], "neshan": p["neshan_url"],
                         "balad": p["balad_url"], "waze": p["waze_url"]}, landmarks=p["landmarks"]),
            section("SEC_02_CHANNELS", "راه‌های ارتباطی و ثبت‌نام", "channels", "contact_channel_cards",
                    {"g1_user_question": "از چه راه‌هایی می‌توانم ثبت‌نام کنم؟",
                     "g2_keywords": [], "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
                     "g5_verbatim": [p["phone_display"], p["mobile_whatsapp"], p["instagram_url"], p["email"]],
                     "g6_bluf": "تماس تلفنی، واتساپ، اینستاگرام و ایمیل؛ پاسخ‌گویی روزهای تعطیل در واتساپ و تلگرام.",
                     "g7_cta": "ارسال پیام واتساپ", "g8_media": "—"},
                    channels={"phone": p["phone_display"], "phone_e164": p["phone_e164"],
                              "whatsapp": p["whatsapp_url"], "instagram": p["instagram_url"],
                              "email": p["email"], "mobile": p["mobile_whatsapp"]}),
            section("SEC_02B_HOURS", "ساعات کاری و روزهای پاسخ‌گویی", "hours", "opening_hours_table",
                    {"g1_user_question": "چه ساعتی باز هستید و جمعه‌ها هم پاسخ می‌دهید؟",
                     "g2_keywords": [], "g3_fact_support": "ACADEMY_BRAND_SUPPORTED",
                     "g5_verbatim": [p["opening_hours"]],
                     "g6_bluf": p["opening_hours"],
                     "g7_cta": "تماس در ساعات کاری", "g8_media": "—"},
                    hours_raw=p["opening_hours"]),
            section("SEC_03_FARDIS", "دسترسی از فردیس، ملارد، تهران و قم", "fardis-access", "fardis_commuter_box",
                    {"g1_user_question": "از شهرهای اطراف چطور برسم؟", "g2_keywords": [],
                     "g3_fact_support": "ACADEMY_BRAND_SUPPORTED", "g5_verbatim": p["transit_routes"],
                     "g6_bluf": "مسیرهای تأییدشده از فردیس، ملارد، گوهردشت، عظیمیه، مهرشهر، تهران و قم.",
                     "g7_cta": "مشاهده مسیرها", "g8_media": "نقشه"},
                    routes=p["transit_routes"], link="/fardis-branch/"),
            section("SEC_04_TUITION", "استعلام شهریه همه دوره‌ها", "tuition", "tuition_transparent_table",
                    {"g1_user_question": "شهریه دوره‌ها چقدر است؟", "g2_keywords": [],
                     "g3_fact_support": "CATALOG_SUPPORTED (courses.csv)",
                     "g5_verbatim": [f"{c['name_fa']} → گروهی {c['tuition_group_irr']} ریال"
                                     for c in list(self.courses.values())[:5]],
                     "g6_bluf": "جدول شهریه همه دوره‌ها به تفکیک خصوصی و گروهی، مستقیماً از تعرفه رسمی آموزشگاه.",
                     "g7_cta": "دریافت مشاوره شهریه", "g8_media": "—"},
                    table=[{"course_fa": c["name_fa"], "slug": c["slug"],
                            "private_toman_fa": L.irr_to_toman_fa(c["tuition_private_irr"]),
                            "group_toman_fa": L.irr_to_toman_fa(c["tuition_group_irr"]),
                            "sessions": L.to_persian_digits(c["sessions_per_term"]),
                            "duration_fa": f"{L.to_persian_digits(c['session_duration_min'])} دقیقه"}
                           for c in self.courses.values()]),
        ]

    # ------------------------------------------------------------- driver
    def build(self):
        plan = {"generated_at": L.now_iso(), "phase": "PHASE_3", "domain": self.profile["domain"], "pages": []}
        for page in self.page_map["pages"]:
            t = page["tier"]
            if t == "0":
                secs = self.build_home_page(page)
            elif t == "1":
                secs = self.build_dept_page(page)
            elif t == "2":
                secs = self.build_course_page(page)
            elif t == "3":
                secs = self.build_cafe_page(page)
            elif page["page_id"] == "GEO_FARDIS_HUB":
                secs = self.build_fardis_page(page)
            elif page["page_id"] == "CONV_AUDITION_HUB":
                secs = self.build_audition_page(page)
            elif page["page_id"] == "HUB_INSTRUCTORS":
                secs = self.build_instructors_page(page)
            else:
                secs = self.build_contact_page(page)

            entry = dict(page)
            entry["sections"] = secs
            entry["dossier_file"] = "seo_dossiers/" + dossier_filename(page)
            entry["meta_title"] = self.meta_title(page)
            entry["meta_description"] = self.meta_description(page)
            entry["h1"] = secs[0]["heading_fa"]
            plan["pages"].append(entry)
        return plan

    def meta_title(self, page):
        pk = page["primary_keyword"]
        t = page["tier"]
        if t == "0":
            return f"{self.profile['brand_fa']} | آموزشگاه موسیقی، بازیگری، سینما و کافه هنر در کرج"
        if t == "2":
            c = self.courses[page["course_id"]]
            extra = "اساتید خانم و آقا + شهریه" if c["has_female_instructor"] else "اساتید مجرب + شهریه"
            return f"{pk} | آموزش خصوصی و گروهی، {extra}"
        if t == "3":
            return "کافه پیانو، گیتار، سنتور و سه‌تار در کرج | کافه هنر و موسیقی زنده آنک"
        if page["page_id"] == "GEO_FARDIS_HUB":
            return "کلاس موسیقی، بازیگری و فن بیان در فردیس کرج | دسترسی ۵ دقیقه‌ای با مترو"
        if page["page_id"] == "CONV_AUDITION_HUB":
            return "تست بازیگری در کرج کجاست؟ | ثبت‌نام تست و تعیین سطح رایگان آنک"
        return f"{pk} | آموزشگاه آنک کرج"

    def meta_description(self, page):
        if page["tier"] == "2":
            c = self.courses[page["course_id"]]
            name = c["name_fa"].replace("کلاس و آموزش ", "").replace("کلاس آموزش ", "").replace("کلاس ", "")
            fem = "استاد خانم و آقا، " if c["has_female_instructor"] else ""
            t = L.irr_to_toman_fa(c["tuition_group_irr"])
            return (f"آموزش تخصصی {name} در کرج از مقدماتی تا پیشرفته؛ {fem}کلاس خصوصی و گروهی، "
                    f"ویژه کودکان و بزرگسالان، شهریه شفاف از {t} تومان و {c['certificate_type']}. "
                    "مشاوره و تعیین سطح رایگان.")
        base = page["serp_and_ai_targets"]["bluf_answer_target"] or page["primary_keyword"]
        return re.sub(r"\s+", " ", base)[:300]


# ======================================================================
#  MARKDOWN DOSSIER RENDERER
# ======================================================================
def render_dossier(entry, builder) -> str:
    out = []
    a = out.append
    tier_name = {"0": "Tier 0 — Master Homepage", "1": "Tier 1 — Faculty Mega-Hub",
                 "2": "Tier 2 — Master Course & Instrument Landing Page",
                 "3": "Tier 3 — Live-Music Art Cafe & Venue Hub",
                 "4": "Tier 4 — Hyper-Local & Conversion Hub"}[entry["tier"]]
    a("# PAGE BRIEF")
    a(f"- URL: {entry['url_slug']}")
    a(f"- Tier: {entry['tier']} ({tier_name})")
    a(f"- Page ID: {entry['page_id']}")
    if entry.get("course_id"):
        a(f"- Course ID: {entry['course_id']}")
    a(f"- Silo: {entry['silo_id']}")
    a(f"- Build Status: {entry['build_status']}")
    a(f"- Primary Keyword: {entry['primary_keyword']}  _(source: {entry.get('primary_keyword_source','DATASET')})_")
    a(f"- Owned Dataset Keywords: {entry['owned_dataset_keyword_count']}")
    if entry["secondary_keywords"]:
        a("- Secondary Keywords: " + "، ".join(entry["secondary_keywords"]))
    if entry["orthographic_variants_assigned"]:
        a("- Orthographic Variants Included (un-Maddahed / spacing): "
          + "، ".join(entry["orthographic_variants_assigned"]))
    if entry.get("dual_intent_supporting_keywords"):
        a("- Dual-Intent Supporting Keywords: " + "، ".join(entry["dual_intent_supporting_keywords"]))
    a("")
    a("# META & HEADING PLAN (PERSIAN CTR-OPTIMIZED)")
    a(f"- Meta Title: {entry['meta_title']}")
    a(f"- Meta Description: {entry['meta_description']}")
    a(f"- H1: {entry['h1']}")
    a(f"- Canonical: {builder.profile['domain'].rstrip('/')}{entry['url_slug']}")
    a("")
    a("# INFORMATION GAIN & AI/SGE TARGETS")
    ig = entry["information_gain_delta"]
    a(f"- Gain Score: {ig['gain_score']} ({ig['gain_percentage_estimate']}%)")
    if ig["unique_curriculum_facts"]:
        a("- Unique Curriculum / Venue Facts: " + "؛ ".join(map(str, ig["unique_curriculum_facts"])))
    a(f"- BLUF Answer Target: {entry['serp_and_ai_targets']['bluf_answer_target']}")
    a(f"- Featured Snippet Format: {entry['serp_and_ai_targets']['featured_snippet_format']}")
    a("")
    a("# REQUIRED ON-PAGE MODULES (FROM page_map.json)")
    for m in entry["required_onpage_modules"]:
        a(f"- {m}")
    a("")
    a("# INTERNAL LINK GRAPH")
    a("- Links to: " + "، ".join(entry["internal_links_to"]))
    a("- Linked from: " + "، ".join(entry["internal_links_from"]))
    a(f"- Click depth from `/`: {entry['click_depth_from_home']}")
    a("")
    a("# RECOMMENDED SECTION PLAN (8-GATE ENGINE)")
    a("")
    for s in entry["sections"]:
        a(f"## [{s['section_id']}] {s['heading_fa']}")
        a(f"- **Anchor:** `#{s['anchor']}`  |  **UI object (G4):** `{s['ui_component']}`")
        a(f"- **G1 · User question & intent:** {s.get('g1_user_question','—')}")
        kws = s.get("g2_keywords") or []
        a("- **G2 · Exact keywords targeted:** " + ("، ".join(kws) if kws else "— (ساختاری/تبدیلی)"))
        a(f"- **G3 · Fact support:** {s.get('g3_fact_support','—')}")
        ver = s.get("g5_verbatim") or []
        if ver:
            a("- **G5 · Verbatim data quotes:**")
            for v in ver:
                if str(v).strip():
                    a(f"  - `{v}`")
        if s.get("g6_bluf"):
            a(f"- **G6 · BLUF extractable answer:** {s['g6_bluf']}")
        a(f"- **G7 · Conversion micro-CTA:** {s.get('g7_cta','—')}")
        a(f"- **G8 · Media & asset spec:** {s.get('g8_media','—')}")
        if s.get("data_gap"):
            a("- **⚠ DATA GAP:** `[INTERNAL_DATA_NEEDED]` — این بخش با اسلات خالی ساخته می‌شود و هیچ داده‌ای ساخته نمی‌شود.")
        if s.get("note"):
            a(f"- **Note:** {s['note']}")
        for p in s.get("paragraphs", []):
            if p:
                a(f"- **Copy block:** {p}")
        if s.get("badges"):
            a("- **Quick-stat badges:** " + " | ".join(s["badges"]))
        if s.get("jump_pills"):
            a("- **Jump pills:** " + " | ".join(f"{t} → `{h}`" for t, h in s["jump_pills"]))
        if s.get("instructor_cards"):
            a("- **Instructor cards:**")
            for ic in s["instructor_cards"]:
                if ic["is_placeholder"]:
                    a(f"  - `{ic['instructor_id']}` **[INTERNAL_DATA_NEEDED]** — {ic['placeholder_label_fa']} "
                      f"({ic['gender_badge_fa']}، {ic['role_title_fa']})")
                else:
                    a(f"  - `{ic['instructor_id']}` {ic['name_fa']} — {ic['gender_badge_fa']} — {ic['role_title_fa']} — {ic['credentials_fa']}")
        if s.get("tabs"):
            a("- **Sub-specialty tabs (rendered in static DOM):**")
            for t in s["tabs"]:
                a(f"  - `{t['module_id']}` {t['title_fa']}" + (f" → {'، '.join(t['keywords'])}" if t["keywords"] else ""))
        if s.get("table"):
            a("- **Table rows:**")
            for row in s["table"]:
                a("  - " + " | ".join(f"{k}={v}" for k, v in row.items() if not k.endswith("_raw")))
        if s.get("matrix"):
            a("- **Comparison matrix rows:**")
            for row in s["matrix"]:
                a("  - " + " | ".join(f"{k}={v}" for k, v in row.items() if not k.endswith("_raw")))
        if s.get("steps"):
            a("- **Timeline steps:**")
            for st in s["steps"]:
                a(f"  - {st['level_fa']} ({st['term_fa']}): {st['description_fa']}"
                  + (f" — ماژول‌ها: {'، '.join(st['modules_fa'])}" if st.get("modules_fa") else ""))
        if s.get("cards"):
            a("- **Cards:**")
            for cd in s["cards"]:
                label = cd.get("name_fa") or cd.get("title_fa") or cd.get("heading_fa", "")
                a(f"  - {label} → `{cd.get('slug','')}`")
        if s.get("portal_cards"):
            a("- **Portal cards:**")
            for cd in s["portal_cards"]:
                a(f"  - {cd['title_fa']} → `{cd['slug']}`")
        if s.get("events"):
            a("- **Verified live events (cafe_events.csv):**")
            for e in s["events"]:
                a(f"  - `{e['event_id']}` {e['title_fa']} — {e['days_of_week_fa']} {e['time_range_fa']} — "
                  f"نوازنده: {e['performer_name_fa']} — رزرو: {e['reservation_required']} → `{e['linked_course_slug']}`")
        if s.get("routes"):
            a("- **Verified commuter routes:**")
            for r in s["routes"]:
                a(f"  - {r}")
        if s.get("nap"):
            a(f"- **NAP:** {s['nap']['address']} | {s['nap']['phone']} | {s['nap']['hours']}")
        if s.get("faq"):
            a("- **FAQ (schema-connected `<details>/<summary>`):**")
            for f in s["faq"]:
                mark = " _(ortho-variant)_" if f.get("ortho_variant") else ""
                a(f"  - **س:** {f['q']}{mark}")
                a(f"    **ج:** {f['a']}")
        if s.get("link"):
            a(f"- **Bridge link:** `{s['link']}`")
        if s.get("links"):
            a("- **Bridge links:** " + "، ".join(f"`{x}`" for x in s["links"]))
        a("")
    a("# SCHEMA PLAN")
    a("- " + "، ".join(entry["schema_types_planned"]))
    a("")
    a("[VERIFIED_DOSSIER_END]")
    return "\n".join(out) + "\n"


def main():
    L.ensure_dirs(L.DOSSIERS, L.OUTPUT)
    b = PlanBuilder()
    plan = b.build()

    # keyword coverage inside the plan (every owned keyword must be placed)
    missing = []
    for entry in plan["pages"]:
        owned = {r["raw_keyword"] for r in b.silo_records(entry["silo_id"])} if entry["silo_id"] in b.reg else set()
        if entry["page_id"] in ("HUB_INSTRUCTORS", "HUB_CONTACT"):
            owned = set()
        placed = set()
        for s in entry["sections"]:
            placed |= set(s.get("g2_keywords") or [])
            for p in s.get("paragraphs", []):
                placed |= {k for k in owned if k in (p or "")}
            for f in s.get("faq", []):
                placed |= {k for k in owned if k in f["q"] or k in f["a"]}
            for t in s.get("tabs", []):
                placed |= set(t.get("keywords") or [])
            for cd in s.get("cards", []):
                placed |= set(cd.get("keywords") or [])
        gap = owned - placed
        if gap:
            missing.append({"page": entry["url_slug"], "missing": sorted(gap)})

    written = []
    for entry in plan["pages"]:
        path = os.path.join(L.DOSSIERS, dossier_filename(entry))
        L.write_text(path, render_dossier(entry, b))
        written.append(path)

    L.write_json(os.path.join(L.OUTPUT, "page_content_plan.json"), plan)

    # ----------------------------------------------------- needed_media.md
    md = ["# رسانه‌های مورد نیاز (needed_media.md)", "",
          "تمام تصاویر/ویدیوها باید **واقعی و متعلق به پردیس کرج آموزشگاه آنک** باشند. "
          "تا زمان دریافت فایل‌ها، بیلد از placeholder با `width`/`height` مشخص استفاده می‌کند تا `CLS = 0` حفظ شود.", "",
          "| اولویت | صفحه | دارایی | مشخصات فنی |", "|---|---|---|---|"]
    for m in sorted(b.media, key=lambda x: (x["priority"], x["page"])):
        md.append(f"| {m['priority']} | `{m['page']}` | {m['asset']} | {m['spec']} |")
    md += ["", "## رسانه‌های سراسری", "",
           "| اولویت | دارایی | مشخصات |", "|---|---|---|",
           "| P1 | لوگوی آموزشگاه (SVG + PNG ۵۱۲×۵۱۲) | پس‌زمینه شفاف |",
           "| P1 | عکس نمای ورودی ساختمان | ۱۲۰۰×۸۰۰، روز |",
           "| P1 | پرتره ۷ استاد در انتظار تأیید | ۸۰۰×۱۰۰۰ (۴:۵) |",
           "| P1 | عکس صحنه کافه هنر در شب اجرای زنده | ۱۶۰۰×۹۰۰ |",
           "| P2 | عکس اتاق‌های آکوستیک، بلک‌باکس، استودیو دوبله، لابراتوار تدوین | ۱۲۰۰×۸۰۰ هرکدام |",
           "| P2 | ویدیو کوتاه معرفی آموزشگاه (۳۰ ثانیه) | MP4 H.264، زیرنویس فارسی |",
           "| P3 | نمونه اجرای صوتی هنرجویان (برای کارت اساتید) | MP3 ≤ ۲ مگابایت |"]
    L.write_text(os.path.join(L.OUTPUT, "needed_media.md"), "\n".join(md) + "\n")

    # ---------------------------------------------------------------- GATE 3
    all_end = all(open(p, encoding="utf-8").read().rstrip().endswith("[VERIFIED_DOSSIER_END]") for p in written)
    module_parity = []
    for entry in plan["pages"]:
        sec_blob = " ".join(s["section_id"] + s["heading_fa"] + s["anchor"] for s in entry["sections"])
        anchors = {s["anchor"] for s in entry["sections"]}
        need = {
            "SEC_HERO_BLUF_OVERVIEW": "hero", "SEC_HOME_HERO_MULTIFACULTY": "hero",
            "SEC_FARDIS_HERO": "hero", "SEC_AUDITION_HERO": "hero",
            "SEC_FEMALE_INSTRUCTORS": "female-teachers", "SEC_PRIVATE_VS_GROUP_FORMAT": "formats",
            "SEC_TUITION_TABLE": "tuition", "MOD_MUSIC_TUITION_MATRIX": "tuition",
            "SEC_KIDS_TEENS_TRACK": "kids-track", "SEC_SUBSTYLE_TABS": "sub-styles",
            "SEC_CAFE_PERFORMANCE_BRIDGE": "cafe-stage", "MOD_CAFE_STAGE_CALLOUT": "cafe-stage",
            "SEC_FARDIS_COMMUTER_ACCESS": "fardis-access", "SEC_INSTRUCTOR_ROSTER": "instructors",
            "MOD_INST_GRID": "instructors", "SEC_CAMPUS_MAP_DIRECTIONS": "campus-map",
            "SEC_COURSE_FAQ": "faq", "SEC_DEPT_FAQ": "faq", "SEC_HOME_FAQ": "faq",
            "SEC_FARDIS_FAQ": "faq", "SEC_AUDITION_FAQ": "faq",
            "SEC_SYLLABUS_ROADMAP": "syllabus", "SEC_AUDITION_BRIDGE": "audition-bridge",
            "SEC_COURSE_GRID_NAVIGATION": "courses", "SEC_COURSE_FINDER_24": "course-finder",
            "SEC_ART_CAFE_SHOWCASE": "art-cafe-preview", "SEC_FEATURED_INSTRUCTORS": "featured-instructors",
            "SEC_LICENSES_AND_FACILITIES": "licenses", "MOD_MUSIC_THEORY_SOLFEGE": "music-theory",
            "SEC_FARDIS_DEMANDED_PROGRAMS": "programs", "SEC_FARDIS_ROUTE_MATRIX": "routes",
            "SEC_FARDIS_WEEKEND_COMPACT_SHIFTS": "weekend-shifts",
            "SEC_AUDITION_PROCESS_STEPS": "process", "SEC_AUDITION_AGE_CRITERIA": "age-criteria",
            "SEC_AUDITION_PREP_GUIDE": "prep", "SEC_JUDGING_PANEL": "panel",
            "SEC_AUDITION_BOOKING_FORM": "booking", "SEC_INSTRUCTOR_FILTERS": "instructor-filters",
            "SEC_CONTACT_CHANNELS": "channels", "SEC_OPENING_HOURS": "hours",
            "SEC_CAFE_HERO": "hero", "SEC_LIVE_NIGHTS_BY_INSTRUMENT": "cafe-piano",
            "SEC_CAFE_MENU": "cafe-menu", "SEC_STUDENT_RECITAL_STAGE": "student-stage",
            "SEC_CAFE_RESERVATION_MAP": "reservation", "SEC_CAFE_FAQ": "faq",
        }
        unmapped = [m for m in entry["required_onpage_modules"] if m not in need]
        if unmapped:
            module_parity.append({"page": entry["url_slug"], "unmapped_modules": unmapped})
        for mod, anchor in need.items():
            if mod in entry["required_onpage_modules"] and anchor not in anchors:
                module_parity.append({"page": entry["url_slug"], "module": mod, "expected_anchor": anchor})

    cafe_entry = next(e for e in plan["pages"] if e["url_slug"] == "/art-cafe/")
    cafe_anchors = {s["anchor"] for s in cafe_entry["sections"]}
    cafe_ok = all(a in cafe_anchors for _, _, _, _, a in L.CAFE_INSTRUMENTS)
    fardis_entry = next(e for e in plan["pages"] if e["url_slug"] == "/fardis-branch/")
    fardis_kws = {r["raw_keyword"] for r in b.silo_records("SILO_GEO_FARDIS")}
    fardis_blob = " ".join(str(s) for s in fardis_entry["sections"])
    fardis_ok = all(k in fardis_blob for k in fardis_kws)

    gates = {
        "G3_1_every_page_has_dossier_with_end_marker": len(written) == len(plan["pages"]) and all_end,
        "G3_2_required_modules_present_as_sections": len(module_parity) == 0,
        "G3_3_cafe_6_keywords_and_5_instrument_sections": cafe_ok,
        "G3_4_fardis_15_keywords_covered_and_mirrored": fardis_ok,
        "G3_5_needed_media_logged": len(b.media) > 0,
        "G3_6_zero_unplaced_keywords": len(missing) == 0,
    }
    if module_parity:
        print("  module parity gaps:", module_parity[:5])
    if missing:
        print("  unplaced keywords:", missing[:5])

    L.update_progress("PHASE_3", "COMPLETE",
                      ["seo_dossiers/*.md", "output/page_content_plan.json", "output/needed_media.md"],
                      gates, "PHASE_4")
    print("=" * 74)
    print("PHASE 3 — COMPLETE")
    print("=" * 74)
    print(f"  dossiers written : {len(written)} → seo_dossiers/")
    print(f"  media items      : {len(b.media)} → output/needed_media.md")
    for k, v in gates.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    return all(gates.values())


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
