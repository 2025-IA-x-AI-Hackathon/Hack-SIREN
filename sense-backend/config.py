"""설정 관리"""
import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j 설정
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Chroma 설정
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "data/chroma")
CHROMA_HOST = os.getenv("CHROMA_HOST", None)  # Docker 환경에서 사용
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_USE_HTTP_CLIENT = os.getenv("CHROMA_HOST") is not None  # Host가 설정되면 HttpClient 사용

# Gemini 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 384

