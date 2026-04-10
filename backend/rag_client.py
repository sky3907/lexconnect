import os
import httpx
from typing import Optional

# RAG Service URL - can be configured via environment variable
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8001")

# HTTP client for RAG service calls
rag_client = httpx.AsyncClient(base_url=RAG_SERVICE_URL, timeout=60.0)


class RAGServiceClient:
    """Client for communicating with the RAG Model Service"""

    def __init__(self, base_url: str = RAG_SERVICE_URL):
        self.base_url = base_url

    async def get_answer(self, question: str, case_context: Optional[str] = None) -> dict:
        """
        Get a legal answer from the RAG service
        
        Args:
            question: The legal question
            case_context: Optional case details for context
            
        Returns:
            Dictionary with:
                - answer: Generated legal answer
                - retrieved_count: Number of documents retrieved
                - sources: List of source documents
        """
        payload = {
            "question": question,
            "case_context": case_context
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/answer",
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def retrieve_documents(self, question: str) -> dict:
        """Retrieve relevant legal documents without inference"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/retrieve",
                json={"question": question}
            )
            response.raise_for_status()
            return response.json()

    async def validate_query(self, question: str) -> dict:
        """Check if a question is about civil law"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/validate",
                json={"question": question}
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> dict:
        """Check if RAG service is healthy"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()


# Create a default client instance
rag_service = RAGServiceClient()
