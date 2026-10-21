#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP 1: LIVE SERP INTRA-CLUSTER MATRIX & PURE HTML DOM INSPECTOR
Role: Pure Data Collection, HTML Element-Level Inspection & SERP Reverse-Engineering
Features:
  - Multi-Key API Rotation (2,450 limit/key)
  - Pure HTML Tree Decomposition (Inspects actual tags, hierarchy, attributes, no CSS assumptions)
  - Detection of all Semantic HTML5, E-Commerce inputs/forms, Tables, Lists, and Custom Elements (<x-...>)
  - Intra-Cluster Rank Variance Analyzer (Why the same URL ranks #1 on keyword A but drops on keyword B)
  - SERP Algorithm Consensus & Competitor Blind-Spot Detection
  - Token-Safe Compact Architecture for Step 2
"""

import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
import re
import json
import time
import asyncio
import logging
from urllib.parse import urlparse
from collections import defaultdict
import httpx
from bs4 import BeautifulSoup, Tag

# ==============================================================================
# 0. DIRECTORIES & LOGGING SETUP
# ==============================================================================
os.makedirs("input", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("DataCollector")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("logs/step1_data_collector.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(file_formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("[%(asctime)s] %(message)s", "%H:%M:%S")
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ==============================================================================
# CONFIGURATION & FILE PATHS
# ==============================================================================
KEYWORDS_FILE = "input/keywords.txt"
KEYS_FILE = "input/serper_keys.txt"
KEY_STATE_FILE = "output/serper_key_usage.json"
RAW_SERP_CACHE = "output/raw_serp_cache.json"
DOM_XRAY_CACHE = "output/dom_xray_cache.json"
FINAL_MATRIX_FILE = "output/serp_algorithm_matrix.json"

CONCURRENT_DOM_SCRAPERS = 10
HTTP_TIMEOUT = 18.0
MAX_QUOTA_PER_KEY = 2450

SERPER_API_KEYS = []

# ==============================================================================
# 1. SERPER API KEY ROTATION MANAGER (2450 QUOTA PERSISTENCE)
# ==============================================================================
class SerperKeyManager:
    def __init__(self, keys_file: str, fallback_keys: list, state_file: str, max_limit: int = 2450):
        self.state_file = state_file
        self.max_limit = max_limit
        self.lock = asyncio.Lock()
        self.keys = self._load_keys(keys_file, fallback_keys)
        self.usage = self._load_state()

        logger.info(f"Initialized SerperKeyManager with {len(self.keys)} total keys.")
        self._log_summary()

    def _load_keys(self, keys_file: str, fallback_keys: list) -> list:
        keys = []
        if os.path.exists(keys_file):
            with open(keys_file, "r", encoding="utf-8") as f:
                for line in f:
                    k = line.strip()
                    if k and not k.startswith("#"):
                        keys.append(k)

        env_keys = os.getenv("SERPER_API_KEYS", "")
        if env_keys:
            keys.extend([k.strip() for k in env_keys.split(",") if k.strip()])

        single_env = os.getenv("SERPER_API_KEY", "")
        if single_env:
            keys.append(single_env.strip())

        keys.extend([k.strip() for k in fallback_keys if k.strip() and not k.startswith("PASTE_")])

        seen = set()
        deduped = []
        for k in keys:
            if k not in seen:
                seen.add(k)
                deduped.append(k)
        return deduped

    def _load_state(self) -> dict:
        state = {k: 0 for k in self.keys}
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    for k in self.keys:
                        if k in saved:
                            state[k] = saved[k]
            except Exception as e:
                logger.warning(f"Could not read key state file: {e}. Initializing fresh counters.")
        return state

    def _save_state(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.usage, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist key state: {e}")

    def _log_summary(self):
        for idx, k in enumerate(self.keys, start=1):
            masked = f"...{k[-6:]}" if len(k) > 6 else k
            count = self.usage.get(k, 0)
            status = "EXHAUSTED" if count >= self.max_limit else f"{count}/{self.max_limit}"
            logger.info(f"  └ Key #{idx} [{masked}]: {status}")

    async def get_active_key(self) -> str:
        async with self.lock:
            for k in self.keys:
                if self.usage[k] < self.max_limit:
                    return k
            raise RuntimeError(
                f"ALL {len(self.keys)} Serper API keys have reached their {self.max_limit} limit! "
                "Please add a new key to input/serper_keys.txt"
            )

    async def record_usage(self, key: str, credits_used: int = 1):
        async with self.lock:
            self.usage[key] = self.usage.get(key, 0) + credits_used
            count = self.usage[key]
            masked = f"...{key[-6:]}" if len(key) > 6 else key
            logger.debug(f"Key [{masked}] count: {count}/{self.max_limit}")

            if count >= self.max_limit:
                logger.warning(f"[!] KEY ROTATION TRIGGERED: Key [{masked}] reached {self.max_limit} threshold. Rotating.")

            self._save_state()

    async def mark_exhausted(self, key: str, reason: str = "Out of credits"):
        async with self.lock:
            masked = f"...{key[-6:]}" if len(key) > 6 else key
            logger.warning(f"[!] Serper key [{masked}] marked EXHAUSTED ({reason}). Forcing rotation.")
            self.usage[key] = self.max_limit
            self._save_state()

# ==============================================================================
# 2. PERSIAN NORMALIZER & CLUSTER RULES
# ==============================================================================
def normalize_persian(text: str) -> str:
    text = text.strip()
    replacements = {
        "ي": "ی", "ك": "ک", "\u200c": " ",
        "اموزشگاه": "آموزشگاه", "اموزش": "آموزش",
        "اواز": "آواز", "ادرس": "آدرس", "اکادمی": "آکادمی",
        "کلاسهای": "کلاس های"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text)

CLUSTER_RULES = [
    ("CAFE_VENUE", r"کافه|رستوران"),
    ("AUDITION_HUB", r"تست بازیگری"),
    ("GEO_FARDIS", r"فردیس"),
    ("CRS_PIANO", r"پیانو"),
    ("CRS_GUITAR", r"گیتار"),
    ("CRS_VIOLIN", r"ویولن"),
    ("CRS_SANTOOR", r"سنتور"),
    ("CRS_TAR_SETAR", r"سه تار|سه‌تار|\bتار\b"),
    ("CRS_TONBAK", r"تنبک"),
    ("CRS_DAF", r"\bدف\b|دف زنی"),
    ("CRS_KAMANCHEH", r"کمانچه"),
    ("CRS_TANBOUR", r"تنبور"),
    ("CRS_FLUTE", r"فلوت"),
    ("CRS_HANGDRUM", r"هنگ درام|هنگ‌درام"),
    ("CRS_ORGAN", r"\bارگ\b"),
    ("CRS_KIDS_MUSIC", r"موسیقی کودک"),
    ("CRS_VOCALS", r"آواز|اواز|خوانندگی"),
    ("DEPT_MUSIC", r"موسیقی"),
    ("CRS_KIDS_ACTING", r"(بازیگری|تئاتر|نمایش خلاق).*(کودک|نوجوان)"),
    ("CRS_ACTING", r"بازیگری|تئاتر|نمایش خلاق"),
    ("CRS_SPEECH", r"فن بیان|سخنوری|مجری"),
    ("CRS_VOICE_DUBBING", r"گویندگی|دوبله|دوبلاژ|دوبلوری"),
    ("CRS_PHOTOGRAPHY", r"عکاسی|فیلمبرداری"),
    ("CRS_FILM_EDITING", r"تدوین|ادیت"),
    ("CRS_DIRECTING_SCRIPT", r"کارگردانی|فیلمنامه"),
    ("CRS_MAKEUP", r"گریم|میکاپ"),
    ("CRS_PAINTING", r"نقاشی|طراحی"),
    ("CRS_CALLIGRAPHY", r"خوشنویسی|خطاطی|\bخط\b"),
]

def assign_cluster(kw: str) -> str:
    norm = normalize_persian(kw)
    for cluster_id, pattern in CLUSTER_RULES:
        if re.search(pattern, norm):
            return cluster_id
    return "GENERAL_ACADEMY"

# ==============================================================================
# 3. SERPER FETCHER WITH KEY ROTATION
# ==============================================================================
async def fetch_serper_top20(client: httpx.AsyncClient, query: str, key_mgr: SerperKeyManager, max_retries: int = 3) -> list:
    url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "gl": "ir",
        "hl": "fa",
        "num": 20
    }

    for attempt in range(1, max_retries + 1):
        try:
            current_key = await key_mgr.get_active_key()
            headers = {
                "X-API-KEY": current_key,
                "Content-Type": "application/json"
            }

            resp = await client.post(url, headers=headers, json=payload, timeout=20.0)

            if resp.status_code == 200:
                data = resp.json()
                credits_used = data.get("credits", 1)
                await key_mgr.record_usage(current_key, credits_used)
                results = data.get("organic", [])
                logger.debug(f"Fetched {len(results)} results for '{query}' (Credits: {credits_used})")
                return results

            elif resp.status_code in (401, 403):
                logger.warning(f"Key rejected by Serper (HTTP {resp.status_code}): {resp.text}")
                await key_mgr.mark_exhausted(current_key, reason=f"HTTP {resp.status_code}")
                continue

            elif resp.status_code == 429:
                wait_time = attempt * 2
                logger.warning(f"Serper rate limited (429). Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

            else:
                logger.error(f"Serper error HTTP {resp.status_code}: {resp.text}")
                return []

        except RuntimeError as re_err:
            logger.critical(str(re_err))
            raise re_err
        except Exception as e:
            logger.warning(f"Network error on attempt {attempt} for '{query}': {str(e)}")
            if attempt == max_retries:
                return []
            await asyncio.sleep(attempt)

    return []

# ==============================================================================
# 4. PURE HTML TREE INSPECTOR & LISTER (ZERO CSS GUESSWORK)
# ==============================================================================
def inspect_pure_html_dom(soup: BeautifulSoup) -> dict:
    """
    Pure HTML Tree Inspector & Lister.
    No CSS class guessing. No regex divination.
    Reads and lists:
      - All HTML tags used across the document (frequency & catalog)
      - Custom Web Components (any tag containing a hyphen, e.g. <product-card>)
      - Complete heading hierarchy (H1 - H6)
      - Interactive tags: <a> (with protocols: tel:, whatsapp, mailto:, anchors),
        <button>, <form>, <input>, <select>, <textarea>
      - Structured tags: <table>, <dl>, <ol>, <ul>, <details>, <dialog>
      - Machine attributes: microdata (itemprop/itemtype), ARIA roles, loading/fetchpriority
      - Section-by-section structural breakdown based on actual semantic containers
    """
    # 1. Global Tag Frequency Inventory
    all_tags = [t.name for t in soup.find_all(True) if t.name]
    tag_counts = {}
    for t in all_tags:
        tag_counts[t] = tag_counts.get(t, 0) + 1

    custom_tags = sorted(list(set(t for t in all_tags if "-" in t)))

    # 2. Heading Tree
    headings = []
    for h in soup.find_all(re.compile(r"^h[1-6]$")):
        text = h.get_text(" ", strip=True)
        if text:
            headings.append({"tag": h.name, "text": text[:100]})

    # 3. Interactive Anchors & Protocols
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(" ", strip=True)
        links.append({
            "href": href[:120],
            "text": text[:50],
            "is_tel": href.startswith("tel:"),
            "is_whatsapp": "wa.me" in href or "whatsapp" in href,
            "is_telegram": "t.me" in href or "telegram" in href,
            "is_mailto": href.startswith("mailto:"),
            "is_anchor": href.startswith("#") and len(href) > 1,
            "rel": a.get("rel", [])
        })

    # 4. Forms & Form Inputs
    forms = []
    for f in soup.find_all("form"):
        inputs_list = []
        for inp in f.find_all(["input", "select", "textarea", "button"]):
            inputs_list.append({
                "tag": inp.name,
                "type": inp.get("type", "text"),
                "name": inp.get("name", ""),
                "required": inp.has_attr("required")
            })
        forms.append({
            "action": f.get("action", "")[:100],
            "method": f.get("method", "get").upper(),
            "inputs_count": len(inputs_list),
            "inputs": inputs_list[:8]
        })

    buttons = [
        {"type": b.get("type", "button"), "text": b.get_text(" ", strip=True)[:40]}
        for b in soup.find_all("button") if b.get_text(strip=True)
    ]

    # 5. Microdata & Accessibility Attributes
    microdata_items = [
        {"itemtype": tag.get("itemtype"), "itemprop": tag.get("itemprop"), "tag": tag.name}
        for tag in soup.find_all(attrs={"itemprop": True})[:15]
    ]

    aria_roles = sorted(list(set(tag.get("role") for tag in soup.find_all(attrs={"role": True}))))

    # 6. Section-by-Section Structural Walk
    # Identify true structural/semantic containers
    containers = soup.find_all(["header", "nav", "main", "section", "article", "aside", "footer", "dialog"])
    if len(containers) < 3:
        body = soup.find("body") or soup
        containers = [c for c in body.children if isinstance(c, Tag) and c.name not in ["script", "style", "svg"]]

    sections = []
    for idx, c in enumerate(containers[:15], start=1):
        if not isinstance(c, Tag):
            continue

        raw_text = c.get_text(" ", strip=True)
        if len(raw_text) < 15 and not c.find(["img", "a", "button", "table", "form"]):
            continue

        sec_tags = sorted(list(set(t.name for t in c.find_all(True))))

        sec_headings = [
            {"tag": h.name, "text": h.get_text(" ", strip=True)[:80]}
            for h in c.find_all(re.compile(r"^h[1-6]$"))[:4]
        ]

        # Tables in section
        sec_tables = []
        for tbl in c.find_all("table")[:2]:
            caption = tbl.caption.get_text(strip=True) if tbl.caption else ""
            headers = [th.get_text(" ", strip=True) for th in tbl.find_all("th")][:6]
            sample_rows = [
                [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])][:6]
                for tr in tbl.find_all("tr")[:3]
            ]
            sec_tables.append({
                "caption": caption,
                "headers": headers,
                "row_count": len(tbl.find_all("tr")),
                "sample_rows": sample_rows
            })

        # Lists in section (ul, ol, dl)
        sec_lists = []
        for ul in c.find_all("ul")[:2]:
            items = [li.get_text(" ", strip=True) for li in ul.find_all("li", recursive=False)[:4]]
            if items:
                sec_lists.append({"type": "unordered_list", "sample_items": items})
        for ol in c.find_all("ol")[:2]:
            items = [li.get_text(" ", strip=True) for li in ol.find_all("li", recursive=False)[:4]]
            if items:
                sec_lists.append({"type": "ordered_list", "sample_items": items})
        for dl in c.find_all("dl")[:1]:
            dt_items = [dt.get_text(" ", strip=True) for dt in dl.find_all("dt")][:3]
            dd_items = [dd.get_text(" ", strip=True) for dd in dl.find_all("dd")][:3]
            sec_lists.append({"type": "definition_list", "terms": dt_items, "definitions": dd_items})

        # Native accordion tags (<details> / <summary>)
        sec_details = [
            {
                "summary": d.summary.get_text(" ", strip=True) if d.summary else "",
                "preview": d.get_text(" ", strip=True)[:80]
            }
            for d in c.find_all("details")[:4]
        ]

        # Section-specific links & CTAs
        sec_links = [
            {"text": a.get_text(" ", strip=True)[:35], "href": a["href"].strip()[:90]}
            for a in c.find_all("a", href=True)[:5]
            if a.get_text(strip=True) or a.get("href", "").startswith(("tel:", "mailto:", "http"))
        ]

        # Media in section
        sec_images = [
            {
                "src": img.get("src", "")[:90] or img.get("data-src", "")[:90],
                "alt": img.get("alt", "").strip()[:60],
                "loading": img.get("loading", "eager"),
                "has_dimensions": bool(img.get("width") and img.get("height"))
            }
            for img in c.find_all("img")[:4] if img.get("src") or img.get("data-src")
        ]

        media_summary = {
            "images": sec_images,
            "videos_count": len(c.find_all(["video", "iframe", "embed"])),
            "audio_count": len(c.find_all("audio"))
        }

        sections.append({
            "section_number": idx,
            "container_tag": c.name,
            "html_tags_present": sec_tags,
            "headings": sec_headings,
            "tables": sec_tables,
            "lists": sec_lists,
            "details_accordions": sec_details,
            "links": sec_links,
            "media": media_summary,
            "text_sample": raw_text[:120]
        })

    return {
        "html_tag_inventory": tag_counts,
        "custom_web_components": custom_tags,
        "heading_tree": headings,
        "links_summary": {
            "total_links_count": len(links),
            "tel_links": [l for l in links if l["is_tel"]],
            "whatsapp_links": [l for l in links if l["is_whatsapp"]],
            "telegram_links": [l for l in links if l["is_telegram"]],
            "sample_links": links[:8]
        },
        "forms": forms,
        "buttons": buttons[:6],
        "microdata": microdata_items,
        "aria_roles": aria_roles,
        "sections": sections
    }

# ==============================================================================
# 5. DOM X-RAY SCRAPER
# ==============================================================================
async def extract_dom_xray(client: httpx.AsyncClient, url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8"
    }
    try:
        resp = await client.get(url, headers=headers, follow_redirects=True, timeout=HTTP_TIMEOUT)
        if resp.status_code != 200:
            return {"url": url, "fetch_ok": False, "status": resp.status_code}

        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type:
            return {"url": url, "fetch_ok": False, "status": "non_html"}

        # Try lxml parser first, fallback to standard html.parser
        try:
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception:
            soup = BeautifulSoup(resp.text, "html.parser")

        # 1. JSON-LD Schema Types
        schema_types = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
                if isinstance(data, dict):
                    if "@graph" in data:
                        for node in data["@graph"]:
                            if isinstance(node, dict) and "@type" in node:
                                schema_types.append(node["@type"])
                    elif "@type" in data:
                        schema_types.append(data["@type"])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "@type" in item:
                            schema_types.append(item["@type"])
            except Exception:
                pass

        # 2. Meta tags
        title = soup.title.get_text(strip=True) if soup.title else ""
        meta_desc = ""
        md_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if md_tag and md_tag.get("content"):
            meta_desc = md_tag["content"].strip()

        # 3. Pure HTML Inspection (before decomposing script/style)
        html_dom_inspection = inspect_pure_html_dom(soup)

        # 4. Text and word count
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()

        h1s = [h.get_text(" ", strip=True) for h in soup.find_all("h1")][:3]
        h2s = [h.get_text(" ", strip=True) for h in soup.find_all("h2")][:15]

        body_text = soup.get_text(" ", strip=True)
        word_count = len(body_text.split())

        # 5. Core structural signals
        signals = {
            "has_table": bool(soup.find("table")),
            "table_count": len(soup.find_all("table")),
            "has_details_faq": bool(soup.find("details")),
            "has_form": bool(soup.find("form")),
            "has_video": bool(soup.find(["video", "iframe"])),
            "image_count": len(soup.find_all("img")),
            "has_tel_link": len(html_dom_inspection["links_summary"]["tel_links"]) > 0,
            "has_whatsapp_link": len(html_dom_inspection["links_summary"]["whatsapp_links"]) > 0,
        }

        return {
            "url": url,
            "domain": urlparse(url).netloc,
            "fetch_ok": True,
            "title": title,
            "meta_description": meta_desc,
            "h1": h1s,
            "h2": h2s,
            "word_count": word_count,
            "schema_types": list(set(schema_types)),
            "signals": signals,
            "html_dom_inspection": html_dom_inspection
        }
    except Exception as e:
        return {"url": url, "fetch_ok": False, "error": str(e)}

# ==============================================================================
# 6. INTRA-CLUSTER OVERLAP & CO-RANKING VARIANCE
# ==============================================================================
def compute_rank_variance_and_deltas(url_footprint: dict, dom_cache: dict) -> list:
    """
    Examines URLs ranking across multiple cluster queries to detect
    exact structural reasons for position shifts (e.g., #1 vs #14).
    """
    variance_records = []
    
    for url, kw_rank_list in url_footprint.items():
        if len(kw_rank_list) < 2:
            continue
        
        ranks = [x["rank"] for x in kw_rank_list]
        min_rank = min(ranks)
        max_rank = max(ranks)
        rank_delta = max_rank - min_rank
        
        dom = dom_cache.get(url, {})
        if not dom.get("fetch_ok"):
            continue

        winning_kws = [x["keyword"] for x in kw_rank_list if x["rank"] <= 3]
        lagging_kws = [x["keyword"] for x in kw_rank_list if x["rank"] >= 8]

        drop_diagnostics = []
        dom_text_blob = " ".join(dom.get("h1", []) + dom.get("h2", []) + [dom.get("title", "")])
        for lag in lagging_kws:
            lag_norm = normalize_persian(lag)
            if "شهریه" in lag_norm or "قیمت" in lag_norm:
                if not dom.get("signals", {}).get("has_table"):
                    drop_diagnostics.append(f"Dropped on '{lag}' (Rank #{next(x['rank'] for x in kw_rank_list if x['keyword'] == lag)}) -> Missing structured <table>.")
            elif "فردیس" in lag_norm and "فردیس" not in dom_text_blob:
                drop_diagnostics.append(f"Dropped on '{lag}' -> Missing explicit geo-modifier in HTML headings.")

        variance_records.append({
            "url": url,
            "domain": dom.get("domain", ""),
            "co_ranking_keyword_count": len(kw_rank_list),
            "best_rank": min_rank,
            "worst_rank": max_rank,
            "rank_delta_spread": rank_delta,
            "winning_keywords_top3": winning_kws,
            "lagging_keywords_pos8plus": lagging_kws,
            "drop_diagnostics": drop_diagnostics[:4],
            "full_cluster_rank_vector": kw_rank_list
        })

    variance_records.sort(key=lambda x: (x["best_rank"], -x["co_ranking_keyword_count"]))
    return variance_records

def analyze_cluster_overlap(cluster_id: str, kw_serps: dict, dom_cache: dict) -> dict:
    keywords = list(kw_serps.keys())
    if not keywords:
        return {}

    seed_kw = sorted(keywords, key=lambda k: (0 if "آموزش" in k or "کلاس" in k else 1, len(k)))[0]
    seed_top10_urls = {r["link"] for r in kw_serps[seed_kw][:10] if "link" in r}

    url_footprint = defaultdict(list)
    sub_kw_overlap = {}

    for kw, results in kw_serps.items():
        top10_urls = {r["link"] for r in results[:10] if "link" in r}
        overlap_count = len(seed_top10_urls.intersection(top10_urls))
        overlap_pct = round((overlap_count / max(len(seed_top10_urls), 1)) * 100, 1)
        sub_kw_overlap[kw] = overlap_pct

        for idx, r in enumerate(results[:20], start=1):
            u = r.get("link")
            if u:
                url_footprint[u].append({"keyword": kw, "rank": idx})

    omni_winners = sorted(
        url_footprint.items(),
        key=lambda item: (len(item[1]), -sum(x["rank"] for x in item[1]) / len(item[1])),
        reverse=True
    )[:10]

    top_records = []
    competitor_schemas = set()
    for url, ranks in omni_winners:
        avg_rank = round(sum(x["rank"] for x in ranks) / len(ranks), 1)
        dom = dom_cache.get(url, {})
        schema_types = dom.get("schema_types", [])
        competitor_schemas.update(schema_types)
        
        h1 = dom.get("h1", [])[:2]
        h2 = dom.get("h2", [])[:6]
        word_count = dom.get("word_count", 0)
        table_count = dom.get("signals", {}).get("table_count", 0)
        faq_detected = dom.get("signals", {}).get("has_details_faq", False)
        
        archetype = "unknown"
        url_lower = url.lower()
        if any(x in url_lower for x in ["course", "class", "کلاس", "دوره", "آموزش"]):
            archetype = "course_landing"
        elif any(x in url_lower for x in ["blog", "article", "مقاله", "post"]):
            archetype = "blog_article"
        elif any(x in url_lower for x in ["price", "شهریه", "قیمت", "هزینه"]):
            archetype = "price_page"
        elif any(x in url_lower for x in ["contact", "about", "درباره", "تماس"]):
            archetype = "info_page"
        
        top_records.append({
            "url": url,
            "co_ranking_keyword_count": len(ranks),
            "avg_rank_position": avg_rank,
            "shared_intra_cluster_footprint": ranks,
            "page_archetype": archetype,
            "h1": h1,
            "h2_sample": h2,
            "word_count": word_count,
            "schema_types": schema_types,
            "table_count": table_count,
            "faq_detected": faq_detected,
            "html_dom_inspection": dom.get("html_dom_inspection", {})
        })

    rank_variance = compute_rank_variance_and_deltas(url_footprint, dom_cache)

    # Top-5 Consensus Statistics
    top5_doms = [dom_cache.get(u, {}) for u, _ in omni_winners[:5] if u in dom_cache]
    valid_top5 = [d for d in top5_doms if d.get("fetch_ok")]
    num_top = max(len(valid_top5), 1)

    consensus_stats = {
        "pct_with_table": round(sum(1 for d in valid_top5 if d.get("signals", {}).get("has_table")) / num_top * 100, 1),
        "pct_with_form": round(sum(1 for d in valid_top5 if d.get("signals", {}).get("has_form")) / num_top * 100, 1),
        "pct_with_video": round(sum(1 for d in valid_top5 if d.get("signals", {}).get("has_video")) / num_top * 100, 1),
        "pct_with_tel_link": round(sum(1 for d in valid_top5 if d.get("signals", {}).get("has_tel_link")) / num_top * 100, 1),
        "pct_with_whatsapp_link": round(sum(1 for d in valid_top5 if d.get("signals", {}).get("has_whatsapp_link")) / num_top * 100, 1),
        "pct_with_schema": round(sum(1 for d in valid_top5 if len(d.get("schema_types", [])) > 0) / num_top * 100, 1),
        "avg_winner_word_count": round(sum(d.get("word_count", 0) for d in valid_top5) / num_top)
    }

    # Discover Competitor Blind Spots
    blind_spots = []
    if consensus_stats["pct_with_table"] < 40:
        blind_spots.append("Competitors omit structured <table> elements. Adding an HTML table provides an immediate Information Gain signal.")
    if consensus_stats["pct_with_tel_link"] < 50:
        blind_spots.append("Fewer than half of top competitors have direct tel: action links above the fold.")
    if consensus_stats["pct_with_whatsapp_link"] < 40:
        blind_spots.append("Competitors lack direct WhatsApp conversion triggers.")
    if consensus_stats["pct_with_video"] < 30:
        blind_spots.append("Zero or few top competitors embed real <video> elements.")

    merge_evidence = []
    borderline_keywords = []
    merged_keywords = []
    
    for kw, pct in sub_kw_overlap.items():
        if pct >= 60:
            merge_evidence.append({"keyword": kw, "top10_overlap_pct": pct})
            merged_keywords.append(kw)
        elif 30 <= pct < 60:
            borderline_keywords.append({
                "keyword": kw,
                "top10_overlap_pct": pct,
                "directive": "EVALUATE_IN_PAGE_SECTION_OR_CHILD_PAGE"
            })

    archetype_map = {
        "CRS_PIANO": "course_landing",
        "CRS_GUITAR": "course_landing",
        "CRS_VIOLIN": "course_landing",
        "CRS_TAR_SETAR": "course_landing",
        "CRS_TONBAK": "course_landing",
        "CRS_SANTOOR": "course_landing",
        "CRS_DAF": "course_landing",
        "CRS_KAMANCHEH": "course_landing",
        "CRS_FLUTE": "course_landing",
        "CRS_ORGAN": "course_landing",
        "CRS_HANGDRUM": "course_landing",
        "CRS_TANBOUR": "course_landing",
        "CRS_KIDS_MUSIC": "course_landing",
        "CRS_ACTING": "course_landing",
        "CRS_KIDS_ACTING": "course_landing",
        "CRS_SPEECH": "course_landing",
        "CRS_VOCALS": "course_landing",
        "CRS_VOICE_DUBBING": "course_landing",
        "CRS_PHOTOGRAPHY": "course_landing",
        "CRS_FILM_EDITING": "course_landing",
        "CRS_DIRECTING_SCRIPT": "course_landing",
        "CRS_MAKEUP": "course_landing",
        "CRS_PAINTING": "course_landing",
        "CRS_CALLIGRAPHY": "course_landing",
        "AUDITION_HUB": "course_landing",
        "GEO_FARDIS": "location_page",
        "CAFE_VENUE": "venue_page",
        "DEPT_MUSIC": "department_page",
    }
    primary_archetype = archetype_map.get(cluster_id, "course_landing")
    word_target = max(consensus_stats["avg_winner_word_count"] + 300, 1600)

    all_keywords_text = " ".join(keywords)
    needs_price_table = any(term in all_keywords_text for term in ["شهریه", "قیمت", "هزینه", "اقساط"]) or consensus_stats["pct_with_table"] >= 40
    needs_faq = any(term in all_keywords_text for term in ["کجاست", "چگونه", "آیا", "شرایط", "چقدر", "مدت"])

    silo_directives = {
        "merge_evidence": merge_evidence,
        "borderline_keywords_30_to_59_pct": borderline_keywords,
        "sub_keywords_merged_into_main_page": merged_keywords,
        "primary_page_archetype_required": primary_archetype,
        "recommended_word_count_target": word_target,
        "competitor_schemas_detected": list(competitor_schemas)[:10],
        "requires_comparison_or_tuition_table": needs_price_table,
        "requires_faq_module": needs_faq,
        "competitor_blind_spots_information_gain": blind_spots
    }

    return {
        "cluster_id": cluster_id,
        "main_seed_keyword": seed_kw,
        "total_keywords_in_cluster": len(keywords),
        "sub_keyword_top10_overlap_pct": sub_kw_overlap,
        "serp_consensus_statistics": consensus_stats,
        "top_5_omni_winner_urls": top_records[:5],
        "top_omni_winner_urls": top_records,
        "intra_cluster_rank_variance_analysis": rank_variance[:6],
        "phase_1_and_2_silo_directives": silo_directives,
    }

# ==============================================================================
# 7. MAIN RUNNER
# ==============================================================================
async def main():
    logger.info("=== STEP 1: INITIALIZING LIVE SERP & PURE HTML DOM INSPECTOR ===")

    if not os.path.exists(KEYWORDS_FILE):
        logger.error(f"Missing file: {KEYWORDS_FILE}. Create it and add Persian keywords (one per line).")
        return

    with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
        raw_keywords = [line.strip() for line in f if line.strip()]

    logger.info(f"Loaded {len(raw_keywords)} keywords from {KEYWORDS_FILE}")

    key_mgr = SerperKeyManager(
        keys_file=KEYS_FILE,
        fallback_keys=SERPER_API_KEYS,
        state_file=KEY_STATE_FILE,
        max_limit=MAX_QUOTA_PER_KEY
    )

    if not key_mgr.keys:
        logger.error(f"No Serper API keys found! Add them to '{KEYS_FILE}' or set SERPER_API_KEYS environment variable.")
        return

    serp_cache = {}
    if os.path.exists(RAW_SERP_CACHE):
        try:
            with open(RAW_SERP_CACHE, "r", encoding="utf-8") as f:
                serp_cache = json.load(f)
            logger.info(f"Loaded {len(serp_cache)} cached SERP results.")
        except Exception as e:
            logger.warning(f"Error reading SERP cache: {e}. Starting fresh.")

    async with httpx.AsyncClient(verify=False, limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)) as client:
        pending_kws = [k for k in raw_keywords if k not in serp_cache]

        if pending_kws:
            logger.info(f"Fetching SERP Top-20 for {len(pending_kws)} pending queries...")
            for idx, kw in enumerate(pending_kws, start=1):
                pct = round((idx / len(pending_kws)) * 100, 1)
                active_key = await key_mgr.get_active_key()
                masked_key = f"...{active_key[-6:]}"
                used_so_far = key_mgr.usage.get(active_key, 0)
                
                logger.info(f"[{idx}/{len(pending_kws)} - {pct}%] [Key {masked_key} ({used_so_far}/{MAX_QUOTA_PER_KEY})] Querying: '{kw}'")

                results = await fetch_serper_top20(client, kw, key_mgr)
                serp_cache[kw] = results

                if idx % 10 == 0:
                    with open(RAW_SERP_CACHE, "w", encoding="utf-8") as f:
                        json.dump(serp_cache, f, ensure_ascii=False, indent=2)

                await asyncio.sleep(0.15)

            with open(RAW_SERP_CACHE, "w", encoding="utf-8") as f:
                json.dump(serp_cache, f, ensure_ascii=False, indent=2)
            logger.info("All SERP searches completed.")

        unique_urls = set()
        clusters = defaultdict(dict)
        for kw in raw_keywords:
            results = serp_cache.get(kw, [])
            cid = assign_cluster(kw)
            clusters[cid][kw] = results
            for r in results[:10]:
                link = r.get("link")
                if link and link.startswith("http"):
                    unique_urls.add(link)

        logger.info(f"Discovered {len(unique_urls)} unique competitor URLs across {len(clusters)} clusters.")

        dom_cache = {}
        if os.path.exists(DOM_XRAY_CACHE):
            try:
                with open(DOM_XRAY_CACHE, "r", encoding="utf-8") as f:
                    dom_cache = json.load(f)
                logger.info(f"Loaded {len(dom_cache)} cached DOM records.")
            except Exception as e:
                logger.warning(f"Error reading DOM cache: {e}.")

        urls_to_scrape = [u for u in unique_urls if u not in dom_cache]
        if urls_to_scrape:
            logger.info(f"Starting Pure HTML DOM Inspection on {len(urls_to_scrape)} URLs (Concurrency: {CONCURRENT_DOM_SCRAPERS})...")
            sem = asyncio.Semaphore(CONCURRENT_DOM_SCRAPERS)
            completed_count = 0
            total_scrape = len(urls_to_scrape)

            async def sem_scrape(u):
                nonlocal completed_count
                async with sem:
                    res = await extract_dom_xray(client, u)
                    completed_count += 1
                    if completed_count % 10 == 0 or completed_count == total_scrape:
                        pct = round((completed_count / total_scrape) * 100, 1)
                        logger.info(f"[HTML Scrape: {completed_count}/{total_scrape} - {pct}%] {u[:60]}...")
                    return u, res

            tasks = [sem_scrape(u) for u in urls_to_scrape]
            for coro in asyncio.as_completed(tasks):
                u, xray = await coro
                dom_cache[u] = xray

                if len(dom_cache) % 25 == 0:
                    with open(DOM_XRAY_CACHE, "w", encoding="utf-8") as f:
                        json.dump(dom_cache, f, ensure_ascii=False, indent=2)

            with open(DOM_XRAY_CACHE, "w", encoding="utf-8") as f:
                json.dump(dom_cache, f, ensure_ascii=False, indent=2)
            logger.info("Pure HTML DOM Scraping complete.")

    logger.info("Computing intra-cluster overlap, rank variance, and competitor blind-spots...")
    clusters_decoded = []
    for cid, kw_serps in clusters.items():
        analysis = analyze_cluster_overlap(cid, kw_serps, dom_cache)
        clusters_decoded.append(analysis)

    final_matrix = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "academy_brand": "آموزشگاه سینمایی، بازیگری و موسیقی آنک - کرج",
        "primary_city": "کرج",
        "total_keywords_analyzed": len(raw_keywords),
        "total_unique_urls_xrayed": len(unique_urls),
        "clusters_decoded": clusters_decoded
    }

    with open(FINAL_MATRIX_FILE, "w", encoding="utf-8") as f:
        json.dump(final_matrix, f, ensure_ascii=False, indent=2)

    logger.info(f"[✓] Complete! Master HTML matrix saved to: {FINAL_MATRIX_FILE}")
    logger.info(f"[✓] Key usage report saved to: {KEY_STATE_FILE}")

if __name__ == "__main__":
    asyncio.run(main())