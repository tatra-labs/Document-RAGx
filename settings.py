from pathlib import Path 
import environ 

BASE_DIR = Path(__file__).resolve().parent

env = environ.Env(DEBUG=(bool, False))

PROJECT_NAME = "Document-RAGx-v1.0" 

EMBEDDING_MODEL = env("EMBEDDING_MODEL", default="all-mpnet-base-v2")
LLM_MODEL = env("LLM_MODEL", default="http://localhost:11434/")

INSTRUCTOR_BASE_URL = env("INSTRUCTOR_BASE_URL", default="http://localhost:11434/v1") 
INSTRUCTOR_API_KEY = env("INSTRUCTOR_API_KEY", default="ollama")

INDICES = env("INDICES", default="./indices")


chunk_size=1000 
chunk_overlap=200


