# ============================================================
# ZENTIC MEDIA — CLIENT HUNTING AUTOMATION
# fb_group_monitor.py — Facebook Group Video Editor Hiring Radar
# Powered by Gemini AI Intent Classifier + Instant Telegram Alerts
# ============================================================

import os
import re
import json
import time
import threading
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from config import cfg
from database import (
    get_all_fb_groups, insert_fb_alert, is_fb_post_seen,
    update_fb_group_scan_stats, get_fb_alerts
)
from telegram_bot import alert_fb_hiring_post

# ── Strict Freshness Filter (Max 3 Hours) ───────────────────
def is_post_fresh(content: str, max_hours: int = 3) -> bool:
    """
    SMART FILTER: Accepts fresh leads posted within the last 3 hours.
    Checks the post HEADER (first 350 chars where author & post timestamp live)
    so recent comments on old posts don't cause false positives.
    Only EXPLICITLY OLD posts (yesterday, 4h+, past dates) are rejected.
    """
    header = content[:350].lower()
    full = content.lower()

    # 1. Explicit OLD indicators in post header -> REJECT IMMEDIATELY
    old_keywords = [
        'yesterday', 'গতকাল', 'days ago', 'দিন আগে', 'day ago',
        'weeks ago', 'সপ্তাহ আগে', 'week ago',
        'months ago', 'মাস আগে', 'month ago',
        'years ago', 'বছর আগে', 'year ago',
        'last week', 'last month', 'last year',
        '2 days ago', '3 days ago', '4 days ago', '5 days ago',
        'গত সপ্তাহে', 'গত মাসে', 'গত বছর'
    ]
    for old in old_keywords:
        if old in header:
            return False

    # Check for '2d', '3d', '1w' in header
    if re.search(r'\b\d+\s*(?:d|days?|দিন|w|weeks?)\b', header):
        return False

    # Check past years (2020-2025) in header
    if re.search(r'\b(201\d|202[0-5])\b', header):
        return False

    # Specific OLD calendar months paired with a day number in header
    old_months = [
        'january', 'february', 'march', 'april', 'june',
        'july', 'august', 'september', 'october', 'december',
        'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'dec',
        'জানুয়ারি', 'ফেব্রুয়ারি', 'মার্চ', 'এপ্রিল', 'মে', 'জুন',
        'জুলাই', 'আগস্ট', 'সেপ্টেম্বর', 'অক্টোবর', 'ডিসেম্বর'
    ]
    for m in old_months:
        if re.search(r'\b\d{1,2}\s+' + m + r'\b|\b' + m + r'\s+\d{1,2}\b', header):
            return False

    # 2. Fresh signals in header (< 1 hour) -> ACCEPT
    if 'just now' in header or 'এইমাত্র' in header:
        return True
    if re.search(r'\b\d+\s*(?:m|min|mins|minutes?|মিনিট)\b', header):
        return True

    # 3. Fresh Hours in header (<= max_hours) -> ACCEPT
    if 'about an hour' in header or 'an hour ago' in header or '১ ঘণ্টা' in header or '1 hour' in header:
        return True

    hr_matches = re.findall(r'\b(\d+)\s*(?:h|hr|hrs|hours?|ঘণ্টা|ঘন্টা)\b', header)
    if hr_matches:
        try:
            min_hr = min(int(h) for h in hr_matches)
            if min_hr <= max_hours:
                return True
            else:
                return False  # explicitly 4h+ -> reject
        except ValueError:
            pass

    # 4. Fallback check across full text for explicit old indicators
    for old in old_keywords:
        if old in full:
            return False

    # 5. No timestamp found -> ALLOW (login wall / hidden timestamp)
    return True

# ── AI / Intent Classification using Gemini LLM ──────────────
def classify_fb_post_with_ai(content: str, author_name: str = "", group_name: str = "") -> Dict[str, Any]:
    """
    Classify whether a post is a CLIENT HIRING a video editor,
    or a FREELANCER looking for work.
    Extracts contact info, budget, job type, and summary.
    """
    # 0. STRICT 3-Hour Freshness Check — drops old posts immediately
    if not is_post_fresh(content, max_hours=3):
        return {
            "is_hiring": False,
            "confidence_score": 0,
            "reason": "Post is older than 3 hours"
        }

    # 1. Try Gemini AI if API Key is available
    if cfg.GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=cfg.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""You are an elite AI recruiting intelligence engine specifically built for Video Editing agencies and Freelancers.
Your task is to analyze a Facebook group post written in English, Bengali (বাংলা), or Banglish, and determine the TRUE INTENT:
Is this author SPENDING MONEY to get video editing done (A CLIENT / EMPLOYER / CREATOR HIRING)?
Or are they TRYING TO EARN MONEY by offering editing services (AN EDITOR / FREELANCER / AGENCY SELLING THEMSELVES)?

CORE CLASSIFICATION PRINCIPLE:
- WHO IS PAYING?
  * If the author is offering money/projects to hire someone -> is_hiring = TRUE
  * If the author is asking for money/clients for their own services -> is_hiring = FALSE

VARIATIONS OF HIRING POSTS (ALL MUST BE DETECTED AS TRUE):
1. Direct Hiring: "Need video editor", "Hiring for YouTube", "Video editor lagbe", "Looking for someone to edit reels"
2. Style Matching: "Looking for an editor who can edit like Iman Gadzhi / Ali Abdaal / Magnates Media / MrBeast style"
3. Banglish / Bengali: "Amar channel er jonno ekjon valo editor dorkar, inbox e rate pathan", "একটি ইউটিউব চ্যানেলের জন্য নিয়মিত ভিডিও এডিটর আবশ্যক"
4. Creative / Story: "Launching my new podcast next week, need a creative wizard to handle 3 long-form episodes and 15 shorts per month"
5. Agency Scaling: "We are onboarding 5 new clients and need 2 remote video editors to join our team"
6. Urgent / Immediate: "Who is free this weekend for a 10-minute vlog edit? Paying well."
7. Portfolio Requests: "Drop your editing portfolio and hourly rate below", "Need someone with After Effects + Premiere Pro knowledge, inbox me"

VARIATIONS OF FREELANCER PROMO POSTS (ALL MUST BE STRICTLY DISCARDED AS FALSE):
1. Self-promo: "I am a professional video editor with 3 years experience, hire me"
2. Portfolio Showcases: "Check out my latest edit", "Rate my edit", "Link to my Behance/Drive portfolio"
3. Discount/Offers: "Special 50% discount on video editing for new clients", "Cheap video editing services"
4. Bangla promo: "আমি একজন প্রফেশনাল ভিডিও এডিটর, কারো কি এডিটর লাগবে?", "কম খরচে ভিডিও এডিটিং সেবা দিচ্ছি"

POST CONTENT:
\"\"\"{content}\"\"\"

AUTHOR: {author_name}
GROUP: {group_name}

Respond ONLY with valid JSON in this exact structure:
{{
  "is_hiring": true,
  "confidence_score": 98,
  "client_name": "...",
  "job_type": "YouTube Long-form / Shorts & Reels / Gaming / Documentary / Podcast / Motion Graphics",
  "budget": "e.g. $60/video or 20,000 BDT/month or Negotiable or Not specified",
  "contact_phone": "+8801... or phone number if mentioned",
  "contact_whatsapp": "whatsapp number or wa.me link if mentioned",
  "contact_email": "email if mentioned",
  "contact_telegram": "telegram handle if mentioned",
  "ai_summary": "Crisp 1-2 sentence Bengali or English summary of exact requirements and conditions"
}}
"""
            res = model.generate_content(
                prompt,
                generation_config={"temperature": 0.1, "response_mime_type": "application/json"}
            )
            raw = res.text.strip()
            data = json.loads(raw)
            return data
        except Exception as e:
            print(f"[FB Monitor AI] Gemini API call failed: {e}. Falling back to Smart Rule Classifier.")

    # 2. High-Precision Heuristic & Regex Fallback Classifier
    return classify_fb_post_heuristic(content, author_name)


def classify_fb_post_heuristic(content: str, author_name: str = "") -> Dict[str, Any]:
    """Smart Rule-based Classifier with regex contact extraction."""
    c_lower = content.lower()

    # Negative patterns (freelancer promoting themselves)
    freelancer_patterns = [
        r'\bi am a video editor\b',
        r'\bi am professional video editor\b',
        r'\bi will edit\b',
        r'\bhire me\b',
        r'\bmy portfolio\b',
        r'\bcheck my portfolio\b',
        r'\bportfolio link\b',
        r'\bavailable for work\b',
        r'\blooking for clients\b',
        r'\bavailable for hire\b',
        r'\bavailable for projects\b',
        r'\bare you looking for (?:a |an )?(?:video )?editor\b',
        r'\bdo you need (?:a |an )?(?:video )?editor\b',
        r'\bopen for commissions\b',
        r'\bopen for projects\b',
        r'\baccepting new clients\b',
        r'\bfeel free to dm\b',
        r'\bping me for editing\b',
        r'\bami video editor\b',
        r'\bami kaj korbo\b',
        r'\bamar portfolio\b',
        r'\border now\b',
        r'\bdm me for editing\b',
        r'\bdiscount on editing\b',
        r'\bcheap price\b',
        r'\breasonable price\b'
    ]

    is_freelancer = any(re.search(p, c_lower) for p in freelancer_patterns)

    # Positive hiring patterns (English + Banglish + Bengali)
    hiring_patterns = [
        r'\b(?:need|looking\s+for|hiring|seeking|want|require)\b[^\.\n\?!]{0,40}\b(?:video\s+editor|editor|motion\s+designer|animator)\b',
        r'\b(?:video\s+editor|editor)\s+(?:lagbe|dorkar|khujchi|chahida|need|hiring)\b',
        r'\b(?:we\s+are\s+hiring|urgently\s+need|urgent\s+requirement|job\s+offer|job\s+circular)\b',
        r'\b(?:pay|budget|salary|rate)\s*[:=–-]?\s*\$?\d+',
        r'\b(?:send\s+portfolio|inbox\s+with\s+portfolio|inbox\s+your\s+rate|apply\s+at)\b',
        r'\b(?:who\s+can\s+edit\s+my\s+videos|need\s+someone\s+to\s+edit)\b',
        r'ভিডিও\s*এডিটর\s*লাগবে',
        r'ভিডিও\s*এডিটর\s*দরকার',
        r'এডিটর\s*লাগবে',
        r'এডিটর\s*আবশ্যক',
        r'ভিডিও\s*এডিটর\s*আবশ্যক',
        r'ভিডিও\s*এডিটর\s*খুঁজছি'
    ]

    is_hiring = any(re.search(p, c_lower) for p in hiring_patterns)

    # If both detected, hiring wins only if explicitly hiring
    if is_freelancer and not any(re.search(p, c_lower) for p in [r'\bwe are hiring\b', r'\bvideo editor lagbe\b', r'\bjob offer\b']):
        is_hiring = False

    # Extract Phone / WhatsApp
    phones = re.findall(r'(?:\+?880\s?1[3-9]\d{8}|01[3-9]\d{8}|\+?1\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})', content)
    contact_phone = phones[0].replace(' ', '').replace('-', '') if phones else ""

    # Extract Email
    emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', content)
    contact_email = emails[0] if emails else ""

    # Extract Budget
    budget_match = re.search(r'(?:budget|rate|salary|pay)\s*[:=–-]?\s*(\$?\d+[\d,]*\s*(?:USD|k|BDT|tk|\/video|\/mo|\/month)?)', content, re.IGNORECASE)
    budget = budget_match.group(1).strip() if budget_match else ("Negotiable" if is_hiring else "Not specified")

    # Determine Job Type
    job_type = "General Video Editing"
    if "short" in c_lower or "reel" in c_lower or "tiktok" in c_lower:
        job_type = "Shorts / Reels / TikTok"
    elif "youtube" in c_lower or "long" in c_lower:
        job_type = "YouTube Long-form"
    elif "podcast" in c_lower:
        job_type = "Podcast Editing"
    elif "gaming" in c_lower:
        job_type = "Gaming Videos"
    elif "motion" in c_lower or "after effect" in c_lower:
        job_type = "Motion Graphics"

    # AI Summary
    summary = content[:200] + ("..." if len(content) > 200 else "")

    return {
        "is_hiring": is_hiring,
        "confidence_score": 92 if is_hiring else 20,
        "client_name": author_name or "Client",
        "job_type": job_type,
        "budget": budget,
        "contact_phone": contact_phone,
        "contact_whatsapp": contact_phone,
        "contact_email": contact_email,
        "contact_telegram": "",
        "ai_summary": summary
    }


def _parse_fb_cookies() -> tuple:
    """Parses cfg.FB_COOKIES from JSON string or semicolon-separated format."""
    raw = (getattr(cfg, "FB_COOKIES", "") or "").strip()
    if not raw:
        return [], ""

    cookie_list = []
    # If JSON list of cookie dicts
    if raw.startswith("["):
        try:
            items = json.loads(raw)
            c_parts = []
            for item in items:
                name = item.get("name", "")
                val = item.get("value", "")
                if name and val:
                    cookie_list.append({
                        "name": name,
                        "value": str(val),
                        "domain": item.get("domain", ".facebook.com"),
                        "path": item.get("path", "/")
                    })
                    c_parts.append(f"{name}={val}")
            return cookie_list, "; ".join(c_parts)
        except Exception:
            pass

    # Semicolon separated string
    c_parts = []
    for part in raw.split(';'):
        if '=' in part:
            k, v = part.strip().split('=', 1)
            k, v = k.strip(), v.strip()
            if k and v:
                cookie_list.append({
                    "name": k,
                    "value": v,
                    "domain": ".facebook.com",
                    "path": "/"
                })
                c_parts.append(f"{k}={v}")
    return cookie_list, "; ".join(c_parts)


# ── Facebook Group Post Scraper ──────────────────────────────
def scrape_facebook_group_posts(group_url: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Scrape recent posts from a Facebook Group.
    Uses authenticated Playwright session with user cookies for high accuracy.
    Captures posts during incremental scrolls before React virtualizes them away.
    """
    clean_url = group_url.strip().rstrip('/')
    cookie_list, cookie_header = _parse_fb_cookies()
    posts = []
    seen_texts = set()

    # 1. Playwright Headless with injected session cookies
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )

            if cookie_list:
                try:
                    context.add_cookies(cookie_list)
                except Exception as ce:
                    print(f"[FB Cookies] Note adding cookies: {ce}")

            page = context.new_page()
            page.goto(clean_url, timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # Incremental scrolls: grab posts as they appear in the DOM
            for _ in range(4):
                if len(posts) >= limit:
                    break

                feed_posts = page.query_selector_all('div[role="feed"] div[role="article"], div[role="article"], div[data-ad-preview="message"]')
                for f_post in feed_posts:
                    if len(posts) >= limit:
                        break
                    try:
                        txt = f_post.inner_text().strip()
                    except Exception:
                        continue

                    if len(txt) > 30 and txt not in seen_texts:
                        seen_texts.add(txt)
                        img_tag = f_post.query_selector('img[src*="scontent"], img')
                        img_src = img_tag.get_attribute("src") if img_tag else ""
                        link_tag = f_post.query_selector('a[href*="/posts/"], a[href*="/permalink/"]')
                        p_href = link_tag.get_attribute("href") if link_tag else clean_url

                        # Author name extraction
                        author_el = f_post.query_selector('h2, h3, strong, a[role="link"]')
                        author = author_el.inner_text().strip() if author_el else "Facebook User"
                        if '\n' in author:
                            author = author.split('\n')[0].strip()

                        pid = f"fb_{abs(hash(txt[:80]))}"
                        posts.append({
                            "post_id": pid,
                            "author_name": author or "Facebook User",
                            "post_url": p_href if p_href.startswith("http") else f"https://facebook.com{p_href}",
                            "content": txt,
                            "image_url": img_src or ""
                        })

                # Scroll down
                page.evaluate("window.scrollBy(0, 1000)")
                page.wait_for_timeout(1500)

            browser.close()
    except Exception as pe:
        print(f"[FB Playwright] Playwright scrape warning: {pe}")

    # 2. HTTP Fallback (in case Playwright fails)
    if len(posts) == 0:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            if cookie_header:
                headers["Cookie"] = cookie_header

            m_url = re.sub(r'https?://(?:www\.)?facebook\.com', 'https://mbasic.facebook.com', clean_url)
            r = requests.get(m_url, headers=headers, timeout=10)
            if r.status_code == 200 and len(r.text) > 1000 and "<title>Error</title>" not in r.text:
                soup = BeautifulSoup(r.text, "html.parser")
                articles = soup.find_all(["article", "div"], role="article")
                for art in articles[:limit]:
                    text = art.get_text(separator=" ").strip()
                    if len(text) > 25:
                        author_el = art.find(["h3", "strong", "a"])
                        author = author_el.get_text().strip() if author_el else "Facebook User"
                        link_el = art.find("a", href=re.compile(r"/story\.php|/posts/|/permalink/"))
                        p_url = ("https://facebook.com" + link_el["href"]) if link_el else clean_url
                        img_el = art.find("img")
                        img_url = img_el.get("src", "") if img_el else ""

                        pid = f"fb_{abs(hash(text[:80]))}"
                        posts.append({
                            "post_id": pid,
                            "author_name": author,
                            "post_url": p_url,
                            "content": text,
                            "image_url": img_url
                        })
        except Exception as e:
            print(f"[FB Scraper] HTTP fallback warning for {group_url}: {e}")

    return posts


# ── Processing & Alert Pipeline ──────────────────────────────
def process_single_fb_group(group: Dict[str, Any]) -> int:
    """Scrapes, classifies, and sends alerts for one group."""
    gid = group["id"]
    gname = group["name"]
    gurl = group["url"]

    posts = scrape_facebook_group_posts(gurl, limit=12)
    update_fb_group_scan_stats(gid, len(posts))

    new_jobs_count = 0
    for p in posts:
        pid = p["post_id"]
        # Skip seen posts
        if is_fb_post_seen(pid):
            continue

        # Classify with AI
        ai_res = classify_fb_post_with_ai(p["content"], p["author_name"], gname)

        if ai_res.get("is_hiring"):
            alert_data = {
                "group_id": gid,
                "group_name": gname,
                "post_id": pid,
                "author_name": p["author_name"],
                "post_url": p["post_url"],
                "content": p["content"],
                "image_url": p.get("image_url", ""),
                "is_hiring": 1,
                "client_name": ai_res.get("client_name", p["author_name"]),
                "job_type": ai_res.get("job_type", "Video Editor"),
                "budget": ai_res.get("budget", "Negotiable"),
                "contact_phone": ai_res.get("contact_phone", ""),
                "contact_email": ai_res.get("contact_email", ""),
                "contact_whatsapp": ai_res.get("contact_whatsapp", ""),
                "contact_telegram": ai_res.get("contact_telegram", ""),
                "confidence_score": ai_res.get("confidence_score", 95),
                "ai_summary": ai_res.get("ai_summary", p["content"][:200]),
                "telegram_sent": 0,
                "telegram_sent_at": None
            }

            # Send Instant Telegram Alert
            sent_ok = alert_fb_hiring_post(alert_data)
            if sent_ok:
                alert_data["telegram_sent"] = 1
                alert_data["telegram_sent_at"] = datetime.now().isoformat()

            insert_fb_alert(alert_data)
            new_jobs_count += 1
            print(f"[FB Radar] 🎯 NEW JOB ALERT DISPATCHED: {alert_data['job_type']} in '{gname}'!")

    return new_jobs_count


# ── Background Worker Loop ───────────────────────────────────
_FB_MONITOR_RUNNING = False
_FB_MONITOR_THREAD = None

def fb_monitor_background_worker():
    global _FB_MONITOR_RUNNING
    print("[FB Radar Worker] Background monitor started...")
    while _FB_MONITOR_RUNNING:
        try:
            groups = [g for g in get_all_fb_groups() if g.get("active") == 1]
            for g in groups:
                if not _FB_MONITOR_RUNNING:
                    break
                process_single_fb_group(g)
                time.sleep(3)  # Brief pause between groups
        except Exception as e:
            print(f"[FB Radar Worker] Error in monitor cycle: {e}")

        # Sleep for 60 seconds before next scan cycle
        for _ in range(60):
            if not _FB_MONITOR_RUNNING:
                break
            time.sleep(1)


def start_fb_monitor():
    global _FB_MONITOR_RUNNING, _FB_MONITOR_THREAD
    if _FB_MONITOR_RUNNING:
        return
    _FB_MONITOR_RUNNING = True
    _FB_MONITOR_THREAD = threading.Thread(target=fb_monitor_background_worker, daemon=True)
    _FB_MONITOR_THREAD.start()
    print("[FB Radar] Monitor service activated.")


def stop_fb_monitor():
    global _FB_MONITOR_RUNNING
    _FB_MONITOR_RUNNING = False
    print("[FB Radar] Monitor service stopped.")


# ── Instant Test Demo ─────────────────────────────────────────
def send_test_fb_hiring_alert() -> Dict[str, Any]:
    """Generates a realistic hiring post and dispatches Telegram alert."""
    test_job = {
        "group_id": None,
        "group_name": "Video Editors & Content Creators Bangladesh",
        "post_id": f"test_{int(time.time())}",
        "author_name": "Tanvir Rahman (YouTuber)",
        "client_name": "Tanvir Rahman",
        "post_url": "https://facebook.com/groups/videoeditorjobs",
        "content": "Urgent Requirement! Looking for a dedicated YouTube video editor for my Finance & Tech channel. Must know Premiere Pro, retention pacing, and sound design. Rate: $60/video ($300-$500/month for 8 videos). WhatsApp your best portfolio: +8801712345678 or email tanvir.creators@gmail.com",
        "image_url": "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?w=800&auto=format&fit=crop",
        "is_hiring": 1,
        "job_type": "YouTube Long-form (Finance & Tech)",
        "budget": "$60/video ($300-$500/month)",
        "contact_phone": "+8801712345678",
        "contact_whatsapp": "+8801712345678",
        "contact_email": "tanvir.creators@gmail.com",
        "contact_telegram": "",
        "confidence_score": 99,
        "ai_summary": "Urgent hiring for YouTube Finance channel. Budget $60/video (up to $500/mo). Requires Premiere Pro & retention editing.",
        "telegram_sent": 0,
        "telegram_sent_at": None
    }

    sent = alert_fb_hiring_post(test_job)
    if sent:
        test_job["telegram_sent"] = 1
        test_job["telegram_sent_at"] = datetime.now().isoformat()

    insert_fb_alert(test_job)
    return {"ok": True, "telegram_sent": sent, "alert": test_job}

