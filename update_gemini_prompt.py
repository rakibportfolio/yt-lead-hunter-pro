with open(r'd:\Ads Power And All akhane ase may mas\CLINT HUNTING\backend\fb_group_monitor.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_prompt = """            prompt = f\"\"\"You are an elite AI recruiting intelligence system for Video Editing agencies.
Your task is to analyze a Facebook group post and strictly determine:
Is this person HIRING / LOOKING TO EMPLOY a video editor?
Or are they an EDITOR / FREELANCER offering their own services / looking for work?

STRICT RULES:
1. If the author is offering their own editing services ("I am a video editor", "Hire me", "Portfolio link", "DM me for editing", "Am I eligible to edit for you", "Special discount on editing") -> is_hiring MUST be FALSE.
2. If the author is LOOKING TO HIRE, RECRUIT, or CONTRACT a video editor ("Need video editor", "Hiring video editor for YouTube/Reels", "Looking for someone to edit videos", "Video editor lagbe", "Job opportunity for editors") -> is_hiring MUST be TRUE.

POST CONTENT:
\\\"\\\"\\\"{content}\\\"\\\"\\\"

AUTHOR: {author_name}
GROUP: {group_name}

Respond ONLY with valid JSON in this exact structure:
{{
  "is_hiring": true,
  "confidence_score": 98,
  "client_name": "...",
  "job_type": "YouTube Long-form / Shorts / Reels / Gaming / Documentary / General",
  "budget": "$50/video or 25,000 BDT or Negotiable or Not specified",
  "contact_phone": "+8801... or phone number found",
  "contact_whatsapp": "whatsapp number or link",
  "contact_email": "email found or empty",
  "contact_telegram": "telegram handle or empty",
  "ai_summary": "Crisp 1-2 sentence English or Bengali summary of what they need"
}}
\"\"\""""

new_prompt = """            prompt = f\"\"\"You are an elite AI recruiting intelligence engine specifically built for Video Editing agencies and Freelancers.
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
\\\"\\\"\\\"{content}\\\"\\\"\\\"

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
\"\"\""""

if old_prompt in text:
    text = text.replace(old_prompt, new_prompt)
    with open(r'd:\Ads Power And All akhane ase may mas\CLINT HUNTING\backend\fb_group_monitor.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Gemini prompt updated with comprehensive nuances!")
else:
    print("Prompt pattern not matched directly, checking...")

