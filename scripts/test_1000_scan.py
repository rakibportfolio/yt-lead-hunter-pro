import sys, time
sys.path.insert(0, 'backend')
from youtube_scraper import scan_youtube

def progress(kind, *args):
    print(f"[{time.strftime('%X')}] PROGRESS: {kind} -> {args}")

t0 = time.time()
print("Starting 1000-channel scan test...")
leads = scan_youtube('motivation', max_results=1000, country='US', progress_callback=progress)
print(f"DONE: {len(leads)} leads collected in {time.time()-t0:.2f}s")
