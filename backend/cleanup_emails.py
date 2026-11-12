import sqlite3
import socket
import sys
from concurrent.futures import ThreadPoolExecutor

def check_domain(domain):
    try:
        socket.gethostbyname(domain)
        return domain, True
    except Exception:
        return domain, False

def check_and_clean():
    conn = sqlite3.connect("backend/zentic_data.db")
    c = conn.cursor()
    c.execute("SELECT id, name, email FROM leads WHERE email IS NOT NULL AND email != ''")
    rows = c.fetchall()
    print(f"Total leads with email: {len(rows)}")

    # Collect unique domains
    unique_domains = set()
    for _, _, email in rows:
        email = email.strip()
        if "@" in email:
            domain = email.split("@")[-1].strip().lower()
            if domain and "." in domain:
                unique_domains.add(domain)

    print(f"Checking {len(unique_domains)} unique domains concurrently...")
    domain_status = {}
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = executor.map(check_domain, unique_domains)
        for domain, is_valid in results:
            domain_status[domain] = is_valid

    invalid_ids = []
    valid_count = 0

    for rid, name, email in rows:
        email = email.strip()
        domain = email.split("@")[-1].strip().lower() if "@" in email else ""
        if not domain or not domain_status.get(domain, False):
            invalid_ids.append((rid, name, email))
        else:
            valid_count += 1

    print(f"Results: {valid_count} VALID domains, {len(invalid_ids)} INVALID / NON-EXISTENT domains.")
    for item in invalid_ids[:10]:
        print(f"  Invalid ID {item[0]}: {item[1]} -> {item[2]}")

    if "--fix" in sys.argv:
        print(f"\nCleaning {len(invalid_ids)} invalid emails from database...")
        for rid, _, _ in invalid_ids:
            c.execute("UPDATE leads SET email = '' WHERE id = ?", (rid,))
        conn.commit()
        print("Success: Database cleaned! Invalid emails set to empty string.")

    conn.close()

if __name__ == "__main__":
    check_and_clean()
