# RAG Service API Reference

## Base URL

**Local Development:**
```
http://localhost:8001
```

**Production (Render):**
```
https://lexconnect-rag-service.onrender.com
```

---

## API Documentation (Interactive)

Both services provide interactive API documentation:

- **RAG Service Swagger UI:** `http://localhost:8001/docs`
- **RAG Service ReDoc:** `http://localhost:8001/redoc`

---

## Endpoints

### 1. Health Check

#### GET `/`
Basic health check

**Response:**
```json
{
  "status": "healthy",
  "service": "LexConnect RAG Model Service",
  "version": "1.0.0"
}
```

---

### 2. Detailed Health Check

#### GET `/health`
Detailed health check with RAG status

**Response:**
```json
{
  "status": "healthy",
  "service": "LexConnect RAG Model Service",
  "rag_loaded": true,
  "faiss_index": "10000 vectors",
  "metadata_entries": 5000
}
```

---

### 3. Get Legal Answer

#### POST `/answer`
Get a legal answer using RAG + SLM inference

**Request:**
```json
{
  "question": "What is a property dispute?",
  "case_context": null
}
```

**Request Body Parameters:**
- `question` (string, required): The legal question
- `case_context` (string, optional): Background context about the case

**Response:**
```json
{
  "answer": "A property dispute is a legal conflict between two or more parties regarding ownership, boundaries, or rights to real or personal property. In India, property disputes are governed primarily by the Transfer of Property Act 1882...",
  "retrieved_count": 3,
  "sources": [
    {
      "text": "Transfer of Property Act 1882 - Section 3: Definition of 'property'",
      "source": "legal_db",
      "chunk": 1
    },
    {
      "text": "Property disputes include cases of encroachment, boundary disagreement, inheritance claims...",
      "source": "case_law",
      "chunk": 5
    }
  ]
}
```

**Response Parameters:**
- `answer` (string): Generated legal answer
- `retrieved_count` (integer): Number of documents retrieved from FAISS
- `sources` (array): List of source documents used for the answer

**Example cURL:**
```bash
curl -X POST http://localhost:8001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is a property dispute?",
    "case_context": null
  }'
```

---

### 4. Retrieve Documents

#### POST `/retrieve`
Retrieve relevant legal documents without generating an answer

**Request:**
```json
{
  "question": "What is a property dispute?",
  "case_context": null
}
```

**Response:**
```json
{
  "query": "What is a property dispute?",
  "retrieved_count": 5,
  "documents": [
    {
      "text": "Property disputes are governed by the Transfer of Property Act 1882...",
      "source": "civil_code",
      "metadata": {}
    }
  ]
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "What is property dispute?"}'
```

---

### 5. Classify Question Type

#### POST `/classify`
Classify question into: procedural, definition, or rights

**Request:**
```json
{
  "question": "How do I file a property dispute case?"
}
```

**Response:**
```json
{
  "question": "How do I file a property dispute case?",
  "type": "procedural",
  "description": "How-to questions requiring step-by-step instructions"
}
```

**Question Types:**
- `procedural`: How-to questions requiring step-by-step instructions
- `definition`: Questions asking for definitions or explanations
- `rights`: Questions about legal rights and remedies

**Example cURL:**
```bash
curl -X POST http://localhost:8001/classify \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I file a property dispute?"}'
```

---

### 6. Validate Civil Query

#### POST `/validate`
Check if a question is about civil law topics

**Request:**
```json
{
  "question": "What is a property dispute?"
}
```

**Response:**
```json
{
  "question": "What is a property dispute?",
  "is_civil_query": true,
  "message": "Valid civil law question"
}
```

**Example - Off-topic Question:**
```bash
curl -X POST http://localhost:8001/validate \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the best cricket recipe?"}'
```

**Response:**
```json
{
  "question": "What is the best cricket recipe?",
  "is_civil_query": false,
  "message": "Question may be off-topic for legal assistance"
}
```

---

### 7. Batch Answer (Multiple Questions)

#### POST `/batch-answer`
Process multiple questions in a batch

**Request:**
```json
[
  {
    "question": "What is a property dispute?",
    "case_context": null
  },
  {
    "question": "How do I file a case?",
    "case_context": "Property dispute in Chennai"
  }
]
```

**Response:**
```json
{
  "total_processed": 2,
  "results": [
    {
      "question": "What is a property dispute?",
      "answer": "A property dispute is...",
      "retrieved_count": 3
    },
    {
      "question": "How do I file a case?",
      "answer": "Step 1: Visit the district court...",
      "retrieved_count": 4
    }
  ]
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8001/batch-answer \
  -H "Content-Type: application/json" \
  -d '[
    {"question": "What is property dispute?"},
    {"question": "Who is a lawyer?"}
  ]'
```

---

### 8. Service Information

#### GET `/info`
Get information about the RAG service capabilities

**Response:**
```json
{
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
    "index_vectors": 10000,
    "metadata_entries": 5000,
    "embedding_model": "sentence-transformers",
    "inference_model": "Qwen2.5-3B-Instruct"
  }
}
```

---

## Common Use Cases

### Use Case 1: Simple Question Answering
```bash
curl -X POST http://localhost:8001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are my rights in a property dispute?",
    "case_context": null
  }'
```

### Use Case 2: Case-Specific Advice
```bash
curl -X POST http://localhost:8001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What should I do next?",
    "case_context": "I own a property in Chennai that my neighbor claims ownership of. He has lived there for 5 years without my permission."
  }'
```

### Use Case 3: Filter Off-Topic Questions
```bash
curl -X POST http://localhost:8001/validate \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the recipe for biryani?"}'

# Returns:
# is_civil_query: false
# Message: "Question may be off-topic..."
```

### Use Case 4: Document Retrieval Only
```bash
curl -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "tenancy rights in Delhi"}'
```

---

## Integration with Backend

From the **Backend Service**, call the RAG service like this:

```python
from rag_client import rag_service

# Get answer with case context
result = await rag_service.get_answer(
    question="What is property dispute?",
    case_context="I own a property..."
)

# Retrieve documents without inference
docs = await rag_service.retrieve_documents("property dispute")

# Validate question is on-topic
is_valid = await rag_service.validate_query("What is property dispute?")

# Check if service is healthy
health = await rag_service.health_check()
```

---

## Request/Response Models

### RAGRequest
```{
  "question": string        # Required: Legal question
  "case_context": string    # Optional: Case background
}
```

### RAGResponse
```json
{
  "answer": string,         # Generated legal answer
  "retrieved_count": int,   # Number of documents retrieved
  "sources": [              # Array of source documents
    {
      "text": string,       # Document text
      "source": string,     # Source identifier
      "metadata": object    # Additional metadata
    }
  ]
}
```

---

## Error Handling

### HTTP Status Codes
- `200` - Success
- `400` - Bad request (invalid input)
- `422` - Validation error (missing required fields)
- `500` - Internal server error
- `503` - Service unavailable

### Error Response Example
```json
{
  "detail": "Question cannot be empty"
}
```

---

## Rate Limiting & Timeouts

**Timeout Values:**
- Answer endpoint: **60 seconds** (includes inference time)
- Retrieve endpoint: **30 seconds**
- Validate endpoint: **10 seconds**

**Performance Notes:**
- First answer takes 1-2 seconds (model inference)
- Subsequent answers are similar (not cached)
- FAISS retrieval is very fast (~50ms)

---

## Testing Endpoints

#### Test with Python Requests
```python
import requests

# Test /answer endpoint
response = requests.post(
    "http://localhost:8001/answer",
    json={
        "question": "What is property dispute?",
        "case_context": None
    }
)
print(response.json())

# Test health
health = requests.get("http://localhost:8001/health")
print(health.json())
```

#### Test with cURL
```bash
# All in one line for easy copy-paste
curl -X POST http://localhost:8001/answer -H "Content-Type: application/json" -d '{"question":"What is property dispute?","case_context":null}' | python -m json.tool
```

#### Test with JavaScript/Fetch
```javascript
const response = await fetch('http://localhost:8001/answer', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: 'What is property dispute?',
    case_context: null
  })
});
const data = await response.json();
console.log(data);
```

---

## Supported Legal Topics

The RAG service is trained on Indian civil law topics:

- ✅ Property disputes & inheritance
- ✅ Tenancy & rent control
- ✅ Divorce & family law
- ✅ Consumer rights & contracts
- ✅ Constitutional remedies & writs
- ✅ Child custody
- ✅ Domestic violence
- ✅ Cheque bounce
- ✅ And more...

---

## Tips for Better Answers

1. **Be specific:** "Property dispute" vs. "My neighbor claims my house is his"
2. **Provide context:** Include relevant facts about your case
3. **Use keywords:** Mention specific laws or acts (e.g., "Transfer of Property Act")
4. **Ask procedural:** "How do I file?" gets step-by-step answers
5. **Ask rights-based:** "What are my rights?" gets rights explanation

---

## Debugging

### Check Service Status
```bash
curl http://localhost:8001/health
```

### View API Documentation
- Browser: http://localhost:8001/docs
- Terminal: Check logs for startup messages

### Monitor Logs
```bash
# Watch RAG service logs for errors
tail -f logs/rag_service.log
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Apr 2024 | Initial release |

---

## Contact & Support

- **Documentation:** See DEPLOYMENT_GUIDE.md
- **GitHub Issues:** Report bugs on GitHub
- **Logs:** Check service logs on Render or local terminal

---

**Last Updated:** April 2024  
**Status:** Production Ready ✓
