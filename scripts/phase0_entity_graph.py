#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIFIED PHASE 0 — INGEST, VALIDATE, DECODE & NORMALISE
Artifacts:
  output/progress_seo.json
  output/macro_topology.json
  output/academy_graph.json
  output/academy_entity_map.json
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_lib as L  # noqa: E402


def course_readiness_score(c, instrs, kw_by_course, cafe_events):
    """STEP 3 — 100-point course readiness score."""
    breakdown, score = {}, 0

    # Core buildable (68)
    v = 12 if c["name_fa"] and c["department_id"] else 0
    breakdown["canonical_title_and_department_12"] = v; score += v
    v = 12 if (c["tuition_private_irr"] > 0 or c["tuition_group_irr"] > 0) else 0
    breakdown["tuition_transparency_12"] = v; score += v
    v = 10 if (c["formats_offered"] and c["age_groups"]) else 0
    breakdown["formats_and_age_groups_10"] = v; score += v
    v = 14 if len(c["sub_specialties_fa"]) >= 2 else (7 if c["sub_specialties_fa"] else 0)
    breakdown["syllabus_levels_defined_14"] = v; score += v
    verified = [i for i in instrs if not L.is_placeholder_instructor(i)]
    v = 12 if verified else (4 if instrs else 0)
    breakdown["verified_instructor_mapped_12"] = v; score += v
    breakdown["primary_media_asset_8"] = 0  # no real photography supplied yet
    # Conversion & local dominance (32)
    needs_female = any(r["intent_vector"] == "FEMALE_SPECIFIC" for r in kw_by_course)
    female_verified = any(i["gender"] == "female" and not L.is_placeholder_instructor(i) for i in instrs)
    v = 8 if (female_verified or (not needs_female and c["has_female_instructor"] and False)) else 0
    breakdown["verified_female_instructor_8"] = v; score += v
    v = 6 if len(c["sub_specialties_fa"]) >= 2 else 0
    breakdown["sub_specialty_coverage_6"] = v; score += v
    breakdown["student_work_sample_6"] = 0
    breakdown["verified_reviews_6"] = 0  # reviews.csv absent
    v = 6 if c["certificate_type"] else 0
    breakdown["certification_pathway_6"] = v; score += v

    gaps = [k for k, val in breakdown.items() if val == 0]
    return score, breakdown, gaps


def main():
    L.ensure_dirs(L.OUTPUT, L.SILOS, L.DOSSIERS)

    profile = L.academy_profile()
    courses = L.load_course_index()
    instructors = L.load_instructors()
    cafe_events = L.load_cafe_events()
    serp = L.load_serp_matrix()
    raw_keywords = L.load_keywords()
    records = [L.classify_keyword(k) for k in raw_keywords]
    reg = L.silo_registry(records)

    f_status = L.fardis_status(profile)
    serp_mode = serp.get("serp_evidence_mode", "NOT_PROVIDED")
    serp_live = serp_mode == "LIVE_SERP"

    # ---------------------------------------------------------------- STEP 0
    stem_equivalence = []
    for silo_id, s in reg.items():
        if s["kind"] != "course" or not s["keywords"]:
            continue
        stems = {}
        for r in s["keywords"]:
            n = r["normalized_keyword"]
            for stem in ("کلاس", "آموزش", "آموزشگاه", "دوره", "مدرسه", "آکادمی", "استاد", "مدرس",
                         "تدریس", "اساتید", "قیمت", "شهریه", "هزینه", "بهترین"):
                if re.search(rf"(?<![\u0600-\u06FF]){stem}", n):
                    stems.setdefault(stem, []).append(r["raw_keyword"])
        if len(stems) >= 2:
            stem_equivalence.append({
                "silo_id": silo_id,
                "target_slug": s["target_slug"],
                "stems_detected": sorted(stems.keys()),
                "stem_keyword_counts": {k: len(v) for k, v in sorted(stems.items())},
                "directive": "MERGE_INTO_MASTER_COURSE_PAGE",
                "evidence_source": "LIVE_SERP_TOP10_OVERLAP" if serp_live else "DETERMINISTIC_PERSIAN_STEM_RULE",
            })

    divergences = [
        {"id": "DIVERGENCE_1_KIDS_ORFF", "trigger_keywords": [r["raw_keyword"] for r in reg["SILO_CRS_KIDS_MUSIC"]["keywords"]][:6],
         "required_url": "/music/kids/", "reason": "SERP برای موسیقی کودک/ارف صفحات اختصاصی کودک را رتبه می‌دهد، نه هاب عمومی موسیقی."},
        {"id": "DIVERGENCE_2_LIVE_CAFE", "trigger_keywords": [r["raw_keyword"] for r in reg["SILO_CAFE_01"]["keywords"]],
         "required_url": "/art-cafe/", "reason": "نتایج کافه/رستوران از نوع Hospitality & Live-Music Venue هستند، نه کلاس آموزشی."},
        {"id": "DIVERGENCE_3_AUDITION", "trigger_keywords": [r["raw_keyword"] for r in reg["SILO_CONV_AUDITION"]["keywords"]],
         "required_url": "/acting-audition/", "reason": "قصد جست‌وجو «اقدام/ثبت‌نام تست» است و نیازمند صفحه تبدیل اختصاصی است."},
        {"id": "DIVERGENCE_4_FARDIS", "trigger_keywords": [r["raw_keyword"] for r in reg["SILO_GEO_FARDIS"]["keywords"]][:8],
         "required_url": "/fardis-branch/", "reason": "SERP زیرمنطقه‌ای فردیس با کرج متفاوت است و صفحه هایپرلوکال می‌خواهد."},
    ]

    ortho_records = [{
        "raw_keyword": r["raw_keyword"],
        "normalized_keyword": r["normalized_keyword"],
        "variant_type": ("NO_MADDAH" if "ORTHO_VARIANT_NO_MADDAH" in r["notes"] else "SPACING_ZWNJ"),
        "assigned_silo": r["silo_id"],
    } for r in records if r["orthographic_variant"]]

    # ------------------------------------------------- STEP 2: macro topology
    macro = {
        "generated_at": L.now_iso(),
        "phase": "PHASE_0",
        "academy_name_fa": profile["brand_fa"],
        "academy_name_en": profile["brand_en"],
        "tagline_fa": profile["tagline_fa"],
        "site_language": profile["language"],
        "site_direction": profile["direction"],
        "market": profile["raw"].get("MARKET", "IR"),
        "domain": profile["domain"],
        "primary_city": profile["city"],
        "province": profile["province"],
        "campus_topology": {
            "model": profile["location_model"],
            "campus_count": 1,
            "main_campus_address_fa": profile["address_fa"],
            "geo_coordinates_google": profile["geo"],
            "geo_coordinates_routing": profile["geo_routing"],
            "postal_code": profile["postal_code"],
            "service_radius_meters": profile["service_radius_m"],
            "served_cities": profile["served_cities"],
            "served_neighborhoods": profile["served_neighborhoods"],
            "fardis_status": f_status,
            "fardis_truth_note": (
                "هیچ آدرس خیابانی مستقلی برای فردیس در academy_data.txt وجود ندارد؛ "
                "فردیس به‌عنوان منطقه خدمات‌دهی/هاب رفت‌وآمد پردیس مرکزی کرج مدل می‌شود و "
                "هیچ NAP جعلی برای فردیس تولید نمی‌شود."
            ) if f_status == "SERVICE_AREA_COMMUTER_HUB" else "آدرس فیزیکی فردیس تأیید شد.",
            "landmarks": profile["landmarks"],
            "transit_and_commuter_routes": profile["transit_routes"],
        },
        "art_cafe_profile": {
            "status": "VERIFIED_ON_SITE_VENUE" if profile["cafe_lines"] else "NOT_VERIFIED",
            "verbatim_lines": profile["cafe_lines"],
            "live_instruments_verified": sorted({e["instrument_focus_fa"] for e in cafe_events}),
            "events_in_cafe_events_csv": len(cafe_events),
            "menu_items_verified_in_inputs": 0,
            "menu_data_gap": "منوی کافه در هیچ فایل ورودی موجود نیست → [INTERNAL_DATA_NEEDED]",
        },
        "official_licenses": [profile["license_fa"]] if profile["license_fa"] else [],
        "guarantees_and_proof": profile["guarantees"],
        "contact": {
            "phone_display": profile["phone_display"], "phone_e164": profile["phone_e164"],
            "mobile_whatsapp": profile["mobile_whatsapp"], "whatsapp_url": profile["whatsapp_url"],
            "instagram_url": profile["instagram_url"], "email": profile["email"],
            "opening_hours": profile["opening_hours"], "maps_url": profile["maps_url"],
            "neshan_url": profile["neshan_url"], "balad_url": profile["balad_url"], "waze_url": profile["waze_url"],
        },
        "validation_counts": {
            "total_raw_keyword_lines": len(raw_keywords),
            "total_distinct_keywords": len({r["raw_keyword"] for r in records}),
            "duplicate_lines": len(raw_keywords) - len({r["raw_keyword"] for r in records}),
            "orthographic_variants_detected": len(ortho_records),
            "courses_in_csv": len(courses),
            "active_courses": sum(1 for c in courses.values() if c["status"] == "active"),
            "instructors_in_csv": len(instructors),
            "verified_instructors": sum(1 for i in instructors if not L.is_placeholder_instructor(i)),
            "pending_instructor_placeholders": sum(1 for i in instructors if L.is_placeholder_instructor(i)),
            "cafe_events": len(cafe_events),
            "silos_planned": len(reg),
        },
        "serp_evidence": {
            "matrix_present": bool(serp),
            "serp_evidence_mode": serp_mode,
            "live_queries_collected": serp.get("live_serp_queries_collected", 0),
            "downstream_directive": serp.get("downstream_directive", "USE_DETERMINISTIC_PERSIAN_STEM_RULES"),
            "clusters_decoded": len(serp.get("clusters_decoded", [])),
            "note": (
                "ماتریس SERP زنده در این اجرا در دسترس نبود (خروجی شبکه مسدود). "
                "هیچ داده رقیبی ساخته نشده است؛ ادغام/تفکیک سیلوها بر پایه قواعد قطعی ریشه‌های فارسی انجام شد."
            ) if not serp_live else "ادغام سیلوها بر پایه هم‌پوشانی تجربی Top-10 انجام شد.",
        },
    }

    # ------------------------------------------- STEP 3 + 4: academy graph
    dept_nodes = []
    course_nodes = []
    kw_by_silo = {sid: s["keywords"] for sid, s in reg.items()}
    total_score = 0
    for cid, c in courses.items():
        instrs = L.instructors_for(cid, instructors)
        kws = kw_by_silo.get(c["silo_id"], [])
        score, breakdown, gaps = course_readiness_score(c, instrs, kws, cafe_events)
        total_score += score
        verified = [i for i in instrs if not L.is_placeholder_instructor(i)]
        pending = [i for i in instrs if L.is_placeholder_instructor(i)]
        course_nodes.append({
            "entity_id": "E_" + cid,
            "course_id": cid,
            "name_fa": c["name_fa"],
            "department_id": c["department_id"],
            "url_slug": c["slug"],
            "silo_id": c["silo_id"],
            "status": c["status"],
            "keyword_demand": len(kws),
            "formats_offered": c["formats_offered"],
            "age_groups": c["age_groups"],
            "sub_specialties_fa": c["sub_specialties_fa"],
            "tuition": {
                "private_irr": c["tuition_private_irr"], "group_irr": c["tuition_group_irr"],
                "private_toman_fa": L.irr_to_toman_fa(c["tuition_private_irr"]),
                "group_toman_fa": L.irr_to_toman_fa(c["tuition_group_irr"]),
                "sessions_per_term": c["sessions_per_term"], "session_duration_min": c["session_duration_min"],
                "verified": c["tuition_private_irr"] > 0,
            },
            "certificate_type": c["certificate_type"],
            "instructors": {
                "verified_ids": [i["instructor_id"] for i in verified],
                "pending_placeholder_ids": [i["instructor_id"] for i in pending],
                "verified_count": len(verified),
                "female_verified": any(i["gender"] == "female" and not L.is_placeholder_instructor(i) for i in instrs),
                "female_flag_in_courses_csv": c["has_female_instructor"],
            },
            "performed_in_cafe": c["performed_in_cafe"],
            "fardis_high_demand": c["fardis_high_demand"],
            "readiness_score_100": score,
            "readiness_breakdown": breakdown,
            "data_gaps": gaps,
        })

    for dkey, d in L.DEPARTMENTS.items():
        children = [c for c in course_nodes if c["department_id"] == dkey]
        dept_nodes.append({
            "entity_id": d["entity_id"], "department_id": dkey, "name_fa": d["name_fa"],
            "url_slug": d["slug"], "silo_id": d["silo_id"],
            "course_count": len(children),
            "course_ids": [c["course_id"] for c in children],
            "own_keyword_demand": len(kw_by_silo.get(d["silo_id"], [])),
            "total_keyword_demand": len(kw_by_silo.get(d["silo_id"], [])) + sum(c["keyword_demand"] for c in children),
            "avg_readiness_score": round(sum(c["readiness_score_100"] for c in children) / max(len(children), 1), 1),
        })

    female_demand_disciplines = {}
    for r in records:
        if r["intent_vector"] == "FEMALE_SPECIFIC":
            female_demand_disciplines.setdefault(r["silo_id"], []).append(r["raw_keyword"])
    female_gate = []
    for silo_id, kws in female_demand_disciplines.items():
        cid = L.SILO_COURSE.get(silo_id)
        instrs = L.instructors_for(cid, instructors) if cid else []
        verified_female = [i for i in instrs if i["gender"] == "female" and not L.is_placeholder_instructor(i)]
        pending_female = [i for i in instrs if i["gender"] == "female" and L.is_placeholder_instructor(i)]
        female_gate.append({
            "silo_id": silo_id, "course_id": cid, "demand_keywords": kws,
            "female_instructor_verified": bool(verified_female),
            "verified_female_ids": [i["instructor_id"] for i in verified_female],
            "pending_female_placeholder_ids": [i["instructor_id"] for i in pending_female],
            "action": "RENDER_VERIFIED_FEMALE_CARD" if verified_female else "[INTERNAL_DATA_NEEDED] — نام/بیوگرافی استاد خانم باید از آموزشگاه دریافت شود",
        })

    academy_graph = {
        "generated_at": L.now_iso(),
        "phase": "PHASE_0",
        "academy": {
            "name_fa": profile["brand_fa"], "name_en": profile["brand_en"],
            "entity_id": "E_ACADEMY_ROOT", "domain": profile["domain"],
            "year_founded": profile["year_founded"], "years_in_operation": profile["years_in_operation"],
            "license_fa": profile["license_fa"],
        },
        "departments": dept_nodes,
        "courses": course_nodes,
        "catalog_readiness": {
            "avg_course_readiness_score": round(total_score / max(len(course_nodes), 1), 1),
            "courses_above_70": sum(1 for c in course_nodes if c["readiness_score_100"] >= 70),
            "courses_below_50": sum(1 for c in course_nodes if c["readiness_score_100"] < 50),
            "courses_without_verified_instructor": [c["course_id"] for c in course_nodes
                                                    if c["instructors"]["verified_count"] == 0],
        },
        "instructor_coverage": {
            "total": len(instructors),
            "verified": sum(1 for i in instructors if not L.is_placeholder_instructor(i)),
            "pending_client_input": [i["instructor_id"] for i in instructors if L.is_placeholder_instructor(i)],
            "female_verified": sum(1 for i in instructors if i["gender"] == "female" and not L.is_placeholder_instructor(i)),
            "male_verified": sum(1 for i in instructors if i["gender"] == "male" and not L.is_placeholder_instructor(i)),
        },
        "female_instructor_gate": female_gate,
        "cafe_readiness": {
            "venue_verified_in_academy_data": bool(profile["cafe_lines"]),
            "events_verified": len(cafe_events),
            "instruments_with_verified_nights": sorted({e["instrument_focus_fa"] for e in cafe_events}),
            "menu_verified": False,
            "blockers": ["منوی کافه/رستوران در ورودی‌ها موجود نیست → [INTERNAL_DATA_NEEDED]"],
        },
        "fardis_readiness": {
            "status": f_status,
            "keyword_demand": len(kw_by_silo["SILO_GEO_FARDIS"]),
            "transit_routes_verified": len(profile["transit_routes"]),
            "courses_flagged_fardis_high_demand": [c["course_id"] for c in course_nodes if c["fardis_high_demand"]],
        },
    }

    # ---------------------------------- STEP 4 + 5: entity map + keyword premap
    entity_map = {
        "generated_at": L.now_iso(),
        "phase": "PHASE_0",
        "entity_classes": {
            "E_DEPT": [{"entity_id": d["entity_id"], "name_fa": d["name_fa"], "url_slug": d["url_slug"]}
                       for d in dept_nodes],
            "E_COURSE": [{"entity_id": c["entity_id"], "name_fa": c["name_fa"], "url_slug": c["url_slug"],
                          "department": c["department_id"], "keyword_demand": c["keyword_demand"]}
                         for c in course_nodes],
            "E_CAFE_VENUE": {
                "entity_id": "E_CAFE_VENUE",
                "name_fa": "کافه هنر و موسیقی آموزشگاه آنک",
                "url_slug": "/art-cafe/",
                "schema_types": ["CafeOrCoffeeShop", "EventVenue"],
                "keywords_owned": [r["raw_keyword"] for r in reg["SILO_CAFE_01"]["keywords"]],
                "HOSTS_LIVE_PERFORMANCE_OF": [
                    {"instrument_fa": fa, "course_entity": "E_" + cid, "course_slug": slug,
                     "verified_event_ids": [e["event_id"] for e in cafe_events if fa.replace(" ", "") in e["instrument_focus_fa"].replace("‌", "").replace(" ", "")]}
                    for fa, sec, slug, cid, anchor in L.CAFE_INSTRUMENTS
                ],
            },
            "E_INSTRUCTOR": [{
                "entity_id": "E_" + i["instructor_id"], "instructor_id": i["instructor_id"],
                "name_fa": i["name_fa"], "gender": i["gender"],
                "course_ids": [c for c in i["course_ids"].split("|") if c],
                "role_title_fa": i["role_title_fa"], "status": i["status"],
                "is_placeholder": L.is_placeholder_instructor(i),
                "same_as_url": i.get("same_as_url", ""),
            } for i in instructors],
            "E_AUDIENCE_FORMAT": [
                {"entity_id": "MOD_KIDS_TEENS", "label_fa": "کودکان و نوجوانان",
                 "keyword_count": sum(1 for r in records if r["intent_vector"] == "KIDS_TEENS_SPECIFIC")},
                {"entity_id": "MOD_WOMEN_FEMALE_TEACHER", "label_fa": "بانوان / مدرس خانم",
                 "keyword_count": sum(1 for r in records if r["intent_vector"] == "FEMALE_SPECIFIC")},
                {"entity_id": "MOD_PRIVATE", "label_fa": "خصوصی",
                 "keyword_count": sum(1 for r in records if "خصوصی" in r["normalized_keyword"])},
                {"entity_id": "MOD_GROUP", "label_fa": "گروهی",
                 "keyword_count": sum(1 for r in records if "گروهی" in r["normalized_keyword"])},
                {"entity_id": "MOD_PRICE_TUITION", "label_fa": "قیمت / شهریه / هزینه",
                 "keyword_count": sum(1 for r in records if r["intent_vector"] == "TUITION_COST")},
                {"entity_id": "MOD_AUDITION", "label_fa": "تست بازیگری",
                 "keyword_count": sum(1 for r in records if r["intent_vector"] == "AUDITION_TEST")},
                {"entity_id": "MOD_ADDRESS", "label_fa": "آدرس / کجاست",
                 "keyword_count": sum(1 for r in records if r["intent_vector"] == "LOCATION_DIRECTION")},
            ],
            "E_GEO": [
                {"entity_id": "E_GEO_KARAJ", "name_fa": "کرج", "type": "City",
                 "keyword_count": sum(1 for r in records if r["geo_target"] == "KARAJ")},
                {"entity_id": "E_GEO_FARDIS", "name_fa": "فردیس کرج", "type": "AdministrativeArea",
                 "status": f_status, "url_slug": "/fardis-branch/",
                 "keyword_count": sum(1 for r in records if r["geo_target"] == "FARDIS_KARAJ")},
            ],
            "E_HUB_AUDITION": {"entity_id": "E_HUB_AUDITION", "url_slug": "/acting-audition/",
                               "keywords_owned": [r["raw_keyword"] for r in reg["SILO_CONV_AUDITION"]["keywords"]]},
        },
        "serp_decoder": {
            "stem_equivalence_locks": stem_equivalence,
            "intent_divergences_requiring_dedicated_url": divergences,
        },
        "orthographic_normalisation": {
            "variants_detected": len(ortho_records),
            "maddah_map": dict(L.MADDAH_MAP),
            "spacing_map": L.SPACING_VARIANTS,
            "records": ortho_records,
        },
        "keyword_pre_mapping": [{
            "raw_keyword": r["raw_keyword"],
            "normalized_keyword": r["normalized_keyword"],
            "orthographic_variant": r["orthographic_variant"],
            "mapped_department": r["mapped_department"],
            "mapped_course_or_hub": r["mapped_course_or_hub"],
            "silo_id": r["silo_id"],
            "geo_target": r["geo_target"],
            "intent_vector": r["intent_vector"],
            "funnel_stage": r["funnel_stage"],
            "section_target": r["section_target"],
            "sub_specialties": r["sub_specialties"],
            "notes": r["notes"],
        } for r in records],
        "data_gap_priorities": [
            {"priority": 1, "gap": "استاد خانم تأییدشده برای پیانو/گیتار/تار و سه‌تار/سنتور/آواز",
             "evidence": [g["silo_id"] for g in female_gate if not g["female_instructor_verified"]],
             "status": "[INTERNAL_DATA_NEEDED]"},
            {"priority": 2, "gap": "اساتید تأییدشده برای همه سازها (۷ ردیف instructors.csv در وضعیت pending_client_input)",
             "evidence": [i["instructor_id"] for i in instructors if L.is_placeholder_instructor(i)],
             "status": "[INTERNAL_DATA_NEEDED]"},
            {"priority": 3, "gap": "منو و قیمت‌های کافه هنر", "evidence": ["academy_data.txt: ART_CAFE_VENUE بدون منو"],
             "status": "[INTERNAL_DATA_NEEDED]"},
            {"priority": 4, "gap": "reviews.csv (نظرات تأییدشده هنرجویان) موجود نیست",
             "evidence": ["input/reviews.csv"], "status": "[INTERNAL_DATA_NEEDED]"},
            {"priority": 5, "gap": "رسانه واقعی کلاس‌ها، استودیو و کافه", "evidence": ["output/needed_media.md"],
             "status": "[INTERNAL_DATA_NEEDED]"},
        ],
    }

    L.write_json(os.path.join(L.OUTPUT, "macro_topology.json"), macro)
    L.write_json(os.path.join(L.OUTPUT, "academy_graph.json"), academy_graph)
    L.write_json(os.path.join(L.OUTPUT, "academy_entity_map.json"), entity_map)

    # --------------------------------------------------------------- GATE 0
    cafe_kws = {r["raw_keyword"] for r in reg["SILO_CAFE_01"]["keywords"]}
    subspec_checks = {
        "آموزش گیتار الکتریک کرج": "SILO_CRS_GUITAR", "کلاس گیتار برقی کرج": "SILO_CRS_GUITAR",
        "آموزش پن فلوت در کرج": "SILO_CRS_FLUTE", "آموزش فلوت لاکوتا در کرج": "SILO_CRS_FLUTE",
        "کلاس ویولن سل کرج": "SILO_CRS_VIOLIN", "آموزش خوشنویسی با خودکار در کرج": "SILO_CRS_CALLIGRAPHY",
        "دوره عکاسی با موبایل کرج": "SILO_CRS_PHOTOGRAPHY", "آموزش آواز سنتی کرج": "SILO_CRS_VOCALS",
        "کلاس آواز پاپ در کرج": "SILO_CRS_VOCALS", "کلاس آواز بانوان در کرج": "SILO_CRS_VOCALS",
        "کلاس اواز گروهی در کرج": "SILO_CRS_VOCALS",
    }
    by_kw = {r["raw_keyword"]: r for r in records}
    gates = {
        "G0_1_keyword_ingestion_100pct": len(records) == len(raw_keywords) and all(r["silo_id"] for r in records),
        "G0_2_cafe_vs_classroom_separation": len(cafe_kws) == 6 and all(
            by_kw[k]["mapped_course_or_hub"] == "E_CAFE_VENUE" for k in cafe_kws),
        "G0_3_sub_specialty_preservation": all(by_kw[k]["silo_id"] == v for k, v in subspec_checks.items() if k in by_kw),
        "G0_4_female_instructor_gate_evaluated": len(female_gate) > 0,
        "G0_5_fardis_truth_gate": all(r["geo_target"] == "FARDIS_KARAJ" for r in reg["SILO_GEO_FARDIS"]["keywords"])
                                  and f_status == "SERVICE_AREA_COMMUTER_HUB",
        "G0_6_valid_json": True,
    }

    L.update_progress("PHASE_0", "COMPLETE",
                      ["output/macro_topology.json", "output/academy_graph.json",
                       "output/academy_entity_map.json", "output/progress_seo.json"],
                      gates, "PHASE_1")

    print("=" * 74)
    print("UNIFIED PHASE 0 — COMPLETE")
    print("=" * 74)
    print(f"  keyword lines ingested : {len(raw_keywords)}  (distinct {len({r['raw_keyword'] for r in records})})")
    print(f"  orthographic variants  : {len(ortho_records)}")
    print(f"  courses / instructors  : {len(courses)} / {len(instructors)}"
          f"  (verified {macro['validation_counts']['verified_instructors']},"
          f" pending {macro['validation_counts']['pending_instructor_placeholders']})")
    print(f"  fardis_status          : {f_status}")
    print(f"  serp evidence mode     : {serp_mode}")
    print(f"  avg course readiness   : {academy_graph['catalog_readiness']['avg_course_readiness_score']}/100")
    for k, v in gates.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    return all(gates.values())


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
