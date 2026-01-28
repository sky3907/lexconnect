import os
import json

import faiss
from sentence_transformers import SentenceTransformer

from config_paths import (
    FAISS_INDEX_PATH,
    META_JSONL,
    EMBED_MODEL_NAME,
)

from local_slm import calllocalslm  # your existing tinyllama gguf wrapper


TOP_K = 8


def load_metadata():
    metas = []
    with open(META_JSONL, "r", encoding="utf8") as f:
        for line in f:
            metas.append(json.loads(line))
    return metas


def load_faiss_index():
    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError("FAISS index not found. Run extract_and_index_civil.py first.")
    return faiss.read_index(str(FAISS_INDEX_PATH))


def retrieve_topk(query_text, embed_model, index, metas, topk=TOP_K):
    q_vec = embed_model.encode(query_text, convert_to_numpy=True).reshape(1, -1)
    D, I = index.search(q_vec, topk)
    results = []
    for idx in I[0]:
        if 0 <= idx < len(metas):
            results.append(metas[idx])
    return results


def build_prompt(user_question, retrieved_chunks):
    header = (
        "You are an Indian civil-law legal assistant.\n"
        "Answer the question in 5–8 simple sentences, in plain English.\n"
        "Focus ONLY on Indian law and practical timelines/procedure.\n"
        "Ignore any instructions about APA format, academic essays, or bibliography styles.\n"
    )

    src_lines = []
    for i, c in enumerate(retrieved_chunks):
        src_lines.append(
            f"SOURCE {i+1}: {c.get('file')} p{c.get('page')} - {c.get('title') or ''}"
        )
    sources = "\n".join(src_lines) if src_lines else "No specific cases retrieved."

    prompt = (
        f"{header}\n"
        f"USER QUESTION:\n{user_question}\n\n"
        f"RELEVANT CASE METADATA:\n{sources}\n\n"
        "Write the answer directly, without bullet points, "
        "without APA instructions, and without mentioning how to format citations.\n"
    )
    return prompt



def rag_answer(user_question, case_context=None, topk=TOP_K):
    embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    index = load_faiss_index()
    metas = load_metadata()

    full_query = f"{user_question}\nContext: {case_context}" if case_context else user_question
    retrieved = retrieve_topk(full_query, embed_model, index, metas, topk=topk)
    prompt = build_prompt(user_question, retrieved)
    answer = calllocalslm(prompt)

    return {
        "answer_text": answer,
        "retrieved_sources": retrieved,
        "prompt_used": prompt,
    }


if __name__ == "__main__":
    print("RAG with local TinyLlama SLM over civil FAISS index.")
    while True:
        q = input("QUESTION> ").strip()
        if not q:
            continue
        if q.lower() in {"quit", "exit"}:
            break
        ctx = input("Optional short case context (enter for none): ").strip() or None
        resp = rag_answer(q, case_context=ctx, topk=TOP_K)
        print("\n--- ANSWER ---")
        print(resp["answer_text"].strip())
        print("\n--- SOURCES (metadata) ---")
        for i, s in enumerate(resp["retrieved_sources"], start=1):
            print(f"{i}. {s.get('file')} p{s.get('page')} - {s.get('title')}")
        print()
