# 🤖 JARVIS — Personal AI Voice Assistant

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?style=for-the-badge&logo=flask)
![Gemini AI](https://img.shields.io/badge/Gemini_AI-1.5_Flash-orange?style=for-the-badge&logo=google)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow?style=for-the-badge&logo=javascript)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightblue?style=for-the-badge&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

> **Just A Rather Very Intelligent System** — A fully functional, bilingual AI voice assistant inspired by Iron Man's JARVIS. Built with Python, Flask, and Google Gemini AI.

---

## 🎯 What is JARVIS?

JARVIS is a **personal AI assistant** that you can talk to — using your voice or by typing. It understands both **Hindi and English**, remembers your conversations permanently, controls your PC, opens apps and websites, and has natural human-like conversations powered by Google Gemini AI.

Think of it as your own personal ChatGPT — but running locally, with voice, with memory, and with full PC control.

---

## ✨ Features

### 🗣️ Voice & Conversation
- **Real-time voice recognition** — speak and see text appear automatically
- **Bilingual support** — Hindi aur English dono mein baat karo
- **Natural conversation** — powered by Google Gemini 1.5 Flash
- **Typewriter effect** — replies appear character by character
- **Text-to-speech** — Jarvis speaks back in human-like voice

### 🧠 Persistent Memory
- **Never forgets** — conversations saved in SQLite database
- **Remembers after restart** — server band karo, wapas chalao — sab yaad hai
- **Auto fact extraction** — naam, shehar, profession automatically save hota hai
- **Memory recall** — "meri yaadein dikhao" bolke sab dekho

### 💻 System Control
- **Shutdown / Restart / Cancel** PC commands
- **Volume control** — badhao, kam karo, mute karo
- **Screenshot** — snipping tool instantly
- **Open apps** — Calculator, Notepad, VS Code, Chrome, VLC, and more
- **Open websites** — YouTube, Gmail, WhatsApp, Netflix, Spotify, and 20+ sites

### 🌐 Web & Information
- **Google Search** — "search Python tutorials"
- **YouTube** — "play Arijit Singh"
- **Wikipedia** — "who is Elon Musk?"
- **Live News** — BBC world headlines
- **Real-time Weather** — location-based

### 🎨 Unique HUD Interface
- **Iron Man inspired UI** — 3-panel HUD layout
- **Live system stats** — CPU, RAM, Network, Battery
- **Animated AI avatar** — eyes blink, mouth moves while speaking
- **Particle background** — animated floating particles
- **Quick action buttons** — one-click commands
- **Memory bank panel** — visual conversation history
- **Weather widget** — real-time with geolocation

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| **Backend** | Python 3.10+, Flask 3.0, Flask-CORS |
| **AI Engine** | Google Gemini 1.5 Flash API |
| **Database** | SQLite3 (persistent memory) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Voice** | Web Speech API (Speech Recognition + TTS) |
| **Fonts** | Orbitron, Share Tech Mono, Rajdhani |
| **Weather** | Open-Meteo API (free, no key needed) |
| **News** | BBC RSS Feed |

---

## 📁 Project Structure

```
jarvis-full/
│
├── server.py              # Main Flask backend (844 lines)
├── memory.db              # SQLite database (auto-created)
├── requirements.txt       # Python dependencies
│
├── templates/
│   └── index.html         # Main UI (266 lines)
│
└── static/
    ├── app.js             # Frontend logic (423 lines)
    └── styles.css         # HUD styling (305 lines)

Total: 1838+ lines of code
```

---

## 🚀 Installation & Setup

### Step 1 — Clone the Repository
```bash
git clone https://github.com/yourusername/jarvis-ai.git
cd jarvis-ai
```

### Step 2 — Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Get Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com)
2. Click **Get API Key**
3. Copy your key (starts with `AIza...`)
4. Paste it in `server.py` at `GEMINI_API_KEY = "your_key_here"`

### Step 5 — Run the Server
```bash
python server.py
```

### Step 6 — Open in Browser
Open **Google Chrome** or **Microsoft Edge** and go to:
```
http://localhost:5000
```

> ⚠️ **Chrome or Edge required** for voice recognition (Web Speech API)

---

## 🎮 How to Use

### Voice Commands
Press `SPACE` or click the mic button and speak:

| Command | Example |
|---|---|
| **Time** | "Kitne baje hain?" / "What time is it?" |
| **Date** | "Aaj ki date?" / "What's today's date?" |
| **YouTube** | "Play Bohemian Rhapsody" / "Chalao Arijit Singh" |
| **Search** | "Search Python tutorials" / "Google karo AI news" |
| **Wikipedia** | "Who is Nikola Tesla?" / "Kya hai black hole?" |
| **Open site** | "Open YouTube" / "Kholo Instagram" |
| **Open app** | "Open Calculator" / "Launch VS Code" |
| **News** | "Latest news" / "Aaj ki khabar batao" |
| **Weather** | "Aaj ka mausam?" / "Weather batao" |
| **Joke** | "Ek joke sunao" / "Tell me a joke" |
| **Motivate** | "Motivate me" / "Himmat do" |
| **Memory** | "Meri yaadein dikhao" / "What do you know about me?" |
| **Shutdown** | "Shutdown" / "PC band karo" |
| **Volume** | "Volume up" / "Awaaz badhao" |
| **Screenshot** | "Screenshot lo" |
| **Clear** | "Clear memory" / "Sab bhool jao" |

### Keyboard Shortcuts
| Key | Action |
|---|---|
| `SPACE` | Toggle microphone |
| `ENTER` | Send message |
| `ESC` | Clear chat |

### Conversation Examples
```
You: "Mera naam Rahul hai"
Jarvis: "Achha Rahul bhai! Nice to meet you 😊 Kya chal raha hai aajkal?"

You: "Aaj mood off hai"
Jarvis: "Arre yaar 😔 kya hua aaj? Baat karo, sun raha hoon."

You: "Mujhe coding nahi aati"
Jarvis: "Bilkul normal hai — starting mein sabko aisa lagta hai 😊
         Kaun si language? Main step by step help karta hoon."
```

---

## 📦 Requirements

```txt
flask>=3.0.0
flask-cors>=4.0.0
google-generativeai>=0.5.0
wikipedia>=1.4.0
requests>=2.31.0
```

Install with:
```bash
pip install -r requirements.txt
```

---

## 🔮 Future Plans

- [ ] 📸 Camera integration — face recognition
- [ ] 🎵 Spotify playback control
- [ ] 📧 Gmail read & send
- [ ] ⏰ Real alarm/reminder system
- [ ] 🌍 Multi-language support (Tamil, Bengali, etc.)
- [ ] 🖥️ Desktop app (Electron/Tauri)
- [ ] 📱 Mobile responsive UI
- [ ] 🔌 Smart home integration

---

## 👨‍💻 Author

**Gopal**
- Built from scratch with Python + JS
- Inspired by Iron Man's JARVIS
- Powered by Google Gemini AI

---

## 📄 License

This project is licensed under the **MIT License** — feel free to use, modify, and distribute.

---

## ⭐ Support

Agar ye project aapko pasand aaya toh **Star** zaroor dena! ⭐

```
"The best way to predict the future is to create it." — Jarvis 🤖
```
