# rag_slm.py - FIXED FOR YOUR 800 CIVIL CASES
import json
from typing import List, Dict, Optional
import faiss
from sentence_transformers import SentenceTransformer
from config_paths import FAISS_INDEX_PATH, META_JSONL, EMBED_MODEL_NAME
from local_slm import calllocalslm as call_local_slm

TOP_K = 5


class CivilRAGSLM:
    def __init__(self):
        print("Loading FAISS index and metadata...")
        self.embed_model = SentenceTransformer(EMBED_MODEL_NAME)
        self.index = faiss.read_index(str(FAISS_INDEX_PATH))
        print(f"FAISS index loaded: {self.index.ntotal} vectors")
        
        self.metadatas: List[Dict] = []
        with open(META_JSONL, 'r', encoding='utf-8') as f:
            for line in f:
                self.metadatas.append(json.loads(line.strip()))
        print(f"Metadata loaded: {len(self.metadatas)} entries")

    def retrieve(self, query: str, topk: int = TOP_K) -> List[Dict]:
        q_vec = self.embed_model.encode([query], convert_to_numpy=True, show_progress_bar=False)
        _, I = self.index.search(q_vec, topk)
        
        results = []
        for idx in I[0]:
            if 0 <= idx < len(self.metadatas):
                results.append(self.metadatas[idx])
        return results

    def build_prompt(self, question: str, case_ctx: Optional[str] = None) -> str:
        full_query = f"{case_ctx or ''} {question}".strip()
        retrieved = self.retrieve(full_query)

        # ROBUST text extraction - tries multiple possible field names
        sources = []
        for i, doc in enumerate(retrieved, 1):
            # Try common field names from your extraction script
            text = (doc.get('text') or 
                   doc.get('chunk') or 
                   doc.get('content') or 
                   doc.get('full', {}).get('text') or 
                   str(doc).split('text', 1)[-1][:200] or 
                   "No text found")
            text = text[:250].replace('\n', ' ').strip()
            
            file = doc.get('file', doc.get('filename', 'unknown'))
            page = doc.get('page', doc.get('pagenum', '?'))
            
            sources.append(f"[{i}] {file} (p{page}): {text}")
        
        sources_text = '\n'.join(sources) if sources else "No relevant civil cases found in database."
        
        prompt = f"""You are a civil law assistant using 800+ Indian civil case judgments.

USE ONLY the case extracts below to answer.

CASES:
{sources_text}

QUESTION: {question}

Answer briefly and accurately:"""
        
        return prompt

    def answer(self, question: str, case_context: Optional[str] = None) -> Dict:
        prompt = self.build_prompt(question, case_context)
        raw = call_local_slm(prompt, max_new_tokens=150, temperature=0.2)
        answer = raw.strip()
        
        return {
            "answer": answer,
            "retrieved_count": len(self.retrieve(question)),
            "prompt_used": prompt[:500] + "..."  # First 500 chars for debugging
        }
