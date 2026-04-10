from pathlib import Path

# RAG Service root dir
ROOT_DIR = Path(__file__).parent.absolute()

# Paths point to the shared data folder one level up
PARENT_DIR = ROOT_DIR.parent
DATA_DIR = PARENT_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"

# FAISS data files (shared with backend)
CIVIL_JSONL = DATA_DIR / "civil_chunks.jsonl"      # text + metadata
FAISS_INDEX_PATH = DATA_DIR / "faiss_civil.index"  # vector index
META_JSONL = DATA_DIR / "civil_meta.jsonl"         # metadata only

# Embedding model name
EMBED_MODEL_NAME = "intfloat/e5-small-v2"  # lightweight and effective
