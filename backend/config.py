import os

# ---------------------------- BASE DIRECTORY ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------- DATA DIRECTORIES & FILE PATHS ---------------------------
DATA_DIR = os.path.join(BASE_DIR, "data")

RAW_DATA_PATH = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_PATH = os.path.join(DATA_DIR, "processed")
VECTOR_DB_PATH = os.path.join(DATA_DIR, "vector_store")

CHUNKS_FILE_PATH = os.path.join(PROCESSED_DATA_PATH, "chunks.pkl")

# ---------------------------- MODEL CONFIG ---------------------------
# embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# LLM
LLM_MODEL_NAME = "llama-3.1-8b-instant"
LLM_TEMPERATURE = 0.5
LLM_MAX_TOKENS = 1024

# ---------------------------- RETRIEVAL CONFIG ---------------------------
RETRIEVAL_K = 5
MEMORY_WINDOW = 6

# ---------------------------- DATABASE CONFIG ---------------------------
DB_DIR = os.path.join(BASE_DIR, "db")
os.makedirs(DB_DIR, exist_ok=True) # Ensure folder exists
DATABASE_PATH = os.path.join(DB_DIR, "chat_history.db")
CONNECTION_STRING = f'sqlite:///{DATABASE_PATH}'
