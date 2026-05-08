# 🩺 MediBot — AI Medical Assistant

> ⚠️ **Work in Progress** — CLI fully functional. FastAPI + Web UI integration in progress.

MediBot is a **RAG-based conversational medical assistant** built with LangChain, Groq LLM, FAISS vector search, and SQLite-powered session memory. It responds like a knowledgeable friend — warm, clear, and helpful — not like a medical textbook.

---

## 🧠 How It Works

```
User Input (text / voice / image)
         ↓
FAISS Vector Store  →  Retrieve relevant medical context
         ↓
Groq LLM (LLaMA 3) →  Generate warm, helpful response
         ↓
SQLite Memory       →  Persist full conversation history
```

---

## 🗂️ Project Structure

```
MediBot/
├── backend/
│   ├── data/
│   │   ├── raw/                    # Source medical PDFs (add your own)
│   │   ├── processed/              # Auto-generated chunks (not tracked)
│   │   └── vector_store/           # FAISS index (pre-built, ready to use)
│   ├── db/                         # SQLite chat history (runtime, not tracked)
│   ├── services/
│   │   ├── build_index.py          # PDF → chunks → FAISS pipeline
│   │   ├── chat_history.py         # SQLite session management
│   │   ├── cli.py                  # CLI interface (text + voice + image)
│   │   ├── media_handler.py        # Voice recording & image analysis (Groq)
│   │   ├── prompts.py              # MediBot system prompt
│   │   └── rag_pipeline.py         # RAG chain + Groq LLM setup
│   └── config.py                   # Paths and model configuration
├── frontend/
│   └── index.html                  # Web UI (SSE streaming, voice, image upload)
├── main.py                         # FastAPI server (in progress)
├── .env.example                    # Copy this → .env and add your keys
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/sujata1712/MediBot.git
cd MediBot
```

### 2. Create a virtual environment

**Using `uv` (recommended):**
```bash
uv venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
```

**Using standard Python:**
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies

```bash
uv pip install -r requirements.txt   # using uv
# OR
pip install -r requirements.txt      # using pip
```

### 4. Set up environment variables

```bash
copy .env.example .env       # Windows
cp .env.example .env         # Mac/Linux
```

Open `.env` and add your API keys:
```
GROQ_API_KEY=your_groq_key_here
HUGGINGFACE_API_TOKEN=your_huggingface_token_here
```

> 🔑 Groq key (free): https://console.groq.com  
> 🔑 HuggingFace token (free): https://huggingface.co/settings/tokens

### 5. Build the knowledge base *(skip if using pre-built FAISS index)*

```bash
python backend/services/build_index.py
```

> Only needed if you add your own PDFs to `backend/data/raw/`.  
> The pre-built FAISS vector store is already included.

### 6. Run MediBot

```bash
python backend/services/cli.py
```

---

## 💬 CLI Usage

Once running, you can chat by typing normally, or use these commands:

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

### Text Input
Just type your question and press Enter:
```
You: I have a headache and fever, what should I do?
```

### Voice Input
Say `voice` and speak into your microphone:
```
You: voice        ← records for 60 seconds (stop speaking anytime)
You: voice 10     ← records for exactly 10 seconds
```
> Requires a working microphone. Powered by Groq Whisper (speech-to-text).

### Image Input
Give the full file path to any image on your computer:
```
You: image C:\Users\YourName\Desktop\rash.jpg
You: image /home/yourname/pictures/xray.png
```
> Works with images from any folder — no need to copy them into the project.  
> You'll be asked if you have a specific question about the image.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq API — LLaMA 3 |
| Embeddings | HuggingFace Sentence Transformers |
| Vector Store | FAISS |
| Memory | SQLite + LangChain |
| Voice Input | Groq Whisper (speech-to-text) |
| Image Input | Groq Vision model |
| Orchestration | LangChain RAG chain |
| Frontend | HTML / CSS / JS (SSE streaming) |
| API | FastAPI *(in progress)* |
| Package Manager | uv |

---

## 📌 Project Status

- [x] PDF ingestion and chunking pipeline
- [x] FAISS vector store creation
- [x] RAG chain with Groq LLM
- [x] Custom MediBot personality prompt
- [x] SQLite session memory (search, load, delete, stats)
- [x] CLI — text input
- [x] CLI — voice input (Groq Whisper)
- [x] CLI — image input (Groq Vision)
- [x] Frontend UI — chat, session sidebar, SSE streaming, voice recorder, image uploader
- [ ] FastAPI backend (`main.py`) — *in progress*
- [ ] Deployment — *planned*

---

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key — free at console.groq.com |
| `HUGGINGFACE_API_TOKEN` | HuggingFace token — free at huggingface.co/settings/tokens |

---

## ⚠️ Disclaimer

MediBot provides **educational health information only**.  
It is **not** a substitute for professional medical advice, diagnosis, or treatment.  
Always consult a qualified healthcare professional for medical concerns.
