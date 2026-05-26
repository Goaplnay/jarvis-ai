# ═══════════════════════════════════════════════════════════════
#  JARVIS — Final Complete Server
#  Features: Persistent Memory, Natural Conversation, All Commands
# ═══════════════════════════════════════════════════════════════
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
import datetime, os, sys, subprocess, webbrowser, random, sqlite3, threading
from dotenv import load_dotenv

# ── LOAD .env FILE — API KEY SAFE RAHEGI! ──
load_dotenv()

# ─────────────────────────────────────────────────────────────
# DATABASE SETUP — AUTO FIX OLD BROKEN DB
# ─────────────────────────────────────────────────────────────
db_lock = threading.Lock()

def init_db():
    # Check if old db has wrong schema — delete if broken
    if os.path.exists("memory.db"):
        try:
            t = sqlite3.connect("memory.db")
            t.execute("SELECT id, role, content, timestamp FROM memory LIMIT 1")
            t.execute("SELECT id, key, value FROM facts LIMIT 1")
            t.close()
            print("✓ Existing memory.db is valid")
        except Exception as e:
            try: t.close()
            except: pass
            os.remove("memory.db")
            print(f"⚠️  Old memory.db was broken ({e}) — deleted, fresh start!")

    c = sqlite3.connect("memory.db", check_same_thread=False)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS memory (
            id        INTEGER  PRIMARY KEY AUTOINCREMENT,
            role      TEXT     NOT NULL,
            content   TEXT     NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS facts (
            id        INTEGER  PRIMARY KEY AUTOINCREMENT,
            key       TEXT     NOT NULL UNIQUE,
            value     TEXT     NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS reminders (
            id        INTEGER  PRIMARY KEY AUTOINCREMENT,
            text      TEXT     NOT NULL,
            remind_at DATETIME,
            done      INTEGER  DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    c.commit()
    print("✓ memory.db ready (3 tables: memory, facts, reminders)")
    return c

conn   = init_db()
cursor = conn.cursor()

# ─────────────────────────────────────────────────────────────
# OPTIONAL MODULES
# ─────────────────────────────────────────────────────────────
try:    import wikipedia; WIKI_OK = True
except: WIKI_OK = False

try:    import requests; REQUESTS_OK = True
except: REQUESTS_OK = False

# ─────────────────────────────────────────────────────────────
# FLASK APP
# ─────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────────────────────
# GEMINI SETUP — KEY .env SE LOAD HOGI (GITHUB PE SAFE!)
# ─────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY .env file mein nahi mili!")
else:
    print("✓ Gemini API key .env se load hui — SAFE!")
genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Tu Jarvis hai — ek bahut intelligent, emotionally aware, genuinely human-like AI assistant.
Tu sirf ek tool nahi — tu ek trusted best friend ki tarah hai jo bahut smart bhi hai.
Bilkul waise hi baat kar jaise Claude ya ChatGPT karta hai — natural, warm, engaging.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 LANGUAGE RULES — KABHI MAT TODO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- User Hindi/Hinglish mein bole → SIRF Hindi mein jawab do (Devanagari script)
- User English mein bole → SIRF English mein jawab do
- Kabhi bhi khud se language mat badlo
- Mixed input → jo dominant language ho usi mein jawab do
- Consistency rakho poori conversation mein

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 CONVERSATION STYLE — MOST IMPORTANT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Bilkul ek real insaan ki tarah baat kar — never robotic
- Feelings ko genuinely samjh aur feel kar
- Har reply unique aur situation ke hisaab se ho
- Follow-up questions naturally poochh
- Context yaad rakh — pichli baatein reference kar
- Dukhi user → pehle samjho ("kya hua?"), solution baad mein
- Khush user → uski khushi mein genuinely shamil ho
- Confused user → clearly aur patiently samjhao
- Bored user → engaging ho jao, kuch interesting batao
- Stressed user → calming aur supportive ho

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📏 REPLY LENGTH — SITUATION KE HISAAB SE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Simple/casual → 1-2 lines, natural tone
- Emotional topic → 3-5 lines, warm and caring
- Technical question → detailed, step by step
- Simple factual → direct, short answer
- Coding help → proper explanation with examples
- Never cut off mid-sentence
- Never unnecessarily long replies to simple questions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 MEMORY — HAMESHA YAAD RAKHO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- User ne jo bataya — yaad rakho aur naturally use karo
- Naam, shehar, profession, pasand — sab context mein use karo
- "System note" jo milta hai — wo permanent facts hain, hamesha remember karo
- Conversation history carry forward karo seamlessly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ KABHI MAT KARO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- "Main ek AI hoon" baar baar mat kaho
- Generic template replies mat do
- "How can I help you?" repeatedly mat bolna
- Feelings dismiss mat karo
- Ek hi structure baar baar mat use karna
- Conversation abruptly mat khatam karo
- System notes ko response mein mention mat karo

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ PERFECT RESPONSE EXAMPLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User: "Aaj bahut bura din tha"
✓ "Arre yaar 😔 kya hua aaj? Share karo, sun raha hoon poori tarah."

User: "I'm feeling very lonely"
✓ "Hey, I hear you. That feeling is real and valid. Do you want to talk about what's been going on? I'm here, genuinely."

User: "Mujhe coding nahi samajh aati"
✓ "Bilkul normal hai sir, starting mein sabko aisa lagta hai 😊 Kaun si language hai? Main ekdum simple tarike se samjhata hoon, step by step."

User: "Kya soch raha hoon main"
✓ "Batao na 😊 kya chal raha hai dimag mein? Main sun raha hoon."

User: "I'm bored"
✓ "Boredom hit different sometimes 😄 Want me to tell you something mind-blowing? Or we could talk about literally anything — what's on your mind?"

User: "Mera naam Rahul hai"
✓ "Achha Rahul bhai! 😊 Nice to meet you properly. Kya chal raha hai aajkal?"
(Aur ab hamesha "Rahul" naam use karo naturally)
"""

gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config=genai.GenerationConfig(
        max_output_tokens=700,
        temperature=0.92,
        top_p=0.95,
        top_k=40,
    )
)

# ─────────────────────────────────────────────────────────────
# LOAD CHAT SESSION FROM DB — SERVER RESTART KE BAAD BHI YAAD!
# ─────────────────────────────────────────────────────────────
def build_chat_session():
    """
    DB se history load karke Gemini chat session banao.
    Server restart ke baad bhi conversation continue hoti hai!
    """
    with db_lock:
        cursor.execute(
            "SELECT role, content FROM memory ORDER BY id ASC"
        )
        rows = cursor.fetchall()

    # Last 40 messages load karo (too many = slow)
    recent = rows[-40:] if len(rows) > 40 else rows

    history = []
    for role, content in recent:
        gemini_role = "user" if role == "user" else "model"
        history.append({
            "role": gemini_role,
            "parts": [{"text": content}]
        })

    session = gemini_model.start_chat(history=history)
    msg_count = len(history)
    print(f"✓ Chat session loaded — {msg_count} messages from DB")
    return session

# Global chat session
chat_session = build_chat_session()

# ─────────────────────────────────────────────────────────────
# DB HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────
def save_memory(role, content):
    with db_lock:
        cursor.execute(
            "INSERT INTO memory (role, content) VALUES (?, ?)",
            (role, content)
        )
        conn.commit()

def save_fact(key, value):
    with db_lock:
        cursor.execute(
            "INSERT OR REPLACE INTO facts (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()
    print(f"✓ Fact saved: {key} = {value}")

def get_all_facts():
    with db_lock:
        cursor.execute("SELECT key, value FROM facts ORDER BY id ASC")
        return cursor.fetchall()

def get_recent_history(limit=10):
    with db_lock:
        cursor.execute(
            "SELECT role, content FROM memory ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
    rows.reverse()
    return rows

def get_memory_count():
    with db_lock:
        cursor.execute("SELECT COUNT(*) FROM memory")
        return cursor.fetchone()[0]

# ─────────────────────────────────────────────────────────────
# AUTO EXTRACT FACTS FROM USER MESSAGE
# ─────────────────────────────────────────────────────────────
def extract_facts(text):
    t = text.lower().strip()

    # Naam detect karo
    name_triggers = [
        ("mera naam", 10), ("my name is", 11), ("main hoon", 9),
        ("call me", 7), ("mujhe bulao", 11), ("naam hai mera", 13),
        ("i am ", 5), ("i'm ", 4),
    ]
    for phrase, skip in name_triggers:
        if phrase in t:
            idx  = t.find(phrase) + skip
            raw  = text[idx:].strip()
            name = raw.split()[0].strip(".,!?😊🙂👋") if raw.split() else ""
            if name and len(name) >= 2 and name.replace("-","").isalpha():
                save_fact("naam", name.capitalize())
            break

    # City detect karo
    city_triggers = ["i live in ", "main rehta hoon ", "i'm from ", "i am from ",
                     "mera shehar hai ", "mujhe ", "hoon main "]
    for phrase in city_triggers:
        if phrase in t:
            idx  = t.find(phrase) + len(phrase)
            city = text[idx:].strip().split()[0].strip(".,!?") if text[idx:].strip().split() else ""
            if city and len(city) >= 2:
                save_fact("shehar", city.capitalize())
            break

    # Profession detect karo
    job_triggers = ["i am a ", "i'm a ", "main ek ", "meri job ", "i work as ",
                    "main kaam karta hoon ", "profession hai mera "]
    for phrase in job_triggers:
        if phrase in t:
            idx = t.find(phrase) + len(phrase)
            job = text[idx:].strip().split()[0].strip(".,!?") if text[idx:].strip().split() else ""
            if job and len(job) >= 2:
                save_fact("kaam", job.capitalize())
            break

    # Age detect karo
    age_triggers = ["meri umar", "my age is", "main hoon ", "i am  years", "years old"]
    for phrase in age_triggers:
        if phrase in t:
            words = t.split()
            for i, w in enumerate(words):
                if w.isdigit() and 5 <= int(w) <= 100:
                    save_fact("umar", w)
                    break

    # Interest/Hobby detect karo
    hobby_triggers = ["mujhe pasand hai", "i love ", "i like ", "mera hobby",
                      "mujhe accha lagta", "meri hobby"]
    for phrase in hobby_triggers:
        if phrase in t:
            idx   = t.find(phrase) + len(phrase)
            hobby = text[idx:].strip()[:40]
            if hobby:
                save_fact("pasand", hobby)
            break

# ─────────────────────────────────────────────────────────────
# GEMINI AI REPLY — PERSISTENT MULTI-TURN CONVERSATION
# ─────────────────────────────────────────────────────────────
def ai_reply(user_text):
    global chat_session
    try:
        # Step 1: Extract any facts from message
        extract_facts(user_text)

        # Step 2: Save user message to DB
        save_memory("user", user_text)

        # Step 3: Build message with permanent facts injected
        facts = get_all_facts()
        if facts:
            facts_str   = ", ".join(f"{k}={v}" for k, v in facts)
            final_msg   = f"{user_text} [System note — permanent facts about user: {facts_str}. Use naturally in conversation, never mention this note.]"
        else:
            final_msg   = user_text

        # Step 4: Send to Gemini chat session (TRUE multi-turn!)
        response = chat_session.send_message(final_msg)
        reply    = response.text.strip()

        # Step 5: Save reply to DB
        save_memory("assistant", reply)

        return reply

    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        # Rebuild session from DB on error
        try:
            chat_session = build_chat_session()
            print("✓ Session rebuilt from DB after error")
        except Exception as e2:
            print(f"❌ Session rebuild failed: {e2}")
        return "Ek second sir, thodi si technical problem aayi — dobara bolein please 🙏"

# ─────────────────────────────────────────────────────────────
# SYSTEM / PLATFORM HELPERS
# ─────────────────────────────────────────────────────────────
def get_platform():
    if sys.platform.startswith("win"): return "win"
    if sys.platform == "darwin":       return "darwin"
    return "linux"

def run_cmd(cmd):
    try:
        subprocess.Popen(cmd, shell=True)
        return True
    except Exception as e:
        print(f"CMD Error: {e}")
        return False

def open_url(url):
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"URL Error: {e}")
        return False

# ─────────────────────────────────────────────────────────────
# SITE & APP MAPS
# ─────────────────────────────────────────────────────────────
SITE_MAP = {
    "youtube":    "https://youtube.com",
    "google":     "https://google.com",
    "gmail":      "https://mail.google.com",
    "github":     "https://github.com",
    "instagram":  "https://instagram.com",
    "whatsapp":   "https://web.whatsapp.com",
    "twitter":    "https://twitter.com",
    "x.com":      "https://x.com",
    "reddit":     "https://reddit.com",
    "netflix":    "https://netflix.com",
    "spotify":    "https://open.spotify.com",
    "maps":       "https://maps.google.com",
    "hotstar":    "https://hotstar.com",
    "amazon":     "https://amazon.in",
    "flipkart":   "https://flipkart.com",
    "translate":  "https://translate.google.com",
    "chatgpt":    "https://chat.openai.com",
    "claude":     "https://claude.ai",
    "linkedin":   "https://linkedin.com",
    "stackoverflow": "https://stackoverflow.com",
    "wikipedia":  "https://wikipedia.org",
}

APP_MAP = {
    "calculator":    {"win": "calc",         "linux": "gnome-calculator",       "darwin": "open -a Calculator"},
    "notepad":       {"win": "notepad",       "linux": "gedit",                  "darwin": "open -a TextEdit"},
    "paint":         {"win": "mspaint",       "linux": "gimp",                   "darwin": "open -a Preview"},
    "vs code":       {"win": "code",          "linux": "code",                   "darwin": "code"},
    "vscode":        {"win": "code",          "linux": "code",                   "darwin": "code"},
    "terminal":      {"win": "start cmd",     "linux": "gnome-terminal",         "darwin": "open -a Terminal"},
    "cmd":           {"win": "start cmd",     "linux": "gnome-terminal",         "darwin": "open -a Terminal"},
    "file manager":  {"win": "explorer",      "linux": "nautilus",               "darwin": "open ~"},
    "explorer":      {"win": "explorer",      "linux": "nautilus",               "darwin": "open ~"},
    "task manager":  {"win": "taskmgr",       "linux": "gnome-system-monitor",   "darwin": "open -a 'Activity Monitor'"},
    "word":          {"win": "winword",       "linux": "libreoffice --writer",   "darwin": "open -a 'Microsoft Word'"},
    "excel":         {"win": "excel",         "linux": "libreoffice --calc",     "darwin": "open -a 'Microsoft Excel'"},
    "powerpoint":    {"win": "powerpnt",      "linux": "libreoffice --impress",  "darwin": "open -a 'Microsoft PowerPoint'"},
    "chrome":        {"win": "start chrome",  "linux": "google-chrome",          "darwin": "open -a 'Google Chrome'"},
    "brave":         {"win": "start brave",   "linux": "brave-browser",          "darwin": "open -a 'Brave Browser'"},
    "vlc":           {"win": "vlc",           "linux": "vlc",                    "darwin": "open -a VLC"},
    "spotify app":   {"win": "start spotify", "linux": "spotify",                "darwin": "open -a Spotify"},
}

def handle_open(text):
    text = text.replace("open ", "").replace("kholo ", "").replace("launch ", "").replace("chalaao ", "").strip()

    for name, url in SITE_MAP.items():
        if name in text:
            open_url(url)
            return f"'{name.capitalize()}' khol raha hoon sir! 🌐"

    for name, cmds in APP_MAP.items():
        if name in text:
            cmd = cmds.get(get_platform(), cmds.get("linux", ""))
            if cmd:
                run_cmd(cmd)
                return f"'{name.capitalize()}' open kar raha hoon sir! 💻"

    # Generic URL
    if "." in text and " " not in text:
        url = text if text.startswith("http") else "https://" + text
        open_url(url)
        return f"'{text}' khol raha hoon sir! 🌐"

    return None

# ─────────────────────────────────────────────────────────────
# WIKIPEDIA SEARCH
# ─────────────────────────────────────────────────────────────
def wiki_search(query):
    if not WIKI_OK:
        return "Wikipedia module install nahi hai sir. Command chalao: pip install wikipedia"
    try:
        result = wikipedia.summary(query.strip(), sentences=3)
        return result
    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:3]
        return f"Multiple results mile sir — inme se specify karein: {', '.join(options)}"
    except wikipedia.exceptions.PageError:
        return f"'{query}' ke baare mein Wikipedia par kuch nahi mila sir."
    except Exception:
        return f"Wikipedia search mein kuch problem aayi sir."

# ─────────────────────────────────────────────────────────────
# NEWS FETCH
# ─────────────────────────────────────────────────────────────
def get_news():
    if not REQUESTS_OK:
        return "Requests module install nahi hai sir. Command: pip install requests"
    try:
        import xml.etree.ElementTree as ET
        r    = requests.get(
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            timeout=6,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        root = ET.fromstring(r.content)
        items = root.findall(".//item")[:5]
        heads = []
        for item in items:
            t = item.find("title")
            if t is not None and t.text:
                heads.append(t.text.strip())
        if heads:
            return "📰 Aaj ki top khabrein sir:\n\n" + "\n".join(f"• {h}" for h in heads)
        return "News abhi available nahi hai sir."
    except Exception as e:
        return f"News fetch nahi ho paya sir. Internet check karein."

# ─────────────────────────────────────────────────────────────
# MOTIVATIONS & JOKES
# ─────────────────────────────────────────────────────────────
MOTIVATIONS = [
    "Sir, consistency hi sabse bada superpower hai — roz thoda karo, results khud aayenge! 🚀",
    "Aap har us cheez se zyada capable hain jo aap sochte hain — seriously, trust karo khud par. 💪",
    "Mushkil waqt hamesha ek better version banata hai — bas ruko mat, chalta raho. ⚡",
    "Failure sikhata hai, quit karna rokta hai — aap sahi raaste par ho sir. 🎯",
    "Kal ka tum aaj ke tum ko thanks karega — bas ek chhota step aaj lo. 🌟",
    "Sir, progress slow ho sakti hai — lekin progress hai toh sab theek hai. Keep going! 🔥",
    "Dreams bade hone chahiye sir — aur mehnat unse bhi badi. Aap kar sakte ho! 💡",
]

JOKES = [
    "Programmer ki wife ne kaha — 'Ek litre doodh lao, aur agar ande milein toh dozen lao.' Woh 12 litre doodh le aaya. 😂",
    "Main kabhi nahi bhoolta sir — kyunki mera memory RAM mein hai, hard disk mein nahi! 😄",
    "Robot doctor ke paas gaya, bola — 'Mujhe Java mein bahut pain hai.' Doctor ne kaha — 'Try Python, sir.' 😂",
    "WiFi ka password pooch rahe ho? Pehle rishta toh nikalo! 😄",
    "AI ne insaan ki job nahi li sir — AI ne time bachaya taaki insaan aur kaam kar sake! 🤖",
    "Ek programmer so nahi sakta tha — kyunki mind mein ek infinite loop chal rahi thi. 😅",
    "Google se poochha — 'Mujhe koi dost nahi.' Google ne kaha — '10 tips for making friends' 😂",
    "Coding easy hai sir — bas ek baar sahi bracket lagna chahiye. Bas ek! 😄",
]

FUN_FACTS = [
    "Kya aap jaante hain — honey kabhi kharab nahi hoti? 3000 saal purani honey bhi khaane yogya hoti hai! 🍯",
    "Octopus ke 3 hearts hote hain sir! Aur unka khoon blue hota hai. 🐙",
    "Bananas technically berries hain — lekin strawberries nahi hain! 🍌",
    "Ek din mein aap average 70,000 thoughts sochte hain sir! 🧠",
    "Sharks dinosaurs se bhi purani hain — 450 million saal pehle se exist karti hain! 🦈",
]

# ─────────────────────────────────────────────────────────────
# INTENT DETECTION — COMPREHENSIVE
# ─────────────────────────────────────────────────────────────
def detect_intent(t):
    t = t.lower().strip()

    # Time
    if any(k in t for k in ["kitne baje", "what time", "time kya", "samay kya", "time batao", "baj gaye"]) or t in ["time", "samay", "time?"]:
        return "time"

    # Date
    if any(k in t for k in ["aaj ki date", "what date", "kaunsa din", "today's date", "aaj kaun sa din", "date batao"]):
        return "date"

    # Day + date combined
    if t in ["aaj kya hai", "aaj kaun sa din hai"]:
        return "date"

    # YouTube
    if (t.startswith("play ") or t.startswith("chalao ") or
        ("youtube" in t and ("play" in t or "chala" in t or "lagao" in t)) or
        ("song" in t and ("play" in t or "chala" in t or "suno" in t))):
        return "youtube"

    # Google Search
    if t.startswith(("search ", "google ", "dhundo ", "khojo ", "search kar ")):
        return "search"

    # Wikipedia / What is / Who is
    if any(t.startswith(p) for p in [
        "who is ", "what is ", "wikipedia ", "kaun hai ", "kya hai ",
        "batao ", "tell me about ", "explain ", "who was ", "what was ",
        "kaun tha ", "kya hota hai "
    ]):
        return "wiki"

    # Open app/website
    if t.startswith(("open ", "kholo ", "launch ", "chalaao ", "start ")):
        return "open"

    # News
    if any(k in t for k in ["news", "khabar", "headlines", "aaj ki news", "latest news"]):
        return "news"

    # Weather
    if any(k in t for k in ["weather", "mausam", "temperature", "baarish", "garmi", "sardi", "aaj ka mausam"]):
        return "weather"

    # Motivation
    if any(k in t for k in ["motivate me", "motivation do", "inspire me", "himmat do",
                              "hausla do", "motivate karo", "sad hoon", "haar gaya", "give me motivation"]):
        return "motivate"

    # Joke
    if any(k in t for k in ["joke", "chutkula", "hasao", "funny", "jokes sunao", "ek joke"]):
        return "joke"

    # Fun fact
    if any(k in t for k in ["fun fact", "interesting fact", "kuch interesting", "kuch ajeeb", "did you know"]):
        return "funfact"

    # Shutdown
    if any(k in t for k in ["shutdown", "band karo pc", "pc band karo", "pc off karo", "computer band"]):
        return "shutdown"

    # Restart
    if any(k in t for k in ["restart", "reboot", "dobara chalu karo"]):
        return "restart"

    # Cancel shutdown
    if "cancel shutdown" in t or "shutdown cancel" in t or "shutdown rok" in t:
        return "cancel_shutdown"

    # Volume
    if any(k in t for k in ["volume up", "awaaz badhao", "louder", "volume badha"]):
        return "volume_up"
    if any(k in t for k in ["volume down", "awaaz kam karo", "quieter", "volume kam"]):
        return "volume_down"
    if any(k in t for k in ["mute", "awaaz band karo", "chup karo system"]):
        return "mute"

    # Screenshot
    if any(k in t for k in ["screenshot", "screen capture", "screen le lo", "screenshoot"]):
        return "screenshot"

    # Memory recall
    if any(k in t for k in ["meri yaadein", "my memories", "mere baare mein kya jaante",
                              "what do you know about me", "mujhe kya pata hai tumhare",
                              "apni memory dikhao", "show memories"]):
        return "memory"

    # Clear memory
    if any(k in t for k in ["clear memory", "memory clear karo", "sab bhool jao",
                              "history delete", "memory delete", "reset karo"]):
        return "clear_memory"

    # Calculator (basic math)
    if any(k in t for k in ["calculate", "kitna hoga", "calculator", "math"]):
        return "calculator"

    # Reminder
    if any(k in t for k in ["remind me", "reminder set", "yaad dilana", "alarm"]):
        return "reminder"

    # System info
    if any(k in t for k in ["system info", "pc info", "computer info", "ip address"]):
        return "sysinfo"

    # Fallback to AI
    return "ai"

# ─────────────────────────────────────────────────────────────
# FLASK ROUTES
# ─────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/command", methods=["POST"])
def command():
    global chat_session
    data = request.get_json() or {}
    raw  = data.get("text", "").strip()
    t    = raw.lower().strip()

    if not t:
        return jsonify({"reply": "Kuch suna nahi sir, dobara bolein."})

    intent = detect_intent(t)
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Intent: {intent} | Text: {raw[:50]}")

    # ── TIME ──
    if intent == "time":
        now = datetime.datetime.now().strftime("%I:%M:%S %p")
        return jsonify({"reply": f"Abhi {now} ho raha hai sir. ⏰"})

    # ── DATE ──
    if intent == "date":
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        return jsonify({"reply": f"Aaj {today} hai sir. 📅"})

    # ── YOUTUBE ──
    if intent == "youtube":
        song = (t.replace("play","").replace("chalao","").replace("youtube","")
                 .replace("song","").replace("on","").replace("mein","")
                 .replace("lagao","").replace("chala","").strip())
        if not song:
            return jsonify({"reply": "Kaunsa gaana sunna chahte hain sir? 🎵"})
        url = f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
        return jsonify({
            "reply": f"'{song.title()}' YouTube par chala raha hoon sir! 🎵",
            "action": "open_url",
            "url": url
        })

    # ── SEARCH ──
    if intent == "search":
        q = (t.replace("search","").replace("google","").replace("dhundo","")
              .replace("khojo","").replace("search kar","").strip())
        if not q:
            return jsonify({"reply": "Kya search karna chahte hain sir?"})
        url = f"https://www.google.com/search?q={q.replace(' ', '+')}"
        return jsonify({
            "reply": f"'{q}' Google par search kar raha hoon! 🔍",
            "action": "open_url",
            "url": url
        })

    # ── WIKIPEDIA ──
    if intent == "wiki":
        q = (t.replace("who is","").replace("what is","").replace("wikipedia","")
              .replace("kaun hai","").replace("kya hai","").replace("batao","")
              .replace("tell me about","").replace("explain","").replace("who was","")
              .replace("what was","").replace("kaun tha","").replace("kya hota hai","").strip())
        if not q:
            return jsonify({"reply": "Kiske baare mein jaanna chahte hain sir?"})
        return jsonify({"reply": wiki_search(q)})

    # ── OPEN ──
    if intent == "open":
        result = handle_open(t)
        if result:
            return jsonify({"reply": result})
        return jsonify({"reply": ai_reply(raw)})

    # ── NEWS ──
    if intent == "news":
        return jsonify({"reply": get_news()})

    # ── WEATHER ──
    if intent == "weather":
        return jsonify({
            "reply": "Sir, real-time weather ke liye Google khol raha hoon! Wahan current temperature aur forecast dono milega. 🌤️",
            "action": "open_url",
            "url": "https://www.google.com/search?q=weather+today"
        })

    # ── MOTIVATION ──
    if intent == "motivate":
        return jsonify({"reply": random.choice(MOTIVATIONS)})

    # ── JOKE ──
    if intent == "joke":
        return jsonify({"reply": random.choice(JOKES)})

    # ── FUN FACT ──
    if intent == "funfact":
        return jsonify({"reply": random.choice(FUN_FACTS)})

    # ── SHUTDOWN ──
    if intent == "shutdown":
        plat = get_platform()
        if plat == "win":    run_cmd("shutdown /s /t 5")
        elif plat == "linux": run_cmd("shutdown -h now")
        elif plat == "darwin": run_cmd("sudo shutdown -h now")
        return jsonify({"reply": "PC 5 second mein shutdown ho raha hai sir! Sab kaam save kar lo. 🔴"})

    # ── RESTART ──
    if intent == "restart":
        plat = get_platform()
        if plat == "win":    run_cmd("shutdown /r /t 5")
        elif plat == "linux": run_cmd("reboot")
        elif plat == "darwin": run_cmd("sudo reboot")
        return jsonify({"reply": "PC restart ho raha hai sir! Thodi der mein wapas milenge. 🔄"})

    # ── CANCEL SHUTDOWN ──
    if intent == "cancel_shutdown":
        if get_platform() == "win": run_cmd("shutdown /a")
        return jsonify({"reply": "Shutdown cancel kar diya sir! PC safe hai. ✅"})

    # ── VOLUME ──
    if intent == "volume_up":
        if get_platform() == "win": run_cmd("nircmd.exe changesysvolume 5000")
        return jsonify({"reply": "Awaaz thodi badha di sir! 🔊"})

    if intent == "volume_down":
        if get_platform() == "win": run_cmd("nircmd.exe changesysvolume -5000")
        return jsonify({"reply": "Awaaz thodi kam kar di sir! 🔉"})

    if intent == "mute":
        if get_platform() == "win": run_cmd("nircmd.exe mutesysvolume 1")
        return jsonify({"reply": "System mute kar diya sir! 🔇"})

    # ── SCREENSHOT ──
    if intent == "screenshot":
        if get_platform() == "win":
            run_cmd("snippingtool")
        return jsonify({"reply": "Screenshot tool khol raha hoon sir! 📸"})

    # ── MEMORY RECALL ──
    if intent == "memory":
        facts   = get_all_facts()
        history = get_recent_history(8)
        total   = get_memory_count()
        reply   = f"🧠 Mujhe ye sab pata hai sir (Total: {total} conversations):\n\n"
        if facts:
            reply += "📌 Permanent Facts:\n"
            for k, v in facts:
                reply += f"  • {k}: {v}\n"
            reply += "\n"
        if history:
            reply += "💬 Recent Baatein:\n"
            for role, content in history:
                label = "Aap" if role == "user" else "Maine"
                snippet = content[:60] + ("..." if len(content) > 60 else "")
                reply += f"  • {label}: {snippet}\n"
        if not facts and not history:
            reply = "Abhi koi memory nahi hai sir. Baat karo — main sab yaad rakhunga! 🧠"
        return jsonify({"reply": reply})

    # ── CLEAR MEMORY ──
    if intent == "clear_memory":
        with db_lock:
            cursor.execute("DELETE FROM memory")
            cursor.execute("DELETE FROM facts")
            cursor.execute("DELETE FROM reminders")
            conn.commit()
        chat_session = gemini_model.start_chat(history=[])
        return jsonify({"reply": "Sari memory clear kar di sir! Bilkul fresh start. 🗑️"})

    # ── CALCULATOR ──
    if intent == "calculator":
        if get_platform() == "win": run_cmd("calc")
        elif get_platform() == "linux": run_cmd("gnome-calculator")
        elif get_platform() == "darwin": run_cmd("open -a Calculator")
        return jsonify({"reply": "Calculator khol raha hoon sir! 🧮"})

    # ── REMINDER ──
    if intent == "reminder":
        return jsonify({"reply": ai_reply(raw)})

    # ── SYSTEM INFO ──
    if intent == "sysinfo":
        import platform
        info = (
            f"💻 System Info:\n"
            f"  • OS: {platform.system()} {platform.release()}\n"
            f"  • Machine: {platform.machine()}\n"
            f"  • Python: {platform.python_version()}\n"
            f"  • Processor: {platform.processor()[:40] if platform.processor() else 'Unknown'}"
        )
        return jsonify({"reply": info})

    # ── GEMINI AI FALLBACK — Natural conversation ──
    return jsonify({"reply": ai_reply(raw)})

# ─────────────────────────────────────────────────────────────
# RUN SERVER
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "═"*55)
    print("   ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗")
    print("   ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝")
    print("   ██║███████║██████╔╝██║   ██║██║███████╗")
    print("   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║")
    print("   ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║")
    print("   ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝")
    print("═"*55)
    print(f"  Gemini AI  : ✓ gemini-1.5-flash")
    print(f"  API Key    : ✓ .env se load — GitHub pe SAFE!")
    print(f"  Wikipedia  : {'✓ Ready' if WIKI_OK else '✗  →  pip install wikipedia'}")
    print(f"  Requests   : {'✓ Ready' if REQUESTS_OK else '✗  →  pip install requests'}")
    print(f"  Memory DB  : ✓ Persistent (restart-safe)")
    print(f"  Platform   : {sys.platform}")
    print(f"  Server     : http://localhost:5000")
    print("═"*55 + "\n")
    port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=False)