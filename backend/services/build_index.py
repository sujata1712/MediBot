import os
import pickle
import sys

# Disable oneDNN + TensorFlow INFO/WARNING logs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Add project root to PYTHONPATH
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))       # SERVICES_DIR = backend/services/
BACKEND_DIR  = os.path.dirname(SERVICES_DIR)                    # BACKEND_DIR  = backend/
ROOT_DIR     = os.path.dirname(BACKEND_DIR)                     # ROOT_DIR     = MEDIBOT/ (where .env lives)

sys.path.insert(0, BACKEND_DIR)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Import Libraries
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

import warnings
warnings.filterwarnings("ignore")
# --------------------------------------------- PATH SETUP ---------------------------------------------

from config import RAW_DATA_PATH, PROCESSED_DATA_PATH, VECTOR_DB_PATH, CHUNKS_FILE_PATH, EMBEDDING_MODEL_NAME

# --------------------------------------------- LOAD RAW PDF(s) ---------------------------------------------

def load_pdf_files(data):

    if not os.path.exists(data):
        raise FileNotFoundError(f"Data path not found: {data}")
    
    loader = DirectoryLoader(
        data,
        glob='**/*.pdf',                # recursive
        loader_cls=PyPDFLoader
    )
    
    documents = loader.load()

    if not documents:
        raise ValueError("No PDF documents were loaded. Check your data folder.")

    return documents


documents = load_pdf_files(data= RAW_DATA_PATH)

# print("Document:\n", documents[15])
# print("Document:\n", documents[15].page_content)
print(f"Loaded {len(documents)} PDF pages")


# --------------------------------------------- CREATE TEXT CHUNKS ---------------------------------------------     

def create_chunks(extracted_data):
    
    if not extracted_data:
        raise ValueError("No documents provided for chunking")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    
    text_chunks= splitter.split_documents(extracted_data)

    if not text_chunks:
        raise ValueError("Chunking failed: no text chunks created")

    os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)      # ensure folder exists

    # save chunks
    with open(CHUNKS_FILE_PATH, "wb") as f:
        pickle.dump(text_chunks, f)
    return text_chunks


text_chunks = create_chunks(extracted_data = documents)

# print("Chunks:\n", text_chunks[20])
print(f"Created {len(text_chunks)} text chunks")


# --------------------------------------------- CREATE VECTOR EMBEDDINGS --------------------------------------------- 

def get_embedding_model():

    try:
        embed_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        return embed_model

    except Exception as e:
        raise RuntimeError(f"Embedding model load failed: {e}")

embeddings = get_embedding_model()

# --------------------------------------------- STORE EMBEDDINGS IN VECTOR DB --------------------------------------------- 

def create_vectorstore(text_chunks, embedding_model):
    
    if not text_chunks:
        raise ValueError("No text chunks to embed")

    os.makedirs(VECTOR_DB_PATH, exist_ok=True)      # ensure folder exists

    try:
        db = FAISS.from_documents(text_chunks, embedding_model)     # create FAISS DB
        db.save_local(VECTOR_DB_PATH)       # save data
    
    except Exception as e:
        raise RuntimeError(f"Vector Database creation failed: {e}")

    return db

db = create_vectorstore(text_chunks, embeddings)

print("FAISS vector store created successfully")



# ------------------------------------------------------------------------------------------ 

print("="*80)
print("Knowledge base created successfully")
