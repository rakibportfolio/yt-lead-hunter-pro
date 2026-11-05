#!/usr/bin/env python3
"""YouTube Channel Email Scraper via Bright Data (CLI & Automated Tool)
Ported from yaronbeen/bright-data-youtube-outreach for Zentic Media Client Hunter.

Workflow:
  Keywords CSV -> BD Videos Dataset -> Deduplicate Channels -> BD Channels Dataset -> Extract Emails -> Output CSV (& SQLite DB)

Usage:
  python bright_data_cli.py keywords.csv output_channels.csv [--save-db]
"""

import csv
import json
import os
import re
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Load environment if present
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(__file__), "backend", ".env"))
except Exception:
    pass

API_KEY = os.environ.get("BRIGHT_DATA_API_KEY", "")

VIDEOS_DATASET_ID = "gd_lk56epmy2i5g7lzu0k"   # YouTube - Videos posts
CHANNELS_DATASET_ID = "gd_lk538t2k2p1k3oos71"  # YouTube - Channels
BASE_URL = "https://api.brightdata.com/datasets/v3"

POLL_INTERVAL = 15
POLL_TIMEOUT = 1800

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

DEFAULT_KEYWORDS = [
    ("video editing tips", 60),
    ("youtube automation", 60),
    ("content creator", 60),
]


def api_request(method, url, data=None):
    if not API_KEY:
        print("ERROR: BRIGHT_DATA_API_KEY environment variable is not set.")
        sys.exit(1)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=180) as resp:
            raw = resp.read().decode()
            if not raw.strip():
                return None
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw.strip()
    except HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        print(f"  HTTP {e.code}: {body_text[:500]}")
        raise
    except URLError as e:
        print(f"  Network error: {e.reason}")
        raise


def read_keywords_csv(path):
    keywords = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header and header[0].lower().strip() not in ("keyword", "keywords"):
            num = int(header[1]) if len(header) > 1 and header[1].strip().isdigit() else 60
            keywords.append((header[0].strip(), num))
        for row in reader:
            if not row or not row[0].strip():
                continue
            kw = row[0].strip()
            num = int(row[1]) if len(row) > 1 and row[1].strip().isdigit() else 60
            keywords.append((kw, num))
    return keywords


def trigger_collection(dataset_id, inputs, discover_by=None):
    url = f"{BASE_URL}/trigger?dataset_id={dataset_id}&notify=false&include_errors=true"
    if discover_by:
        url += f"&type=discover_new&discover_by={discover_by}"
    payload = {"input": inputs}
    print(f"  Triggering collection with {len(inputs)} input(s)...")
    resp = api_request("POST", url, payload)
    if isinstance(resp, dict) and "snapshot_id" in resp:
        return resp["snapshot_id"]
    if isinstance(resp, str):
        return resp
    raise RuntimeError(f"Unexpected trigger response: {resp}")


def poll_until_ready(snapshot_id):
    url = f"{BASE_URL}/progress/{snapshot_id}"
    start = time.time()
    last_status = None
    while time.time() - start < POLL_TIMEOUT:
        try:
            resp = api_request("GET", url)
        except HTTPError:
            time.sleep(POLL_INTERVAL)
            continue

        status = resp.get("status") if isinstance(resp, dict) else str(resp)
        if status != last_status:
            elapsed = int(time.time() - start)
            print(f"  Status: {status} ({elapsed}s elapsed)")
            last_status = status

        if status == "ready":
            time.sleep(5)
            return
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"Collection failed with status: {status}. Details: {resp}")

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(f"Collection timed out after {POLL_TIMEOUT}s")


def download_snapshot(snapshot_id, retries=3):
    url = f"{BASE_URL}/snapshot/{snapshot_id}?format=json"
    for attempt in range(retries):
        print(f"  Downloading snapshot {snapshot_id} (attempt {attempt + 1}/{retries})...")
        try:
            result = api_request("GET", url)
        except Exception as e:
            print(f"  Download error: {e}")
            if attempt < retries - 1:
                time.sleep(10)
                continue
            raise

        if isinstance(result, dict) and "snapshot_id" in result:
            print(f"  Data not ready yet, retrying...")
            if attempt < retries - 1:
                time.sleep(15)
                continue
            raise RuntimeError(f"Snapshot data not available after {retries} attempts")

        if isinstance(result, list):
            return result

        print(f"  Unexpected response type: {type(result).__name__}, retrying...")
        if attempt < retries - 1:
            time.sleep(10)
            continue
        return result

    return None


def extract_emails(text):
    if not text:
        return []
    matches = EMAIL_REGEX.findall(str(text))
    # clean and deduplicate
    clean = []
    blocked = ["noreply", "no-reply", "example.com", ".png", ".jpg", ".webp", "support@youtube"]
    for m in matches:
        m_clean = m.strip().strip(".,;:()<>[]{}'\"")
        if not any(b in m_clean.lower() for b in blocked) and m_clean not in clean:
            clean.append(m_clean)
    return clean


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    save_to_db = "--save-db" in sys.argv

    input_csv = args[0] if len(args) > 0 else "keywords.csv"
    output_csv = args[1] if len(args) > 1 else "output_channels.csv"

    if not API_KEY:
        print("ERROR: Set your Bright Data API key in environment or backend/.env:")
        print("  set BRIGHT_DATA_API_KEY=your_key")
        return

    # Step 1: Read Keywords
    if input_csv and os.path.exists(input_csv):
        print(f"[1/9] Reading keywords from {input_csv}")
        keywords = read_keywords_csv(input_csv)
    else:
        print("[1/9] Using default keywords")
        keywords = DEFAULT_KEYWORDS

    print(f"  Keywords: {[k for k, _ in keywords]}")

    # Step 2: Trigger video search
    print("\n[2/9] Triggering Bright Data Videos collection...")
    video_inputs = [
        {"keyword": kw, "num_of_posts": str(num), "start_date": "", "end_date": "", "country": ""}
        for kw, num in keywords
    ]
    video_snapshot_id = trigger_collection(VIDEOS_DATASET_ID, video_inputs, discover_by="keyword")
    print(f"  Snapshot ID: {video_snapshot_id}")

    # Step 3: Wait for videos
    print("\n[3/9] Waiting for video collection to complete (this may take 2-5 minutes)...")
    poll_until_ready(video_snapshot_id)

    # Step 4: Download video results
    print("\n[4/9] Downloading video results...")
    videos = download_snapshot(video_snapshot_id)
    if not videos:
        print("  No videos returned. Exiting.")
        return
    print(f"  Got {len(videos)} video records")

    # Step 5: Deduplicate channels
    print("\n[5/9] Deduplicating channels...")
    channels_map = {}
    videos = [v for v in videos if isinstance(v, dict)]

    for v in videos:
        ch_url = v.get("channel_url", "")
        if not ch_url:
            continue

        kw = ""
        if isinstance(v.get("discovery_input"), dict):
            kw = v["discovery_input"].get("keyword", "")
        if not kw and isinstance(v.get("input"), dict):
            inp = v["input"]
            kw = inp.get("keyword", "")

        if ch_url not in channels_map:
            channels_map[ch_url] = {
                "subscribers": v.get("subscribers", ""),
                "handle": v.get("youtuber", ""),
                "keywords": set(),
            }
        if kw:
            channels_map[ch_url]["keywords"].add(kw)

    print(f"  Found {len(channels_map)} unique channels")

    if not channels_map:
        print("  No channels found. Exiting.")
        return

    # Step 6: Trigger channel scraping
    print("\n[6/9] Triggering Bright Data Channels collection...")
    channel_inputs = []
    for ch_url in channels_map:
        about_url = ch_url.rstrip("/")
        if not about_url.endswith("/about"):
            about_url += "/about"
        channel_inputs.append({"url": about_url})

    channel_snapshot_id = trigger_collection(CHANNELS_DATASET_ID, channel_inputs)
    print(f"  Snapshot ID: {channel_snapshot_id}")

    # Step 7: Wait + download channel data
    print("\n[7/9] Waiting for channel collection to complete...")
    poll_until_ready(channel_snapshot_id)

    print("  Downloading channel results...")
    channel_results = download_snapshot(channel_snapshot_id) or []
    channel_results = [ch for ch in channel_results if isinstance(ch, dict)]

    channel_data_map = {}
    for ch in channel_results:
        ch_url = ch.get("url", "")
        normalized = ch_url.rstrip("/").removesuffix("/about")
        channel_data_map[normalized] = ch
        channel_data_map[ch_url] = ch

    # Step 8: Extract emails
    print("\n[8/9] Extracting verified emails...")
    rows = []
    email_count = 0
    for ch_url, info in channels_map.items():
        normalized = ch_url.rstrip("/")
        ch_data = channel_data_map.get(normalized, {})

        description = ch_data.get("Description", "") or ch_data.get("description", "") or ""
        links = ch_data.get("Links", "") or ch_data.get("links", "") or ""
        name = ch_data.get("name", "") or ch_data.get("Name", "") or info.get("handle", "")
        subs = ch_data.get("subscribers", "") or info.get("subscribers", "")

        all_text = f"{description} {links}"
        emails = extract_emails(all_text)
        email_str = "; ".join(emails) if emails else ""
        if emails:
            email_count += len(emails)

        links_str = "; ".join(str(l) for l in links) if isinstance(links, list) else str(links)
        keywords_str = "; ".join(sorted(info["keywords"]))

        row = {
            "keyword": keywords_str,
            "channel_url": ch_url,
            "channel_name": name,
            "subscribers": str(subs),
            "description": str(description)[:500],
            "email": email_str,
            "links": links_str[:500],
        }
        rows.append(row)

    # Step 9: Write output CSV
    print(f"\n[9/9] Writing output to {output_csv}...")
    fieldnames = ["keyword", "channel_url", "channel_name", "subscribers", "description", "email", "links"]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone! {len(rows)} channels written to {output_csv}")
    print(f"  Channels with emails: {sum(1 for r in rows if r['email'])}")
    print(f"  Total unique emails: {email_count}")

    # Optional DB Sync
    if save_to_db:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
            from database import insert_lead
            saved_count = 0
            for r in rows:
                lead_data = {
                    "name": r["channel_name"] or "Creator",
                    "channel": r["channel_name"],
                    "channel_url": r["channel_url"],
                    "platform": "YouTube",
                    "subscribers": r["subscribers"],
                    "email": r["email"].split(";")[0].strip() if r["email"] else "",
                    "website": r["channel_url"],
                    "social": {},
                    "ai_score": 85 if r["email"] else 50,
                    "lead_type": "hot" if r["email"] else "warm",
                }
                insert_lead(lead_data)
                saved_count += 1
            print(f"  Successfully saved {saved_count} leads to SQLite database!")
        except Exception as e:
            print(f"  Could not save to SQLite: {e}")


if __name__ == "__main__":
    main()

