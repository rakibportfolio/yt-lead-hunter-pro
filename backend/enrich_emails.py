import sqlite3
import requests
import re
import json
import socket
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", re.IGNORECASE)
OBFUSCATED_RE = re.compile(
    r"([a-zA-Z0-9_.+-]+)\s*(?:\[at\]|\(at\)|\sat\s|@)\s*([a-zA-Z0-9-]+)\s*(?:\[dot\]|\(dot\)|\sdot\s|\.)\s*([a-zA-Z]{2,6})",
    re.IGNORECASE
)

BLOCKED_DOMAINS = {
    "youtube.com", "google.com", "sentry.io", "wixpress.com",
    "doubleclick.net", "googletagmanager.com", "example.com",
    "schema.org", "w3.org", "gstatic.com", "ytimg.com"
}
BLOCKED_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".css", ".js")

_dns_cache = {}

def is_domain_valid(domain: str) -> bool:
    domain = domain.lower().strip()
    if domain in _dns_cache:
        return _dns_cache[domain]
    if any(b in domain for b in BLOCKED_DOMAINS) or "." not in domain:
        _dns_cache[domain] = False
        return False
    try:
        socket.gethostbyname(domain)
        _dns_cache[domain] = True
        return True
    except Exception:
        _dns_cache[domain] = False
        return False

def clean_and_verify_email(email_cand: str) -> str:
    if not email_cand:
        return ""
    email_cand = email_cand.strip().strip(".,;:()<>[]{}'\"").lower()
    if "@" not in email_cand:
        return ""
    if any(email_cand.endswith(ext) for ext in BLOCKED_EXTS):
        return ""
    domain = email_cand.split("@")[-1].strip()
    if is_domain_valid(domain):
        return email_cand
    return ""

def extract_all_emails_from_text(text: str) -> list:
    if not text:
        return []
    found = []
    # 1. Direct standard emails
    for m in EMAIL_RE.findall(text):
        verified = clean_and_verify_email(m)
        if verified and verified not in found:
            found.append(verified)

    # 2. Obfuscated emails (e.g. name [at] gmail [dot] com)
    for m in OBFUSCATED_RE.findall(text):
        cand = f"{m[0]}@{m[1]}.{m[2]}"
        verified = clean_and_verify_email(cand)
        if verified and verified not in found:
            found.append(verified)

    return found

def extract_website_from_channel_page(html_text: str) -> list:
    urls = []
    redirects = re.findall(r"q=(https?(?:%3A%2F%2F|://)[^&\"\\\s]+)", html_text)
    for q in redirects:
        try:
            decoded = urllib.parse.unquote(q)
            if not decoded.startswith("http"):
                decoded = "https://" + decoded
            dom = decoded.split("/")[2].lower()
            if not any(b in dom for b in BLOCKED_DOMAINS) and "accounts.google.com" not in decoded:
                if decoded not in urls:
                    urls.append(decoded)
        except Exception:
            continue

    raw_webs = re.findall(r"(?:https?://|www\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s\"'<>]*)?", html_text)
    for w in raw_webs:
        try:
            if not w.startswith("http"):
                w = "https://" + w
            dom = w.split("/")[2].lower()
            if not any(b in dom for b in BLOCKED_DOMAINS) and w not in urls:
                urls.append(w)
        except Exception:
            continue

    return urls

def scrape_email_from_external_site(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=3.5)
        if r.status_code == 200:
            emails = extract_all_emails_from_text(r.text)
            if emails:
                return emails[0]
            
            if "linktr.ee" not in url and "beacons.ai" not in url:
                base_site = "/".join(url.split("/")[:3])
                for sub in ["/contact", "/about", "/contact-us"]:
                    try:
                        rc = requests.get(f"{base_site}{sub}", headers=HEADERS, timeout=3.0)
                        if rc.status_code == 200:
                            sub_emails = extract_all_emails_from_text(rc.text)
                            if sub_emails:
                                return sub_emails[0]
                    except Exception:
                        pass
    except Exception:
        pass
    return ""

def deep_extract_channel_email(channel_url: str, handle: str = "", description: str = "") -> dict:
    res = {"email": "", "source": "", "website": ""}

    # 1. Check existing description
    if description:
        emails = extract_all_emails_from_text(description)
        if emails:
            res["email"] = emails[0]
            res["source"] = "channel_description"
            return res

    target_url = channel_url
    if not target_url and handle:
        h = handle if handle.startswith("@") else f"@{handle}"
        target_url = f"https://www.youtube.com/{h}"

    if not target_url:
        return res

    # 2. Fetch Channel Page / About tab
    try:
        about_url = target_url.rstrip("/") + "/about"
        r = requests.get(about_url, headers=HEADERS, timeout=4.0)
        if r.status_code == 200:
            emails = extract_all_emails_from_text(r.text)
            if emails:
                res["email"] = emails[0]
                res["source"] = "youtube_about"
                return res

            ext_sites = extract_website_from_channel_page(r.text)
            if ext_sites:
                res["website"] = ext_sites[0]
                for site in ext_sites[:2]:
                    site_email = scrape_email_from_external_site(site)
                    if site_email:
                        res["email"] = site_email
                        res["source"] = f"website:{site}"
                        return res
    except Exception:
        pass

    # 3. Check Recent Videos (top 2 uploads)
    try:
        v_url = target_url.rstrip("/") + "/videos"
        rv = requests.get(v_url, headers=HEADERS, timeout=4.0)
        if rv.status_code == 200:
            video_ids = list(dict.fromkeys(re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', rv.text)))[:2]
            for vid in video_ids:
                try:
                    vp = requests.get(f"https://www.youtube.com/watch?v={vid}", headers=HEADERS, timeout=3.5)
                    if vp.status_code == 200:
                        v_emails = extract_all_emails_from_text(vp.text)
                        if v_emails:
                            res["email"] = v_emails[0]
                            res["source"] = f"recent_video:{vid}"
                            return res
                except Exception:
                    continue
    except Exception:
        pass

    return res

def enrich_single_lead(lead_tuple):
    lead_id, name, handle, channel_url, desc = lead_tuple
    res = deep_extract_channel_email(channel_url, handle, desc)
    return lead_id, name, res.get("email", ""), res.get("source", ""), res.get("website", "")

def batch_enrich_database(limit=100, workers=15):
    conn = sqlite3.connect("backend/zentic_data.db")
    c = conn.cursor()
    c.execute(
        "SELECT id, name, handle, channel_url, description FROM leads "
        "WHERE (email IS NULL OR email = '') AND channel_url IS NOT NULL AND channel_url != '' "
        f"LIMIT {limit}"
    )
    leads_to_enrich = c.fetchall()
    print(f"Found {len(leads_to_enrich)} leads to enrich (limit={limit})...", flush=True)
    if not leads_to_enrich:
        conn.close()
        return 0

    enriched_count = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(enrich_single_lead, lead): lead for lead in leads_to_enrich}
        for future in as_completed(future_map):
            lead_id, name, email, source, website = future.result()
            if email:
                enriched_count += 1
                print(f"  [+] Enriched ID {lead_id} ({name}): {email} (via {source})", flush=True)
                c.execute("UPDATE leads SET email = ? WHERE id = ?", (email, lead_id))
                conn.commit()

    conn.close()
    print(f"\n[Done] Successfully enriched {enriched_count}/{len(leads_to_enrich)} leads with real verified emails!", flush=True)
    return enriched_count

if __name__ == "__main__":
    batch_enrich_database(limit=60, workers=15)
