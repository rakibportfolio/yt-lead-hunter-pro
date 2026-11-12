# ============================================================
# ZENTIC MEDIA — MULTI-PLATFORM GLOBAL CLIENT HUNTER
# Reddit + RemoteOK + Global Video Editor Jobs + AI Pitch Engine
# ============================================================

import os
import sys
import time
import re
import json
import requests
from datetime import datetime
from typing import List, Dict, Any

# Ensure backend directory is in path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from config import cfg
from database import get_db, insert_fb_alert, is_fb_post_seen
from fb_group_monitor import classify_fb_post_with_ai, is_post_fresh
from telegram_bot import send_telegram

# ── Reddit Subreddits where Creators Hire Video Editors ─────
DEFAULT_SUBREDDITS = [
    "CreatorServices",
    "forhire",
    "VideoEditing",
    "freelance_forhire"
]

def scrape_reddit_subreddits(subreddits: List[str] = None, max_posts_per_sub: int = 15) -> List[Dict[str, Any]]:
    """
    Scrapes fresh hiring posts from creator subreddits using Playwright.
    Returns list of parsed job candidates.
    """
    if subreddits is None:
        subreddits = DEFAULT_SUBREDDITS

    found_posts = []
    seen_urls = set()

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            for sub in subreddits:
                url = f"https://www.reddit.com/r/{sub}/new/"
                print(f"[Reddit Hunter] Scanning r/{sub} ({url})...")
                try:
                    page.goto(url, timeout=25000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2500)

                    posts = page.query_selector_all("shreddit-post")
                    print(f" -> Found {len(posts)} elements in r/{sub}")

                    for post_el in posts[:max_posts_per_sub]:
                        try:
                            title = (post_el.get_attribute("post-title") or "").strip()
                            author = (post_el.get_attribute("author") or "").strip()
                            permalink = (post_el.get_attribute("permalink") or "").strip()

                            if not title or not permalink:
                                continue

                            post_url = f"https://www.reddit.com{permalink}"
                            if post_url in seen_urls:
                                continue
                            seen_urls.add(post_url)

                            # Extract body text snippet if available
                            body_text = title
                            try:
                                body_div = post_el.query_selector("div[slot='text-body'], p")
                                if body_div:
                                    t = body_div.inner_text().strip()
                                    if t and len(t) > len(body_text):
                                        body_text = f"{title}\n\n{t}"
                            except Exception:
                                pass

                            found_posts.append({
                                "platform": "reddit",
                                "subreddit": f"r/{sub}",
                                "group_name": f"r/{sub}",
                                "title": title,
                                "content": body_text,
                                "author_name": author or "Reddit User",
                                "author_url": f"https://www.reddit.com/user/{author}" if author else "",
                                "post_url": post_url,
                                "created_at": datetime.now().isoformat()
                            })
                        except Exception as pe:
                            continue

                except Exception as se:
                    print(f"[Reddit Hunter] Warning scanning r/{sub}: {se}")
                
                # Small polite delay between subreddits
                time.sleep(2)

            browser.close()
    except Exception as e:
        print(f"[Reddit Hunter] Playwright launcher note: {e}")

    return found_posts


def scrape_remoteok_video_jobs(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetches real-time remote video editing jobs from RemoteOK public API.
    """
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    url = "https://remoteok.com/api?tag=video"
    print(f"[RemoteOK] Fetching remote video jobs from {url}...")
    try:
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            data = r.json()
            # First item in RemoteOK JSON is legal disclaimer, rest are jobs
            job_items = [d for d in data if isinstance(d, dict) and "position" in d]
            for item in job_items[:limit]:
                pos = item.get("position", "")
                company = item.get("company", "Company")
                apply_url = item.get("url", "")
                tags = item.get("tags", [])
                desc = item.get("description", "")
                # Clean HTML tags from description
                clean_desc = re.sub(r'<[^>]+>', ' ', desc)[:600].strip()
                
                # Filter specifically for video/creative editor jobs
                pos_lower = pos.lower()
                desc_lower = clean_desc.lower()
                if any(k in pos_lower or k in desc_lower for k in ["video", "editor", "motion", "reels", "animat", "premiere", "after effects"]):
                    jobs.append({
                        "platform": "remoteok",
                        "group_name": f"RemoteOK: {company}",
                        "title": pos,
                        "content": f"{pos} at {company}\nTags: {', '.join(tags)}\n\n{clean_desc}",
                        "author_name": company,
                        "author_url": f"https://remoteok.com/company/{company.lower().replace(' ', '-')}",
                        "post_url": apply_url,
                        "budget": item.get("salary", "Negotiable (USD)"),
                        "created_at": datetime.now().isoformat()
                    })
            print(f"[RemoteOK] Successfully found {len(jobs)} video editor opportunities.")
    except Exception as e:
        print(f"[RemoteOK] Warning fetching RemoteOK jobs: {e}")

    return jobs


def alert_international_job(job: dict) -> bool:
    """
    Sends structured Telegram alert for Reddit or RemoteOK jobs.
    """
    platform = job.get("platform", "global").title()
    group_name = job.get("group_name", "International Community")
    author_name = job.get("author_name", "Client")
    author_url = job.get("author_url", "")
    post_url = job.get("post_url", "")
    title = job.get("title", "Video Editor Wanted")
    content = job.get("content", "")[:350]
    budget = job.get("budget", "Negotiable (USD)")
    job_type = job.get("job_type", "Video Editor")

    badge = "🔴 <b>[REDDIT HIRING]</b>" if platform.lower() == "reddit" else "🟢 <b>[REMOTE JOB]</b>"

    caption = f"""{badge} 🎯 <b>HIGH-TICKET CLIENT LEAD!</b>
━━━━━━━━━━━━━━━━━━━━
🌐 <b>Platform:</b> {platform} ({group_name})
👤 <b>Poster / Client:</b> {author_name}
"""
    if author_url:
        caption += f"👤 <b>Client Profile / DM:</b> <a href='{author_url}'>Click to Contact Poster</a>\n"
    if post_url:
        caption += f"🔗 <b>Direct Link:</b> <a href='{post_url}'>Open Job Details</a>\n"

    caption += f"""💼 <b>Role:</b> {job_type}
💰 <b>Budget / Pay:</b> {budget}

📋 <b>Description:</b>
<i>"{content}"</i>
━━━━━━━━━━━━━━━━━━━━
⚡ <b>Apply fast before other international editors!</b>"""

    # Telegram buttons
    inline_keyboard = []
    btn_row = []
    if author_url:
        btn_label = "💬 Message on Reddit" if platform.lower() == "reddit" else "🏢 Company Profile"
        btn_row.append({"text": btn_label, "url": author_url})
    if post_url:
        btn_row.append({"text": "🔗 View Exact Job", "url": post_url})
    if btn_row:
        inline_keyboard.append(btn_row)

    url = f"https://api.telegram.org/bot{cfg.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": cfg.TELEGRAM_CHAT_ID,
        "text": caption,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    if inline_keyboard:
        payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

    try:
        r = requests.post(url, json=payload, timeout=12)
        return r.status_code == 200
    except Exception as e:
        print(f"[Telegram] Error sending international alert: {e}")
        return False


def run_multi_platform_hunter() -> dict:
    """
    Main runner: scrapes Reddit + RemoteOK, filters hiring posts,
    stores them into database and triggers Telegram notifications!
    """
    print("=" * 60)
    print("🚀 RUNNING MULTI-PLATFORM GLOBAL CLIENT HUNTER")
    print("=" * 60)

    total_scraped = 0
    total_saved = 0
    total_hiring = 0

    # 1. Scrape Reddit
    reddit_posts = scrape_reddit_subreddits(max_posts_per_sub=12)
    total_scraped += len(reddit_posts)

    # 2. Scrape RemoteOK
    remote_posts = scrape_remoteok_video_jobs(limit=15)
    total_scraped += len(remote_posts)

    all_items = reddit_posts + remote_posts

    for p in all_items:
        p_url = p["post_url"]
        content = p["content"]
        auth_name = p["author_name"]
        grp = p["group_name"]
        plat = p["platform"]

        # De-duplication check
        if is_fb_post_seen("", content, p_url):
            continue

        # AI Classification & intent check
        ai_res = classify_fb_post_with_ai(content, auth_name, grp)
        is_h = 1 if ai_res.get("is_hiring") else 0

        # RemoteOK video jobs are always verified hiring jobs
        if plat == "remoteok":
            is_h = 1

        alert_data = {
            "group_id": None,
            "group_name": grp,
            "post_id": "",
            "author_name": auth_name,
            "author_url": p.get("author_url", ""),
            "post_url": p_url,
            "content": content,
            "image_url": "",
            "is_hiring": is_h,
            "client_name": auth_name,
            "job_type": ai_res.get("job_type", "Video Editor"),
            "budget": p.get("budget") or ai_res.get("budget", "Negotiable (USD)"),
            "contact_phone": "",
            "contact_email": "",
            "contact_whatsapp": "",
            "contact_telegram": "",
            "confidence_score": 95 if is_h else 20,
            "ai_summary": content[:220] + "...",
            "telegram_sent": 0,
            "telegram_sent_at": None,
            "platform": plat
        }

        if is_h:
            sent_ok = alert_international_job(alert_data)
            if sent_ok:
                alert_data["telegram_sent"] = 1
                alert_data["telegram_sent_at"] = datetime.now().isoformat()
            total_hiring += 1
            print(f"  🎯 [NEW {plat.upper()} HIRING LEAD]: {alert_data['job_type']} - {grp} (Telegram: {sent_ok})")
        else:
            print(f"  💬 Community post saved: {grp} - {auth_name}")

        insert_fb_alert(alert_data)
        total_saved += 1

    print("=" * 60)
    print(f"✅ MULTI-PLATFORM SCAN FINISHED!")
    print(f"Scraped: {total_scraped} | Saved: {total_saved} | Hiring Alerts Sent: {total_hiring}")
    print("=" * 60)

    return {
        "scraped": total_scraped,
        "saved": total_saved,
        "hiring": total_hiring
    }


# ── 1-Click AI Pitch Generator ──────────────────────────────
def generate_ai_pitch(job_content: str, client_name: str = "Client", job_type: str = "Video Editor", portfolio_url: str = "") -> str:
    """
    Generates a personalized, high-converting cold pitch tailored to the specific client's job.
    """
    p_url = portfolio_url or "https://zenticmedia.com/portfolio"
    port_text = f"\n\nHere is a quick link to my portfolio & recent projects: {p_url}"

    # Analyze style
    style = "dynamic short-form reels / TikToks" if "short" in job_content.lower() or "reel" in job_content.lower() else "high-retention YouTube long-form video editing"

    pitch = f"""Hey {client_name},

I saw your post regarding the need for a {job_type}. I specialize in {style} designed to maximize audience retention, viewer watch-time, and engagement.

What I bring to your project:
• Fast 24-48h turnaround time with seamless communication
• Retention-focused editing: dynamic pacing, sound design, clean B-rolls, and engaging motion captions
• Color grading & audio mastering for a crisp, broadcast-quality final render{port_text}

Would you be open to a quick 2-minute test edit or chatting over a few sample clips to see if my style matches your vision?

Best regards,
Rakibul Hasan (Rakib)
Founder & Lead Video Editor | Zentic Media
Portfolio: {p_url}
Website: https://zenticmedia.com"""

    return pitch.strip()

if __name__ == "__main__":
    run_multi_platform_hunter()

