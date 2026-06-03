# 🩺 MediBot — AI Medical Assistant

MediBot is a **RAG-based conversational medical assistant** built with LangChain, Groq LLM, FAISS vector search, and SQLite-powered session memory. It responds like a knowledgeable friend — warm, clear, and medically grounded — not like a textbook.

> ⚠️ **Disclaimer:** MediBot is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment.

---

## ✨ Features

- AI-powered medical Q&A with RAG (context-aware answers from medical PDFs)
- Voice input — speak your question, Whisper transcribes it automatically
- Image analysis — attach a skin condition, X-ray, or wound photo
- Real-time streaming responses (word-by-word SSE)
- Markdown-formatted answers with bullets, headings, and sections
- Persistent chat history — searchable and resumable sessions
- User authentication with cookie-based sessions

---

## 🧠 How It Works

```
User Input  (text / voice / image)
        ↓
Intent Check  →  Small-talk? Skip retrieval. Medical query? Continue.
        ↓
FAISS Vector Store  →  Retrieve top-5 relevant medical context chunks
        ↓
Groq LLM (LLaMA 3.3 70B)  →  Generate structured, formatted response
        ↓
SQLite Memory  →  Persist full conversation history per session
        ↓
FastAPI + SSE  →  Stream response token-by-token to the browser
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| LLM | Groq — LLaMA 3.3 70B Versatile |
| Vision | Groq — LLaMA 4 Scout 17B |
| Voice (STT) | Groq — Whisper Large v3 |
| Embeddings | HuggingFace — `all-MiniLM-L6-v2` |
| Vector Store | FAISS (top-5 similarity retrieval) |
| Memory | SQLite + LangChain `SQLChatMessageHistory` |
| RAG Framework | LangChain |
| Backend | FastAPI + SSE streaming |
| Frontend | Vanilla HTML / CSS / JS |
| Auth | Cookie-based sessions (hashed passwords) |
| Package Manager | uv |

---

## 📂 Project Structure

```
MediBot/
├── backend/
│   ├── data/
│   │   ├── raw/                    # Source medical PDFs (add your own)
│   │   ├── processed/              # Auto-generated chunks (not tracked)
│   │   └── vector_store/           # FAISS index (pre-built, ready to use)
│   ├── db/                         # Runtime databases — auto-created, not tracked
│   ├── services/
│   │   ├── build_index.py          # PDF → chunks → FAISS pipeline
│   │   ├── chat_history.py         # SQLite session management
│   │   ├── cli.py                  # CLI interface (text + voice + image)
│   │   ├── media_handler.py        # Voice (Whisper) + image analysis (Vision)
│   │   ├── prompts.py              # MediBot system prompt + vision prompt
│   │   └── rag_pipeline.py         # RAG chain + small-talk bypass + LLM setup
│   └── config.py                   # Paths and model configuration
├── frontend/
│   ├── index.html                  # Main chat UI
│   └── login.html                  # Login page
├── main.py                         # FastAPI server (auth, sessions, streaming)
├── users.json                      # Created automatically on first run (not tracked)
├── .env.example                    # Copy → .env and add your API keys
├── requirements.txt
└── README.md
```

---

## 🚀 Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/sujata1712/MediBot.git
cd MediBot
```

### 2. Create a virtual environment

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate     # Mac/Linux
.venv\Scripts\activate        # Windows

# OR using standard Python
python -m venv .venv
source .venv/bin/activate     # Mac/Linux
.venv\Scripts\activate        # Windows
```

### 3. Install dependencies

```bash
uv pip install -r requirements.txt   # using uv
# OR
pip install -r requirements.txt      # using pip
```

### 4. Set up environment variables

```bash
cp .env.example .env     # Mac/Linux
copy .env.example .env   # Windows
```

Open `.env` and add your API keys:

```env
GROQ_API_KEY=your_groq_key_here
HUGGINGFACE_API_TOKEN=your_huggingface_token_here
```

> 🔑 Groq key (free): https://console.groq.com  
> 🔑 HuggingFace token (free): https://huggingface.co/settings/tokens

### 5. Build the knowledge base *(skip if using the pre-built FAISS index)*

Add your medical PDFs to `backend/data/raw/`, then run:

```bash
python backend/services/build_index.py
```

### 6. Run MediBot

```bash
python main.py
```

The browser opens automatically at `http://localhost:8000/login`.

---

## 🌐 Web Interface

- **Text chat** — describe your symptoms or ask any health question
- **Voice input** — click the microphone and speak; MediBot transcribes and responds
- **Image upload** — attach a medical image with an optional follow-up question
- **Session sidebar** — all past conversations saved, searchable, and resumable
- **Streaming** — answers stream word-by-word in real time

### Authentication

- A default `admin` account is created automatically on first run.  
  Default credentials: `admin` / `medibot123` — **change this before sharing or deploying.**
- Sign-up is available from the login page to create additional accounts.
- Sessions are cookie-based and expire after 8 hours.

> 🔒 `users.json` and all database files are excluded from version control. They are created at runtime and contain private user data.

---

## 💻 CLI Mode

```bash
python backend/services/cli.py
```

```
Commands:
  new                  → Start a new conversation
  history              → View current session history
  sessions             → List all saved sessions
  load <session_id>    → Continue a previous session
  delete <session_id>  → Delete a session
  clear                → Delete ALL sessions
  voice [seconds]      → Speak your question (default: 60s)
  image <path>         → Analyze a medical image
  exit                 → Quit
```

---

## 📌 Project Status

- [x] PDF ingestion and chunking pipeline
- [x] FAISS vector store with semantic retrieval
- [x] RAG chain with Groq LLM (LLaMA 3.3 70B)
- [x] SQLite session memory (concurrent-safe)
- [x] CLI — text, voice, and image input
- [x] FastAPI backend — sessions and SSE streaming
- [x] Web UI — chat, sidebar, voice recorder, image upload
- [x] User authentication and session management

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).