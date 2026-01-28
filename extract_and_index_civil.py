import os
import re
import json
from pathlib import Path

import fitz  # PyMuPDF
import faiss
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

from config_paths import (
    PDF_DIR,
    CIVIL_JSONL,
    FAISS_INDEX_PATH,
    META_JSONL,
    EMBED_MODEL_NAME,
)

CRIMINAL_PATTERNS = [
    r"\bFIR\b",
    r"\bIndian Penal Code\b",
    r"\bIPC\b",
    r"\bSections?\s*\d+/\d+\b",
    r"\bSections?\s*\d+\b\s*IPC\b",
    r"\bpolice\b",
    r"\bcharges?\b",
]

CIVIL_PATTERNS = [
    r"\bCivil Appeal\b",
    r"\bWrit Petition\b",
    r"\bCivil Revision\b",
    r"\bOriginal Application\b",
    r"\bservice law\b",
    r"\bcivil\b",
    r"\bjurisdiction\b",
    r"\bpetition\b",
]


def is_civil_page(title: str, filename: str, text: str, max_chars: int = 3000) -> bool:
    combined = " ".join([
        title or "",
        filename or "",
        (text or "")[:max_chars],
    ]).lower()

    for pat in CRIMINAL_PATTERNS:
        if re.search(pat.lower(), combined):
            return False

    for pat in CIVIL_PATTERNS:
        if re.search(pat.lower(), combined):
            return True

    return False


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 200):
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - overlap

    return chunks


def create_or_load_faiss_index(dim: int):
    if os.path.exists(FAISS_INDEX_PATH):
        index = faiss.read_index(str(FAISS_INDEX_PATH))
    else:
        index = faiss.IndexFlatL2(dim)
    return index


def save_faiss_index(index):
    faiss.write_index(index, str(FAISS_INDEX_PATH))


def main():
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    CIVIL_JSONL.parent.mkdir(parents=True, exist_ok=True)
    META_JSONL.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading embedding model: {EMBED_MODEL_NAME}")
    embed_model = SentenceTransformer(EMBED_MODEL_NAME)

    dim = embed_model.get_sentence_embedding_dimension()
    index = create_or_load_faiss_index(dim)

    chunk_id_counter = 0
    batch_texts = []
    batch_meta = []
    BATCH_SIZE = 16

    civ_jsonl_f = open(CIVIL_JSONL, "w", encoding="utf8")
    meta_jsonl_f = open(META_JSONL, "w", encoding="utf8")

    pdf_files = list(PDF_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDFs in {PDF_DIR}")

    try:
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
            doc = fitz.open(pdf_path)
            try:
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    if not text or not text.strip():
                        continue

                    title = None
                    m_title = re.search(r"([A-Z].*?v(?:ersus)?\.?.*?)\n", text)
                    if m_title:
                        title = m_title.group(1).strip()

                    if not is_civil_page(title, pdf_path.name, text):
                        continue

                    chunks = chunk_text(text)
                    if not chunks:
                        continue

                    for ch in chunks:
                        chunk_id = f"{pdf_path.name}_p{page_num+1}_c{len(batch_texts)}_{chunk_id_counter}"
                        chunk_id_counter += 1

                        meta_full = {
                            "chunk_id": chunk_id,
                            "file": pdf_path.name,
                            "page": page_num + 1,
                            "title": title,
                            "text": ch,
                        }
                        civ_jsonl_f.write(json.dumps(meta_full, ensure_ascii=False) + "\n")

                        batch_texts.append(ch)
                        batch_meta.append({
                            "chunk_id": chunk_id,
                            "file": pdf_path.name,
                            "page": page_num + 1,
                            "title": title,
                        })

                        if len(batch_texts) >= BATCH_SIZE:
                            vecs = embed_model.encode(
                                batch_texts,
                                convert_to_numpy=True,
                                batch_size=BATCH_SIZE,
                            )
                            index.add(vecs)
                            for m in batch_meta:
                                meta_jsonl_f.write(json.dumps(m, ensure_ascii=False) + "\n")
                            batch_texts.clear()
                            batch_meta.clear()

            finally:
                doc.close()

        if batch_texts:
            vecs = embed_model.encode(
                batch_texts,
                convert_to_numpy=True,
                batch_size=BATCH_SIZE,
            )
            index.add(vecs)
            for m in batch_meta:
                meta_jsonl_f.write(json.dumps(m, ensure_ascii=False) + "\n")

    finally:
        civ_jsonl_f.close()
        meta_jsonl_f.close()

    save_faiss_index(index)
    print(f"Done. Saved FAISS index at {FAISS_INDEX_PATH}")
    print(f"Civil chunks JSONL at {CIVIL_JSONL}")
    print(f"Metadata JSONL at {META_JSONL}")


if __name__ == "__main__":
    main()
