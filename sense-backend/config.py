"""설정 관리"""
import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j 설정
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Chroma 설정
CHROMA_PERSIST_DIR = "data/chroma"

# Gemini 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 384

