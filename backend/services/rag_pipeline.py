import os
import sys
import warnings

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

ROOT_DIR = os.path.dirname(BACKEND_DIR)

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

from config import VECTOR_DB_PATH, EMBEDDING_MODEL_NAME, RETRIEVAL_K, LLM_MODEL_NAME, LLM_TEMPERATURE, LLM_MAX_TOKENS

from chat_history import wrap_chain_with_history
from prompts import MEDICAL_PROMPT

warnings.filterwarnings("ignore")
# --------------------------------------------- Load Components ---------------------------------------------
# LLM
llm = ChatGroq(
    model=LLM_MODEL_NAME,
    temperature=LLM_TEMPERATURE,
    max_tokens=LLM_MAX_TOKENS,
)

# Embeddings & Vector Store
embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

db = FAISS.load_local(
    VECTOR_DB_PATH,
    embedding_model,
    allow_dangerous_deserialization=True
)

# Set up retriever with similarity search and k results
retriever = db.as_retriever(
    search_type="similarity",
    search_kwargs={"k": RETRIEVAL_K}
)

# --------------------------------------------- Prompt ---------------------------------------------

prompt = ChatPromptTemplate.from_messages([
    ("system", MEDICAL_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])

# --------------------------------------------- RAG Chain ---------------------------------------------

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    RunnablePassthrough.assign(
        context=lambda x: format_docs(retriever.invoke(x["question"]))
    )
    | prompt
    | llm
    | StrOutputParser()
)

# Wrap with SQLite memory
conversational_chain = wrap_chain_with_history(
    rag_chain,
    input_key="question",
    history_key="chat_history",
)
