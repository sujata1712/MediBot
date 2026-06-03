import os
import sys
import warnings

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))       # SERVICES_DIR = backend/services/
BACKEND_DIR  = os.path.dirname(SERVICES_DIR)                    # BACKEND_DIR  = backend/
ROOT_DIR     = os.path.dirname(BACKEND_DIR)                     # ROOT_DIR     = project root (where .env lives)
sys.path.insert(0, BACKEND_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, ".env"))

if not os.getenv("GROQ_API_KEY"):
    raise EnvironmentError("GROQ_API_KEY is missing. Add it to your .env file.")

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from config import (
    VECTOR_DB_PATH, EMBEDDING_MODEL_NAME, RETRIEVAL_K,
    LLM_MODEL_NAME, LLM_TEMPERATURE, LLM_MAX_TOKENS,
)
from services.chat_history import wrap_chain_with_history
from services.prompts import MEDICAL_PROMPT

warnings.filterwarnings("ignore")

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatGroq(
    model=LLM_MODEL_NAME,
    temperature=LLM_TEMPERATURE,
    max_tokens=LLM_MAX_TOKENS,
)

# ── Embeddings & Vector Store ─────────────────────────────────────────────────
embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

db = FAISS.load_local(
    VECTOR_DB_PATH,
    embedding_model,
    allow_dangerous_deserialization=True,
)

retriever = db.as_retriever(
    search_type="similarity",
    search_kwargs={"k": RETRIEVAL_K},
)

# ── Prompt ────────────────────────────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    ("system", MEDICAL_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])

# ── RAG helpers ───────────────────────────────────────────────────────────────
def format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)

# Single-word small-talk terms that never need RAG retrieval
_SMALLTALK = {
    "ok", "okay", "alright", "sure", "thanks", "thank you", "ty", "got it",
    "hi", "hello", "hey", "hiya", "howdy", "great", "cool", "nice", "good",
    "yes", "no", "yep", "nope", "yup", "fine", "understood", "noted", "k",
}

def _needs_retrieval(question: str) -> bool:
    """
    Return False only when the message is a known small-talk phrase.
    FIX: previous logic had wrong operator precedence making the check always True.
    Correct: skip RAG only if the whole normalised string is in _SMALLTALK.
    """
    q = question.strip().lower().rstrip("!.,?")
    return q not in _SMALLTALK

def _get_retrieval_query(x: dict) -> str:
    """
    FIX: when an image analysis block is included in the question,
    extract only the user-facing question for FAISS retrieval.
    Sending the full 500-word image analysis block degrades embedding quality.
    """
    q = x["question"]
    # Image questions are prefixed with "Image Analysis:\n...\nUser Question:\n"
    if "User Question:" in q:
        parts = q.split("User Question:", 1)
        user_q = parts[1].strip()
        return user_q if user_q else q
    return q

def _get_context(x: dict) -> str:
    if not _needs_retrieval(x["question"]):
        return ""
    query = _get_retrieval_query(x)
    return format_docs(retriever.invoke(query))

# ── Chain ─────────────────────────────────────────────────────────────────────
rag_chain = (
    RunnablePassthrough.assign(context=_get_context)
    | prompt
    | llm
    | StrOutputParser()
)

conversational_chain = wrap_chain_with_history(
    rag_chain,
    input_key="question",
    history_key="chat_history",
)