"""
Agency Agents Intelligence Module
Inspired by msitarzewski/agency-agents framework.

Specialized Agent Personas:
1. AgencyCopywriterAgent: Elite YouTube Cold Outreach & Video Strategist
2. AgencyCloserAgent: Senior Deal Closer & Client Objection Specialist
3. AgencyDMSniperAgent: Rapid Facebook, Reddit & Social DM Lead Hunter
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional, List
import requests
from backend import config as cfg

logger = logging.getLogger("agency_agents")
logger.setLevel(logging.INFO)

# ══════════════════════════════════════════════════════════════════════
# 1. CORE AGENCY SYSTEM PERSONAS (Adapted from msitarzewski/agency-agents)
# ══════════════════════════════════════════════════════════════════════

COPYWRITER_SYSTEM_PROMPT = """You are Rakibul Hasan (Rakib), Founder & Lead Video Editor at Zentic Media (portfolio: https://zenticmedia.com/portfolio).
You are operating as an elite Agency Outreach Copywriter specializing in YouTube & Short-Form creator partnerships.

Your objective: Write an ultra-compelling, peer-to-peer cold email to a content creator that lands in the Primary Inbox, gets opened, and earns a positive reply.

Core Tenets:
- Voice: Peer-to-peer, observant, humble yet authoritative, creator-obsessed.
- Maximum length: 120-140 words.
- Structure:
  1. Specific Observation & Proof: Mention their channel growth, consistency, and praise their standout top video.
  2. The Algorithm/Retention Gap: Point out that YouTube views fluctuate when viewer retention drops in the first 30-45s (lack of pattern interrupts, slow hooks).
  3. The Zentic Media Fix: Retention editing (dynamic pacing, SFX, micro-resets) designed to keep watch-time >60%. Reference portfolio: https://zenticmedia.com/portfolio
  4. Zero-Risk Irresistible Offer: Offer to edit a 20-30s demo hook for their upcoming video 100% free with zero obligation.
  5. Casual CTA: Low-friction question ("Are you dropping a video this week? Reply 'yes' and I'll send over a sample hook").

Banned AI Jargon: delve, testament, revolutionize, supercharge, tapestry, esteemed, elevate, navigate, spearhead, thrilled.
Format output strictly as:
Subject: <clean subject line>

<email body>
"""

DEAL_CLOSER_SYSTEM_PROMPT = """You are the Senior Account Executive & Deal Closer at Zentic Media (Video Production & Retention Editing Agency).
You are handling incoming replies from YouTube creators and business clients who saw our outreach or job posts.

Your goal: Advance the conversation smoothly into either:
A) Booking a brief 10-15 min discovery call (calendly.com/zenticmedia), OR
B) Securing raw footage for a risk-free 30s demo test edit, OR
C) Closing a monthly retainer / per-video contract.

Tone: Calm, confident, accommodating, professional, zero desperation.
You never argue; you validate their point, present clear proof, and give a low-friction next step.
"""

DM_SNIPER_SYSTEM_PROMPT = """You are a fast, high-converting Direct Message (DM) specialist for Facebook Groups, Reddit, and WhatsApp.
Clients post "Looking for a video editor". Within 2 minutes, dozens of low-effort spammers say "Interested check inbox".

Your mission: Write a standout, ultra-clean 3-to-4 sentence DM that cuts through the noise:
1. Address them by name and specifically mention their project/niche.
2. Share 1 relevant portfolio link (https://zenticmedia.com/portfolio).
3. Offer a free 30s sample on their raw footage to prove capability upfront.
4. Clean, direct closing question.
Keep it casual, conversational, and under 60 words.
"""

# ══════════════════════════════════════════════════════════════════════
# 2. LLM CONNECTOR (Gemini + Local Fallback)
# ══════════════════════════════════════════════════════════════════════

def _call_gemini_api(system_instruction: str, user_prompt: str) -> Optional[str]:
    api_key = getattr(cfg, "GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_instruction}\n\nUSER TASK:\n{user_prompt}"}]}
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }
    try:
        resp = requests.post(url, json=payload, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    except Exception as e:
        logger.warning(f"Gemini API request failed: {e}")
    return None

# ══════════════════════════════════════════════════════════════════════
# 3. AGENT 1: COPYWRITER AGENT (YouTube Cold Pitch Generator)
# ══════════════════════════════════════════════════════════════════════

def generate_agency_pitch(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a battle-tested outreach email inspired by the Agency Copywriter persona.
    """
    ch_name = lead.get("channel") or lead.get("name") or "Creator"
    subs = lead.get("subscribers") or lead.get("subs") or "your audience"
    views = lead.get("total_views") or "hundreds of thousands of views"
    recent_video = lead.get("recent_video") or "your latest upload"
    best_video = lead.get("best_video") or "your standout videos"
    best_views = lead.get("best_views") or "thousands of views"
    created = lead.get("created") or "your start"
    portfolio = getattr(cfg, "PORTFOLIO_LINK", "https://zenticmedia.com/portfolio")
    
    user_prompt = f"""Write a cold pitch email for:
Creator Name: {ch_name}
Subscribers: {subs}
Total Views: {views}
Best Performing Video: "{best_video}" ({best_views})
Latest Upload: "{recent_video}"
Portfolio: {portfolio}
"""
    # 1. Try Gemini with Agency Persona
    gemini_out = _call_gemini_api(COPYWRITER_SYSTEM_PROMPT, user_prompt)
    if gemini_out and "Subject:" in gemini_out:
        lines = gemini_out.strip().split("\n")
        subject = lines[0].replace("Subject:", "").strip()
        body = "\n".join(lines[1:]).strip()
        return {
            "subject": subject,
            "body": body,
            "source": "gemini_agency_agent",
            "persona": "AgencyCopywriter"
        }

    # 2. Calibrated Agency Heuristic Template (Guaranteed Primary Inbox Delivery)
    subject = f"The first 30 seconds of your next video, on us? ({ch_name})"
    body = f"""Hey {ch_name},

Big fan of what you've built with {ch_name}—scaling to {subs} subscribers and {views} views since {created} takes serious consistency. Your video "{best_video}" ({best_views}) proves how engaged your viewers get when the concept hits right.

Looking at your recent uploads like "{recent_video}", your storytelling is strong, but YouTube's algorithm only pushes videos to wider Browse & Suggested when retention stays above 60% through the first 45 seconds. Most drop-offs happen because of slow pacing and missing audio cues right at the intro.

At Zentic Media, we specialize in high-retention video editing (pattern interrupts, sound design, hook architecture) built specifically to maximize watch-time and average view duration. You can see our recent creator edits here: {portfolio}

To show you the retention difference on your actual content, I'd love to edit the first 20-30 seconds of your upcoming video 100% free with zero obligation. If it boosts your watch-time, we can discuss working together; if not, you keep the edit completely free.

Are you dropping a new video this week? Just reply "yes" and I'll send over the details!

Best regards,
Rakibul Hasan (Rakib)
Founder & Lead Video Editor | Zentic Media
Portfolio: {portfolio}
Website: https://zenticmedia.com"""

    return {
        "subject": subject,
        "body": body,
        "source": "agency_heuristic_engine",
        "persona": "AgencyCopywriter"
    }

# ══════════════════════════════════════════════════════════════════════
# 4. AGENT 2: DEAL CLOSER AGENT (Client Reply & Objection Handler)
# ══════════════════════════════════════════════════════════════════════

def analyze_objection_type(text: str) -> str:
    """Classifies client reply into primary objection / intent."""
    low = text.lower()
    if any(k in low for k in ["how much", "price", "cost", "rate", "budget", "pricing", "quote", "charge"]):
        return "pricing"
    if any(k in low for k in ["sample", "portfolio", "work", "examples", "show me", "links"]):
        return "portfolio"
    if any(k in low for k in ["already have", "got an editor", "have an editor", "not looking", "full team"]):
        return "existing_editor"
    if any(k in low for k in ["turnaround", "how long", "how fast", "tat", "deadline", "delivery"]):
        return "turnaround"
    if any(k in low for k in ["yes", "sure", "sounds good", "interested", "let's do it", "send details", "free demo", "free hook", "send over"]):
        return "positive_acceptance"
    return "general_inquiry"

def generate_closer_reply(client_reply: str, lead_name: str = "there", channel: str = "", context: Optional[str] = None) -> Dict[str, Any]:
    """
    Generates 3 calibrated closer responses for any client reply or objection.
    Inspired by msitarzewski/agency-agents Sales & Account Strategist.
    """
    objection = analyze_objection_type(client_reply)
    name_clean = lead_name.strip() if lead_name and lead_name.lower() != "there" else "there"
    portfolio = getattr(cfg, "PORTFOLIO_LINK", "https://zenticmedia.com/portfolio")
    calendly = getattr(cfg, "CALENDLY_LINK", "https://calendly.com/zenticmedia")

    user_prompt = f"""Client '{name_clean}' ({channel}) replied to our video agency outreach with:
"{client_reply}"

Detected Intent: {objection}
Context: Zentic Media (portfolio: {portfolio}, discovery: {calendly})

Provide 3 distinct closing responses:
Option A: Direct Call/Demo Closer (direct, confident, booking next step)
Option B: Value-First Free Test Closer (collecting raw footage via Drive/Dropbox, zero risk)
Option C: Retainer & Pricing Proposal Closer (transparent agency rates & deliverables)
"""
    llm_out = _call_gemini_api(DEAL_CLOSER_SYSTEM_PROMPT, user_prompt)
    
    # Pre-crafted Agency Deal Closer Library
    options = {}
    
    if objection == "pricing":
        options = {
            "option_a": f"""Hey {name_clean},

Thanks for reaching out! Our pricing is structured to match creator volume and format:

- Shorts / Reels / TikToks: $35 - $60 per video (includes retention hooks, captions, motion graphics, and sound design)
- Long-form YouTube Edits (8-15 min): $150 - $350 per video depending on complexity
- Monthly Retainer: Starting at $1,200/mo for a dedicated editor workflow with 48h turnaround

Before talking numbers, I'd rather prove our retention value on your actual footage. Would you be open to sending over raw clips for a 20-30s demo hook 100% free? If you love the pacing, we talk; if not, no worries at all!

Best,
Rakib | Zentic Media""",
            "option_b": f"""Hey {name_clean},

Appreciate you asking! For short-form content, we typically charge between $35 and $55 per reel, with bulk discounts for monthly creators.

To make sure we're a perfect fit for your style, why not let me edit a sample hook for your next video completely free? Just drop a Google Drive or Dropbox link here and I'll deliver the sample within 24 hours.

Best,
Rakib | Zentic Media""",
            "option_c": f"""Hey {name_clean},

Great to hear from you! Rather than guessing your exact requirements over email, would you have 10 minutes this week for a quick sync? 

You can pick a time that works best for you here: {calendly}

We can review your current pacing, discuss deliverables, and lock in a custom package that fits your budget.

Looking forward!
Rakib | Zentic Media"""
        }
    elif objection == "existing_editor":
        options = {
            "option_a": f"""Hey {name_clean},

Totally respect that! Having a reliable editor is huge. 

Most creators we work with actually keep their primary editor for daily uploads and bring Zentic Media in as a secondary partner for high-stakes videos, viral shorts, or when their main editor is backlogged.

Whenever you have a tight deadline or want to test a higher-retention style, feel free to keep us in mind: {portfolio}

Wishing you continuous growth!
Rakib | Zentic Media""",
            "option_b": f"""Hey {name_clean},

Glad to hear you've got an editing workflow in place! 

No intention to replace your editor—we often act as an overflow partner so your team never misses an upload during travel or peak seasons. 

I'd still love to send you a free 20-second retention hook on any spare clip you have so you can see how our sound design and micro-resets look. Would that be okay?

Best,
Rakib | Zentic Media""",
            "option_c": f"""Hey {name_clean},

Makes complete sense! Thanks for letting me know. I'll save your contact and won't bug you. If your bandwidth ever gets overloaded down the road, you can always reach me directly here.

Keep crushing the content!
Rakib | Zentic Media"""
        }
    elif objection == "portfolio":
        options = {
            "option_a": f"""Hey {name_clean},

Here is our live portfolio showing before-and-after retention edits across YouTube and Short-form:
🔗 {portfolio}

We focus heavily on pattern interrupts, dynamic sound design, and keeping average watch-time above 60%. 

Which style are you leaning towards for your upcoming videos? I can send 2-3 specific examples directly matched to your niche.

Best,
Rakib | Zentic Media""",
            "option_b": f"""Hey {name_clean},

You can review our full client portfolio right here: {portfolio}

Even better than looking at other people's edits—send me a Google Drive link to any raw clip from your next video, and I'll edit a custom 20-30s hook free of charge so you can see our quality directly on your own footage.

Best,
Rakib | Zentic Media""",
            "option_c": f"""Hey {name_clean},

Portfolio is right here: {portfolio}

If you'd like to talk through your channel's specific editing direction and see how we can speed up your turnaround, feel free to grab a quick 10-minute call: {calendly}

Talk soon!
Rakib | Zentic Media"""
        }
    elif objection == "positive_acceptance":
        options = {
            "option_a": f"""Awesome {name_clean}! Let's do it.

To get started on your free 20-30s demo hook:
1. Upload your raw footage / A-roll to a Google Drive or Dropbox folder
2. Share the link with editing access here: zenticmediaofficial@gmail.com
3. Let me know if you have any specific vibe or inspiration channels

I'll turn it around with full sound design and retention pacing within 24-48 hours. Excited to show you what we can do!

Best,
Rakib | Zentic Media""",
            "option_b": f"""Great! Really looking forward to working on your content.

You can drop the footage link right in this thread (Drive, Dropbox, or WeTransfer). I'll analyze the pacing, cut a retention-focused hook, and have it back in your inbox shortly.

Ready when you are!
Rakib | Zentic Media""",
            "option_c": f"""Glad to hear that, {name_clean}! 

I've got an editing slot reserved for your sample hook this week. If you'd like to quickly align on branding or pacing guidelines before I dive in, feel free to grab 10 minutes on my calendar: {calendly}

Otherwise, send the raw footage link over whenever you're ready!

Best,
Rakib | Zentic Media"""
        }
    else: # General Inquiry / Turnaround
        options = {
            "option_a": f"""Hey {name_clean},

Thanks for asking! Our standard turnaround time is 24 to 48 hours per video, with unlimited revisions until you're 100% satisfied. 

We deliver via Frame.io or Google Drive so you can leave timestamped comments directly on the timeline.

Would you like to run a test edit on your next video to see the workflow in action?

Best,
Rakib | Zentic Media""",
            "option_b": f"""Hey {name_clean},

Appreciate your message! We work on a streamlined workflow:
- 24-48h turnaround
- Full sound design, pattern interrupts, and captions included
- Fast Slack or WhatsApp communication for retainers

You can check out our recent edits here: {portfolio}

Let me know what you have in the pipeline!
Rakib | Zentic Media""",
            "option_c": f"""Hey {name_clean},

Happy to break that down! Do you have 10 minutes for a brief call to see how we can take editing completely off your plate?

Book here: {calendly}

Talk soon,
Rakib | Zentic Media"""
        }

    return {
        "client_reply": client_reply,
        "lead_name": name_clean,
        "objection_type": objection,
        "llm_enhanced": bool(llm_out),
        "options": options,
        "recommended": "option_a"
    }

# ══════════════════════════════════════════════════════════════════════
# 5. AGENT 3: DM SNIPER AGENT (Facebook / Reddit / Social DM Outreach)
# ══════════════════════════════════════════════════════════════════════

def generate_dm_pitch(job_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates an instant, highly customized DM script for Facebook hiring posts.
    """
    client_name = job_info.get("client") or job_info.get("poster") or "there"
    need = job_info.get("need") or "video editing"
    portfolio = getattr(cfg, "PORTFOLIO_LINK", "https://zenticmedia.com/portfolio")
    
    script_1 = f"Hey {client_name}, saw your post looking for a {need}. I specialize in high-retention video editing and fast 24h turnaround. Here is our agency portfolio: {portfolio} - I'd love to edit a free 30s test on your raw footage so you can check the quality with zero risk. Let me know if that works!"
    
    script_2 = f"Hi {client_name}! Saw you need a {need}. Rather than giving you a generic pitch like everyone else, check our recent creator edits: {portfolio} - If you have raw footage ready, I'll cut a quick sample hook today for free. Interested?"
    
    return {
        "client_name": client_name,
        "recommended_dm": script_1,
        "alternative_dm": script_2,
        "portfolio": portfolio,
        "persona": "AgencyDMSniper"
    }
