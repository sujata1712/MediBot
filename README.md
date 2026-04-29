# 🩺 MediBot — AI Medical Assistant

> ⚠️ **Work in Progress** — Backend fully functional. Frontend integration in progress.

MediBot is a **RAG-based conversational medical assistant** built with LangChain,
Groq LLM, FAISS vector search, and SQLite-powered session memory. It responds
like a knowledgeable friend — warm, clear, and helpful — not like a medical textbook.

---

## 🧠 How It Works

```
User Question
     ↓
FAISS Vector Store  →  Retrieve relevant medical context
     ↓
Groq LLM (LLaMA 3) →  Generate warm, helpful response
     ↓
SQLite Memory       →  Remember full conversation history
```

---

## 🗂️ Project Structure

```
MediBot/
├── backend/
│   ├── data/
│   │   ├── raw/                    # Source medical PDF(s)
│   │   ├── processed/              # Auto-generated chunks (not tracked)
│   │   └── vector_store/           # FAISS index (pre-built, ready to use)
│   ├── db/                         # SQLite chat history (runtime, not tracked)
│   ├── services/
│   │   ├── rag_pipeline.py         # RAG chain + Groq LLM setup
│   │   ├── chat_history.py         # SQLite session management
│   │   ├── build_index.py          # PDF → chunks → FAISS pipeline
│   │   ├── prompts.py              # MediBot system prompt
│   │   └── cli.py                  # CLI chat interface
│   └── config.py                   # Paths and model configuration
├── frontend/
│   └── index.html                  # Web UI (in progress)
├── .env.example                    # Copy this → .env and add your keys
├── requirements.txt
├── pyproject.toml
├── uv.lock
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
```

**Using standard Python:**
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
```

### 3. Install dependencies

**Using `uv`:**
```bash
uv pip install -r requirements.txt
```

**Using pip:**
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
copy .env.example .env
```
Open `.env` and add your API keys:
```
GROQ_API_KEY=your_groq_key_here
HUGGINGFACE_API_TOKEN=your_huggingface_token_here
```
> Get Groq key free at: https://console.groq.com  
> Get HuggingFace token free at: https://huggingface.co/settings/tokens

### 5. Build the knowledge base
```bash
python backend/services/build_index.py
```
> ⚠️ Only needed if you're using your own PDFs.  
> The pre-built FAISS vector store is already included and ready to use.

### 6. Run MediBot (CLI)
```bash
python backend/services/cli.py
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq API (LLaMA 3) |
| Embeddings | HuggingFace Sentence Transformers |
| Vector Store | FAISS |
| Memory | SQLite + LangChain |
| Orchestration | LangChain (RAG chain) |
| Frontend | HTML/CSS/JS *(in progress)* |
| Package Manager | uv |

---

## 📌 Project Status

- [x] PDF ingestion and chunking pipeline
- [x] FAISS vector store creation
- [x] RAG chain with Groq LLM
- [x] Custom MediBot personality prompt
- [x] SQLite conversation memory with session management
- [x] CLI chat interface with search, load, delete, stats
- [ ] REST API (FastAPI) — *planned*
- [ ] Frontend (HTML/CSS/JS) — *in progress*
- [ ] Deployment — *planned*

---

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key (free at console.groq.com) |
| `HUGGINGFACE_API_TOKEN` | Your HuggingFace token (free at huggingface.co/settings/tokens) |

---

## ⚠️ Disclaimer

MediBot provides **educational health information only**.  
It is **not** a substitute for professional medical advice, diagnosis, or treatment.  
Always consult a qualified healthcare professional for medical concerns.
