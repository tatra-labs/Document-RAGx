from pathlib import Path 
import environ 

BASE_DIR = Path(__file__).resolve().parent

env = environ.Env(DEBUG=(bool, False))

PROJECT_NAME = "Document-RAGx-v1.0" 

LLM_PROVIDER = env("LLM_PROVIDER", default="http://localhost:11434/")
LLM_MODEL = env("LLM_MODEL", default="llama3.2")
EMBEDDING_MODEL = env("EMBEDDING_MODEL", default="models/all-mpnet-base-v2")

INSTRUCTOR_BASE_URL = env("INSTRUCTOR_BASE_URL", default="http://localhost:11434/v1") 
INSTRUCTOR_API_KEY = env("INSTRUCTOR_API_KEY", default="ollama")

INDICES = env("INDICES", default="./indices")
COLLECTION_NAME = env("COLLECTION_NAME", default="document-RAGx")
VECTOR_STORE_PATH = Path(str(INDICES)) / "vector_store" 
DOCUMENT_STORE_PATH = Path(str(INDICES)) / "document_store"

NUM_PERM=128 

DATA_DIR = env("DATA_DIR", default="./data")
SNAPSHOT_FILE = env("SNAPSHOT_FILE", default="./preprocess/snapshot.json")

chunk_size=1000 
chunk_overlap=200

k=5