#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIFIED PHASE 1 — HYBRID KEYWORD SILOS, SERP CO-RANKING LOCK & TAXONOMY RECONCILIATION
Artifacts:
  output/silos/silo_[ID]_keywords.tsv   (8-column TSV, 100% keyword partition)
  output/academy_keyword_map.json
  output/macro_topology.json            (updated)
"""
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_lib as L  # noqa: E402

TSV_HEADER = ["keyword", "normalized_stem", "intent_vector", "funnel_stage",
              "geo_modifier", "mapped_entity_id", "section_target", "notes"]

DISCIPLINE_STEMS = ["کلاس", "آموزش", "آموزشگاه", "دوره", "استاد", "مدرس", "اساتید",
                    "تدریس", "مدرسه", "آکادمی", "قیمت", "شهریه", "هزینه", "بهترین", "معلم"]


def write_silo_tsv(silo_id: str, records: list) -> str:
    path = os.path.join(L.SILOS, f"silo_{silo_id}_keywords.tsv")
    lines = ["\t".join(TSV_HEADER)]
    seen = set()
    for r in sorted(records, key=lambda x: (x["section_target"], x["raw_keyword"])):
        if r["raw_keyword"] in seen:
            continue
        seen.add(r["raw_keyword"])
        lines.append("\t".join([
            r["raw_keyword"], r["normalized_keyword"], r["intent_vector"], r["funnel_stage"],
            r["geo_target"], r["mapped_course_or_hub"], r["section_target"], r["notes"],
        ]))
    L.write_text(path, "\n".join(lines) + "\n")
    return path


def main():
    L.ensure_dirs(L.OUTPUT, L.SILOS)
    profile = L.academy_profile()
    courses = L.load_course_index()
    instructors = L.load_instructors()
    cafe_events = L.load_cafe_events()
    raw_keywords = L.load_keywords()
    records = [L.classify_keyword(k) for k in raw_keywords]
    reg = L.silo_registry(records)
    f_status = L.fardis_status(profile)

    # ------------------------------------------------ PART A · STEP 1-7 TSVs
    written, distinct_total = [], set()
    for silo_id, s in reg.items():
        written.append(write_silo_tsv(silo_id, s["keywords"]))
        distinct_total |= {r["raw_keyword"] for r in s["keywords"]}

    # ------------------------------------- PART B · STEP 8-10 reconciliation
    course_mappings = []
    for cid, c in courses.items():
        s = reg[c["silo_id"]]
        kws = s["keywords"]
        instrs = L.instructors_for(cid, instructors)
        verified = [i for i in instrs if not L.is_placeholder_instructor(i)]
        female_verified = [i for i in instrs if i["gender"] == "female" and not L.is_placeholder_instructor(i)]
        intent = Counter(r["intent_vector"] for r in kws)
        sections = Counter(r["section_target"] for r in kws)
        subs = sorted({s_ for r in kws for s_ in r["sub_specialties"]})
        has_female_kw = intent.get("FEMALE_SPECIFIC", 0) > 0

        if len(kws) >= 10:
            directive = "BUILD_COURSE_MEGA"
        elif len(kws) >= 1:
            directive = "BUILD_COURSE_STANDARD"
        else:
            directive = "BUILD_COURSE_STANDARD_NO_DIRECT_DEMAND"
        if c["status"] != "active":
            directive = "CANNOT_SERVE_MISSING_COURSE"

        course_mappings.append({
            "silo_id": c["silo_id"],
            "target_slug": c["slug"],
            "department_id": c["department_id"],
            "course_id": cid,
            "course_name_fa": c["name_fa"],
            "keyword_count": len({r["raw_keyword"] for r in kws}),
            "intent_breakdown": {
                "course_enrollment": intent.get("COURSE_ENROLLMENT", 0),
                "instructor_seeking": intent.get("INSTRUCTOR_SEEKING", 0),
                "female_specific": intent.get("FEMALE_SPECIFIC", 0),
                "kids_teens_specific": intent.get("KIDS_TEENS_SPECIFIC", 0),
                "tuition_cost": intent.get("TUITION_COST", 0),
                "location_direction": intent.get("LOCATION_DIRECTION", 0),
                "superlative_comparison": intent.get("SUPERLATIVE_COMPARISON", 0),
            },
            "section_target_breakdown": dict(sections),
            "catalog_verification": {
                "course_exists_in_csv": True,
                "instructor_count": len(instrs),
                "verified_instructor_count": len(verified),
                "pending_instructor_placeholders": [i["instructor_id"] for i in instrs if L.is_placeholder_instructor(i)],
                "female_instructor_verified": bool(female_verified),
                "female_instructor_demanded_by_keywords": has_female_kw,
                "female_data_gap": has_female_kw and not female_verified,
                "private_format_verified": "private" in c["formats_offered"],
                "group_format_verified": "group" in c["formats_offered"],
                "kids_track_verified": "kids" in c["age_groups"],
                "tuition_data_verified": c["tuition_private_irr"] > 0,
            },
            "sub_specialties_merged": subs,
            "sub_specialty_split_decision": {
                "decision": "KEEP_AS_IN_PAGE_MODULE",
                "reason": "courses.csv هیچ course_id مستقلی برای این زیرتخصص‌ها تعریف نکرده و سرفصل مجزا با ≥۴ ماژول ندارد.",
            } if subs else {"decision": "NOT_APPLICABLE", "reason": "زیرتخصص اختصاصی در کلیدواژه‌ها یافت نشد."},
            "stem_lock": {
                "stems_merged": sorted({st for r in kws for st in DISCIPLINE_STEMS
                                        if re.search(rf"(?<![\u0600-\u06FF]){st}", r["normalized_keyword"])}),
                "directive": "MERGE_INTO_MASTER_COURSE_PAGE",
            },
            "build_directive": directive,
        })

    dept_alignment = []
    for dkey, d in L.DEPARTMENTS.items():
        s = reg[d["silo_id"]]
        child = [m for m in course_mappings if m["department_id"] == dkey]
        dept_alignment.append({
            "silo_id": d["silo_id"], "department_id": dkey, "target_slug": d["slug"],
            "name_fa": d["name_fa"],
            "own_keyword_count": len({r["raw_keyword"] for r in s["keywords"]}),
            "child_course_silos": [m["silo_id"] for m in child],
            "child_keyword_count": sum(m["keyword_count"] for m in child),
            "build_directive": "BUILD_DEPARTMENT_HUB" if s["keywords"] else "BUILD_DEPARTMENT_HUB_NAVIGATIONAL",
            "primary_keyword_source": "DATASET" if s["keywords"] else "DERIVED_BRAND_TAXONOMY",
        })

    cafe_records = reg["SILO_CAFE_01"]["keywords"]
    cafe_mapping = {
        "silo_id": "SILO_CAFE_01", "target_slug": "/art-cafe/",
        "keyword_count": len(cafe_records),
        "keywords": [r["raw_keyword"] for r in cafe_records],
        "instruments_featured_in_cafe_keywords": [fa for fa, _, _, _, _ in L.CAFE_INSTRUMENTS],
        "cafe_data_verified": bool(profile["cafe_lines"]),
        "cafe_events_verified": len(cafe_events),
        "cafe_menu_verified": False,
        "cafe_menu_status": "[INTERNAL_DATA_NEEDED] — منوی کافه در ورودی‌ها نیست؛ بخش منو با اسلات خالی ساخته می‌شود.",
        "linked_course_slugs": [slug for _, _, slug, _, _ in L.CAFE_INSTRUMENTS],
        "bidirectional_bridge": [
            {"cafe_section": sec, "instrument_fa": fa, "course_slug": slug,
             "course_silo": L.COURSE_SILO[cid],
             "reciprocal_module_on_course_page": "SEC_CAFE_PERFORMANCE_BRIDGE",
             "verified_event_ids": [e["event_id"] for e in cafe_events
                                    if fa.replace(" ", "") in e["instrument_focus_fa"].replace("‌", "").replace(" ", "")]}
            for fa, sec, slug, cid, _ in L.CAFE_INSTRUMENTS
        ],
    }

    fardis_records = reg["SILO_GEO_FARDIS"]["keywords"]
    fardis_routes = []
    for r in fardis_records:
        target = r["dual_intent"]
        slug = next((x[2] for x in L.FARDIS_ROUTING if x[1] == target), "/music/")
        fardis_routes.append({"keyword": r["raw_keyword"], "dual_intent_silo": target, "course_slug": slug})
    demanded = sorted({x["course_slug"] for x in fardis_routes})
    fardis_mapping = {
        "silo_id": "SILO_GEO_FARDIS", "target_slug": "/fardis-branch/",
        "keyword_count": len(fardis_records),
        "fardis_campus_status": f_status,
        "nap_safety_rule": "NEVER_EMIT_FARDIS_STREET_ADDRESS" if f_status == "SERVICE_AREA_COMMUTER_HUB" else "EMIT_VERIFIED_BRANCH_NAP",
        "demanded_courses_in_fardis": demanded,
        "dual_intent_routes": fardis_routes,
        "reciprocal_module_on_course_pages": "SEC_FARDIS_COMMUTER_ACCESS",
        "verified_transit_routes": profile["transit_routes"],
    }

    audition_records = reg["SILO_CONV_AUDITION"]["keywords"]
    audition_mapping = {
        "silo_id": "SILO_CONV_AUDITION", "target_slug": "/acting-audition/",
        "keyword_count": len(audition_records),
        "keywords": [r["raw_keyword"] for r in audition_records],
        "feeds_into": ["/performing-arts/acting/", "/performing-arts/kids-acting-drama/"],
        "judging_faculty_source": "instructors.csv → CRS_ACTING | CRS_KIDS_ACTING",
    }

    # STEP 11 — orphan demand / unserved courses
    orphan = []
    for cid, c in courses.items():
        if not reg[c["silo_id"]]["keywords"]:
            orphan.append({"type": "COURSE_WITHOUT_DIRECT_SEARCH_DEMAND", "course_id": cid,
                           "slug": c["slug"], "action": "BUILD_AS_CATALOG_PAGE_LINKED_FROM_HUB"})
    for silo_id, s in reg.items():
        if s["kind"] == "course" and s["course_id"] not in courses:
            orphan.append({"type": "DEMAND_WITHOUT_COURSE", "silo_id": silo_id})
    unserved_demand = [r["raw_keyword"] for r in records if r["silo_id"] == "SILO_00"]

    # ---------------------------------------------------------- ACCOUNTABILITY
    def distinct(sid):
        return len({r["raw_keyword"] for r in reg[sid]["keywords"]})

    acct = {
        "silo_00_brand_campus": distinct("SILO_00"),
        "silo_dept_hubs": sum(distinct(d["silo_id"]) for d in L.DEPARTMENTS.values()),
        "silo_course_pages": sum(distinct(c["silo_id"]) for c in courses.values()),
        "silo_art_cafe": distinct("SILO_CAFE_01"),
        "silo_fardis_geo": distinct("SILO_GEO_FARDIS"),
        "silo_audition_hub": distinct("SILO_CONV_AUDITION"),
        "unresolved_noise": len(unserved_demand),
    }
    acct["total_accounted"] = sum(v for k, v in acct.items() if k != "unresolved_noise") + acct["unresolved_noise"]
    acct["total_distinct_keywords"] = len(distinct_total)
    acct["total_raw_lines"] = len(raw_keywords)
    acct["duplicate_lines_collapsed"] = len(raw_keywords) - len(distinct_total)
    acct["balanced"] = acct["total_accounted"] == len(distinct_total)

    keyword_map = {
        "generated_at": L.now_iso(),
        "phase": "PHASE_1",
        "total_raw_keyword_lines": len(raw_keywords),
        "total_distinct_keywords": len(distinct_total),
        "orthographic_variants_preserved": sum(1 for r in records if r["orthographic_variant"]),
        "total_silos_created": len(reg),
        "silo_files": [os.path.relpath(p, L.ROOT).replace(os.sep, "/") for p in written],
        "serp_lock_mode": L.load_serp_matrix().get("downstream_directive", "USE_DETERMINISTIC_PERSIAN_STEM_RULES"),
        "department_alignment": dept_alignment,
        "course_silo_mappings": course_mappings,
        "cafe_venue_mapping": cafe_mapping,
        "fardis_geo_mapping": fardis_mapping,
        "audition_hub_mapping": audition_mapping,
        "brand_silo_mapping": {
            "silo_id": "SILO_00", "target_slug": "/",
            "keyword_count": distinct("SILO_00"),
            "note": ("همه پرس‌وجوهای «آدرس/کجاست» دو-قصدی هستند و طبق قانون Dual-Intent فاز ۱ "
                     "در سیلوی دوره مربوطه با section_target=SEC_CAMPUS_MAP_DIRECTIONS و "
                     "notes=DUAL_INTENT:SILO_00 قرار گرفته‌اند؛ بنابراین صفحه اصلی کلیدواژه انحصاریِ "
                     "دیتاست ندارد و با کلیدواژه برند/تاکسونومی ساخته می‌شود."),
            "dual_intent_inbound_keywords": [r["raw_keyword"] for r in records
                                             if r["section_target"] == "SEC_CAMPUS_MAP_DIRECTIONS"],
        },
        "female_instructor_gate": [
            {"silo_id": m["silo_id"], "course_id": m["course_id"],
             "demanded": m["catalog_verification"]["female_instructor_demanded_by_keywords"],
             "verified": m["catalog_verification"]["female_instructor_verified"],
             "priority_1_client_data_request": m["catalog_verification"]["female_data_gap"]}
            for m in course_mappings if m["catalog_verification"]["female_instructor_demanded_by_keywords"]
        ],
        "orphan_or_unserved_courses": orphan,
        "unresolved_keywords": unserved_demand,
        "keyword_accountability": acct,
    }
    L.write_json(os.path.join(L.OUTPUT, "academy_keyword_map.json"), keyword_map)

    # update macro topology
    macro_path = os.path.join(L.OUTPUT, "macro_topology.json")
    macro = L.read_json(macro_path, {})
    macro["phase"] = "PHASE_1"
    macro["updated_at"] = L.now_iso()
    macro["silo_summary"] = {
        "total_silos": len(reg),
        "silos_with_keywords": sum(1 for s in reg.values() if s["keywords"]),
        "silos_navigational_only": [sid for sid, s in reg.items() if not s["keywords"]],
        "keyword_accountability": acct,
    }
    L.write_json(macro_path, macro)

    # ---------------------------------------------------------------- GATE 1
    # Cannibalisation: within ONE geo market, a discipline stem family must map to
    # exactly one silo. (`کلاس آواز در کرج` vs `کلاس آواز در فردیس کرج` are a
    # deliberate geo split with DUAL_INTENT routing, not cannibalisation.)
    stem_owner = defaultdict(set)
    for r in records:
        n = r["normalized_keyword"]
        core = re.sub(r"(?<![\u0600-\u06FF])(" + "|".join(DISCIPLINE_STEMS) + r"|در|های|کرج|فردیس|برای|و)(?![\u0600-\u06FF])", " ", n)
        core = re.sub(r"\s+", " ", core).strip()
        if core:
            stem_owner[(core, r["geo_target"])].add(r["silo_id"])
    cannibal = {f"{k[0]}|{k[1]}": sorted(v) for k, v in stem_owner.items() if len(v) > 1}

    ortho_ok = all("ORTHO_VARIANT" in r["notes"] for r in records if r["orthographic_variant"])
    tsv_ok = True
    for p in written:
        for i, ln in enumerate(open(p, encoding="utf-8").read().rstrip("\n").split("\n")):
            if len(ln.split("\t")) != 8:
                tsv_ok = False
                print(f"  !! TSV column error in {p} line {i+1}")

    gates = {
        "G1_1_keyword_balance_100pct": acct["balanced"],
        "G1_2_zero_stem_cannibalization": len(cannibal) == 0,
        "G1_3_cafe_isolation_and_bridging": (cafe_mapping["keyword_count"] == 6 and
                                             len(cafe_mapping["linked_course_slugs"]) == 5),
        "G1_4_fardis_dual_routing_integrity": all(x["dual_intent_silo"] for x in fardis_routes),
        "G1_5_orthographic_coverage": ortho_ok,
        "G1_6_valid_tsv_and_json": tsv_ok,
    }
    if cannibal:
        print("  cannibalisation suspects:", list(cannibal.items())[:6])

    L.update_progress("PHASE_1", "COMPLETE",
                      ["output/silos/*.tsv", "output/academy_keyword_map.json", "output/macro_topology.json"],
                      gates, "PHASE_2")

    print("=" * 74)
    print("UNIFIED PHASE 1 — COMPLETE")
    print("=" * 74)
    print(f"  silos written          : {len(written)}  → output/silos/")
    print(f"  distinct keywords      : {len(distinct_total)} / raw lines {len(raw_keywords)}")
    print(f"  accountability balanced: {acct['balanced']}  ({acct['total_accounted']} accounted)")
    print(f"  course silos with demand: {sum(1 for m in course_mappings if m['keyword_count'])}/24")
    print(f"  female data gaps       : {[g['course_id'] for g in keyword_map['female_instructor_gate'] if g['priority_1_client_data_request']]}")
    for k, v in gates.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    return all(gates.values())


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
