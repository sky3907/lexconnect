"""
RAG Model Service - Separate FastAPI Service for Legal Document Retrieval and Inference
This service handles all RAG-related tasks independently from the main backend.
"""


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List

from rag_slm import CivilRAGSLM

# Initialize FastAPI app
app = FastAPI(
    title="LexConnect - RAG Model Service",
    description="Handles legal document retrieval and inference using RAG + SLM"
)

# CORS middleware for cross-service communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system at startup
print("📚 Starting RAG Model Service...")
rag = CivilRAGSLM()
print("✓ RAG system initialized successfully")


# ── Request/Response Models ────────────────────────────────────────────────
class RAGRequest(BaseModel):
    """Request model for RAG inference"""
    question: str
    case_context: Optional[str] = None


class RetrievedDocument(BaseModel):
    """Model for retrieved documents"""
    text: Optional[str] = None
    chunk: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None


class RAGResponse(BaseModel):
    """Response model for RAG results"""
    answer: str
    retrieved_count: int
    sources: List[Dict]


# ── Health Check Endpoint ──────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint to verify service is running"""
    return {
        "status": "healthy",
        "service": "LexConnect RAG Model Service",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def detailed_health():
    """Detailed health check with RAG status"""
    return {
        "status": "healthy",
        "service": "LexConnect RAG Model Service",
        "rag_loaded": True,
        "faiss_index": f"{rag.index.ntotal} vectors",
        "metadata_entries": len(rag.metadatas)
    }


# ── Main RAG Endpoints ────────────────────────────────────────────────────
@app.post("/answer", response_model=RAGResponse, tags=["RAG"])
def get_rag_answer(request: RAGRequest) -> RAGResponse:
    """
    Get legal answer using RAG + SLM inference
    
    **Parameters:**
    - `question` (str): Legal question from user
    - `case_context` (str, optional): Case details for context-aware answers
    
    **Returns:**
    - `answer`: Generated legal answer
    - `retrieved_count`: Number of documents retrieved
    - `sources`: List of source documents used
    """
    result = rag.answer(
        question=request.question,
        case_context=request.case_context
    )
    return RAGResponse(**result)


@app.post("/retrieve", tags=["RAG"])
def retrieve_documents(request: RAGRequest) -> Dict:
    """
    Retrieve relevant legal documents without inference
    Useful for direct source access without generating an answer
    """
    retrieved = rag.retrieve(
        query=request.question,
        topk=5
    )
    return {
        "query": request.question,
        "retrieved_count": len(retrieved),
        "documents": retrieved
    }


@app.post("/classify", tags=["RAG"])
def classify_question(request: RAGRequest) -> Dict:
    """
    Classify question type: procedural, definition, or rights
    """
    q_type = rag._classify_question(request.question)
    return {
        "question": request.question,
        "type": q_type,
        "description": {
            "procedural": "How-to questions requiring step-by-step instructions",
            "definition": "Questions asking for definitions or explanations",
            "rights": "Questions about legal rights and remedies"
        }[q_type]
    }


@app.post("/validate", tags=["RAG"])
def validate_civil_query(request: RAGRequest) -> Dict:
    """
    Check if a question is about civil law topics
    Helps filter off-topic questions before processing
    """
    from rag_slm import is_civil_query
    
    is_valid = is_civil_query(request.question)
    return {
        "question": request.question,
        "is_civil_query": is_valid,
        "message": "Valid civil law question" if is_valid else "Question may be off-topic for legal assistance"
    }


# ── Batch Processing Endpoints ────────────────────────────────────────────
@app.post("/batch-answer", tags=["RAG"])
def batch_answer(requests: List[RAGRequest]) -> Dict:
    """
    Process multiple questions in a batch
    Useful for handling multiple client queries efficiently
    """
    results = []
    for req in requests:
        result = rag.answer(question=req.question, case_context=req.case_context)
        results.append({
            "question": req.question,
            "answer": result["answer"],
            "retrieved_count": result["retrieved_count"]
        })
    
    return {
        "total_processed": len(results),
        "results": results
    }


# ── Service Info Endpoint ────────────────────────────────────────────────
@app.get("/info", tags=["Service"])
def service_info():
    """Get information about the RAG service"""
    return {
        "service_name": "LexConnect RAG Model Service",
        "version": "1.0.0",
        "capabilities": [
            "Legal document retrieval (FAISS index)",
            "Semantic search with embeddings",
            "Inference using Qwen2.5 3B SLM",
            "Indian civil law expertise",
            "Batch processing support"
        ],
        "rag_status": {
            "index_vectors": rag.index.ntotal,
            "metadata_entries": len(rag.metadatas),
            "embedding_model": "sentence-transformers",
            "inference_model": "Qwen2.5-3B-Instruct"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
