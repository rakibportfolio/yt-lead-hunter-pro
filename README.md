# ⚡ Zentic Media — Video Editing Client Hunting Automation

A complete, full-stack, automated Client Hunting & Outreach Operating System built for video editing agencies and freelance editors.

---

## 🚀 Quick Start (১ ক্লিকে শুরু করুন)

1. **সার্ভার চালু করুন:**
   - ফোল্ডারে থাকা `START_SERVER.bat` ফাইলটিতে ডাবল-ক্লিক করুন।
   - অথবা টার্মিনালে রান করুন:
     ```bash
     cd backend
     python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
     ```
2. **ড্যাশবোর্ড ওপেন করুন:**
   - ব্রাউজারে যান: **[http://localhost:8000](http://localhost:8000)**
   - অথবা সরাসরি `index.html` ফাইলটি যেকোনো ব্রাউজারে ওপেন করুন।

---

## 🛠️ সিস্টেম আর্কিটেকচার (System Architecture)

```
CLINT HUNTING/
├── START_SERVER.bat        # ১ ক্লিকে ব্যাকএন্ড ও ড্যাশবোর্ড রান করার ব্যাচ ফাইল
├── index.html              # প্রিমিয়াম ডার্ক-মোড গ্লাস মরফিজম ড্যাশবোর্ড UI
├── styles.css              # ভ্যানিলা CSS ডিজাইন সিস্টেম ও মাইক্রো-অ্যানিমেশন
├── app.js                  # ক্লায়েন্ট লজিক + রিয়েল-টাইম API ইন্টিগ্রেশন
├── apps_script.gs          # Google Sheets এ অটোমেটিক আউটরিচ ইমেইল পাঠানোর Apps Script
├── keywords.csv            # বাল্ক কিওয়ার্ড দিয়ে ইউটিউব চ্যানেল খোঁজার ফাইল
├── bright_data_cli.py      # Bright Data ডেটাসেট ব্যবহার করে রিয়েল ইমেইল স্ক্র্যাপ করার সিএলআই টুল
├── test_bright_data.py     # ব্রাইট ডেটা ও ইমেইল এক্সট্রাকশন ইউনিট টেস্ট সুইট
└── backend/
    ├── .env                # API Keys ও কনফিগারেশন ফাইল (Bright Data API Key সহ)
    ├── config.py           # সেন্ট্রালাইজড সেটিংস লোডার
    ├── database.py         # SQLite ডেটাবেস লেয়ার (Leads, Emails, Campaigns, Stats)
    ├── email_engine.py     # SMTP ইমেইল সেন্ডার + ট্র্যাকিং পিক্সেল + লিঙ্ক র্যাপার
    ├── youtube_scraper.py  # ইউটিউব চ্যানেল সার্চ + Bright Data Datasets + জেমিনি এআই অ্যানালাইসিস
    ├── telegram_bot.py     # টেলিগ্রাম বটের মাধ্যমে রিয়েল-টাইম নোটিফিকেশন ও ডেইলি রিপোর্ট
    ├── main.py             # FastAPI ব্যাকএন্ড সার্ভার (REST API + Static Frontend Host)
    └── requirements.txt    # পাইথন লাইব্রেরি ডিপেনডেন্সি
```

---

## 🔑 এপিআই এবং ক্রেডেনশিয়াল সেটআপ (`backend/.env`)

সিস্টেমের পূর্ণ শক্তি ব্যবহার করতে `backend/.env` ফাইলটি নোটপ্যাডে খুলে আপনার তথ্য বসিয়ে দিন:

```env
# ১. জিমেইল সেটিংস (ইমেইল পাঠাতে ও ট্র্যাক করতে)
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_PASSWORD=xxxx xxxx xxxx xxxx     # Google Account > Security > App Password (16 digit)
DAILY_SEND_LIMIT=200
TRACKING_BASE_URL=http://localhost:8000

# ২. ইউটিউব ও এআই অ্যানালাইসিস
YOUTUBE_API_KEY=AIzaSy...              # Google Cloud Console > YouTube Data API v3
BRIGHT_DATA_API_KEY=...                # Bright Data API Key (১০০% আসল ভেরিফায়েড ইউটিউব ইমেইল পেতে)
GEMINI_API_KEY=AIzaSy...               # Google AI Studio Gemini API Key

# ৩. টেলিগ্রাম বটের রিয়েল-টাইম অ্যালার্ট
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...   # @BotFather থেকে তৈরি করা Bot Token
TELEGRAM_CHAT_ID=123456789             # আপনার Telegram Chat ID (বের করতে @userinfobot)
DAILY_REPORT_TIME=23:00                # প্রতিদিন রাত ১১টায় অটো রিপোর্ট পাঠাবে

# ৪. সোশ্যাল মিডিয়া (অপশনাল)
WHATSAPP_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_ID=your_phone_id
TWITTER_BEARER_TOKEN=your_bearer_token
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
```

> **টিপ (Demo Mode):** এপিআই কি ছাড়াও ড্যাশবোর্ডটি স্বয়ংক্রিয়ভাবে সিমুলেটেড ডেমো ডেটা দিয়ে রান করবে, ফলে কোনো কি না থাকলেও আপনি সম্পূর্ণ সিস্টেম টেস্ট করতে পারবেন।

---

## 🌟 মূল ফিচারসমূহ (Core Features)

1. **🔍 Lead Finder Engine:**
   - কি-ওয়ার্ড এবং সাবস্ক্রাইবার রেঞ্জ দিয়ে ইউটিউব ক্রিয়েটর সার্চ।
   - জেমিনি এআই দিয়ে ভিডিওর এডিটিং কোয়ালিটি, থাম্বনেইল ও কনসিস্টেন্সি অ্যানালাইসিস করে সুযোগ স্কোরিং (Hot, Warm, Cold)।
   - ডেসক্রিপশন থেকে ইমেইল ও সোশ্যাল মিডিয়া প্রোফাইল এক্সট্রাকশন।

2. **📌 Drag-and-Drop Pipeline (Kanban):**
   - New Lead ➔ Cold Email Sent ➔ Opened ➔ Replied ➔ Meeting Booked ➔ Closed Client।

3. **📧 100% Stealth Email Tracking:**
   - ইনভিজিবল `1x1` ট্র্যাকিং পিক্সেলের মাধ্যমে ইমেইল ওপেন নোটিফিকেশন।
   - লিঙ্ক ট্র্যাকিং ও অটো রিডাইরেক্ট।
   - আনসাবস্ক্রাইব হ্যান্ডলার।

4. **✈️ Telegram Instant Alerts & Daily Summary:**
   - কেউ ইমেইল ৩ বার ওপেন করলে সাথে সাথে টেলিগ্রামে ফায়ার অ্যালার্ট: *"They opened it 3 times — CALL THEM NOW!"*
   - প্রতিদিন রাতে অটোমেটিক সম্পূর্ণ দিনের কাজের সামারি (কতগুলো লিড পাওয়া গেল, কতগুলো মেইল সেন্ট হলো, ওপেন রেট কত ইত্যাদি)।

5. **💬 Multi-Channel Outreach:**
   - একই ড্যাশবোর্ড থেকে Email, WhatsApp, LinkedIn এবং Twitter/X এ মেসেজ পাঠানো ও লগ রাখা।
