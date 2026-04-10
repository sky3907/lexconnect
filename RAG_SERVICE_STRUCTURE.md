# LexConnect - Separate Service Deployment Structure

## 📋 Overview

This document explains the new folder structure for deploying LexConnect as separate microservices on Render. The application has been refactored to split the RAG (Retrieval-Augmented Generation) model inference from the main backend API.

---

## 🏗️ New Folder Structure

```
lexconnect/
├── rag_service/                    # NEW: Separate RAG Service
│   ├── rag_app.py                 # FastAPI app for RAG service
│   ├── rag_slm.py                 # RAG logic (civil law Q&A)
│   ├── local_slm.py               # Local LLM inference (Qwen 3B)
│   ├── legal_ground_truth.py       # Legal facts grounding
│   ├── config_paths_rag.py         # Configuration for RAG service
│   ├── requirements.txt            # RAG-specific dependencies
│   ├── __init__.py
│   ├── .env.example               # Environment variables template
│   └── models/                     # Symlink or copy of models
│
├── backend/                        # Existing backend (MODIFIED)
│   ├── app.py                     # Modified to use RAG service client
│   ├── rag_client.py              # NEW: HTTP client for RAG service
│   ├── database.py
│   ├── intake_agent.py
│   ├── router_agent.py
│   ├── lawyer_agent.py
│   ├── import_lawyers.py
│   ├── requirements.txt           # Updated with httpx
│   ├── .env.example              # Environment variables template
│   └── ...
│
├── frontend/                       # React/Vite app
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   └── ...
│
├── data/                           # Shared data folder
│   ├── faiss_civil.index
│   ├── civil_meta.jsonl
│   ├── civil_chunks.jsonl
│   └── ...
│
├── models/                         # Shared models folder
│   └── qwen2.5-3b-instruct.Q4_K_M.gguf
│
├── render.yaml                     # NEW: Multi-service Render config
├── DEPLOYMENT_GUIDE.md             # NEW: Complete deployment instructions
├── start_services.bat              # NEW: Windows startup script
├── start_services.sh               # NEW: Linux/Mac startup script
├── setup.bat
├── config_paths.py                 # Original config
├── suppress_warnings.py
├── check_lawyers.py
├── QUICK_INTEGRATION.js
├── README.md
└── .gitignore
```

---

## 🔄 Architecture Changes

### Before (Monolithic)
```
Frontend → Backend (Port 8000) → Local RAG Model
           ↓
           Database
```

**Issues:**
- Model loading delays backend startup (2-5 minutes)
- Backend can't scale independently from RAG
- If RAG crashes, entire service fails
- Hard to update RAG separately

### After (Microservices)
```
Frontend → Backend (Port 8000) → RAG Service (Port 8001)
           ↓
           Database
           
RAG Service → FAISS Index + Qwen 3B Model
```

**Benefits:**
- Independent scaling of services
- RAG service can be updated independently
- Better resource management
- Easier to debug issues in isolation
- Can deploy RAG on different hardware if needed

---

## 📦 Key Files Created

### 1. **rag_service/rag_app.py**
- New FastAPI application for RAG service
- Endpoints:
  - `POST /answer` - Get legal answer with retrieval
  - `POST /retrieve` - Retrieve documents without inference
  - `POST /classify` - Classify question type
  - `POST /validate` - Check if question is about civil law
  - `POST /batch-answer` - Process multiple questions
  - `GET /health` - Health check
  - `GET /info` - Service information

### 2. **rag_service/config_paths_rag.py**
- Configuration for RAG service paths
- Points to shared `data/` and `models/` folders
- Allows RAG service to work independently

### 3. **backend/rag_client.py**
- HTTP client for calling RAG service
- Async support for efficient communication
- Handles connection errors gracefully
- Used instead of direct RAG import

### 4. **render.yaml**
- Multi-service deployment configuration
- Defines RAG Service, Backend, and Frontend services
- Specifies build commands, start commands, environment variables
- Can be deployed directly to Render

### 5. **DEPLOYMENT_GUIDE.md**
- Complete step-by-step deployment instructions
- Architecture diagrams
- Environment setup
- Troubleshooting guide

### 6. **start_services.bat / start_services.sh**
- Quick start scripts for local development
- Installs dependencies automatically
- Starts both services
- Shows service URLs and documentation links

### 7. **.env.example files**
- Templates for environment configuration
- Separate for RAG and Backend services
- Copy to `.env` before running

---

## 🚀 How to Use

### Local Development

#### Windows:
```bash
# Just double-click or run from PowerShell
.\start_services.bat
```

#### Linux/Mac:
```bash
# Make script executable
chmod +x start_services.sh

# Run it
./start_services.sh
```

### Manual Start

```bash
# Terminal 1: RAG Service
cd rag_service
python -m pip install -r requirements.txt
uvicorn rag_app:app --reload --host 0.0.0.0 --port 8001

# Terminal 2: Backend API
cd backend
python -m pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Frontend (optional)
cd frontend
npm install
npm run dev
```

### Render Deployment

See `DEPLOYMENT_GUIDE.md` for full instructions. Quick summary:

1. Push to GitHub
2. Create Render services for RAG and Backend
3. Configure environment variables
4. Deploy

---

## 🔧 Modified Files

### backend/app.py
**Change:** RAG is now called via HTTP instead of direct import

**Before:**
```python
from .rag_slm import CivilRAGSLM
rag = CivilRAGSLM()

# In endpoint:
result = rag.answer(payload.message, case_context=ctx)
```

**After:**
```python
from .rag_client import rag_service

# In endpoint:
result = await rag_service.get_answer(payload.message, case_context=ctx)
```

### backend/requirements.txt
**Added:**
- `httpx` - Async HTTP client for calling RAG service

---

## 🌐 Service Communication

### RAG Service Endpoints

#### Get Legal Answer
```bash
POST http://localhost:8001/answer
Content-Type: application/json

{
  "question": "What is a property dispute?",
  "case_context": null
}
```

Response:
```json
{
  "answer": "A property dispute is...",
  "retrieved_count": 3,
  "sources": [...]
}
```

#### Health Check
```bash
GET http://localhost:8001/health
```

### Backend → RAG Service

The backend automatically calls the RAG service when needed. Configuration:

```python
# In rag_client.py
RAG_SERVICE_URL = os.getenv(
    "RAG_SERVICE_URL", 
    "http://localhost:8001"
)
```

Environment variable `RAG_SERVICE_URL` controls the RAG service location.

---

## 📊 Deployment Comparison

| Aspect | Before | After |
|--------|--------|-------|
| **Services** | 1 Monolith | 3 Microservices |
| **Startup Time** | 2-5 min (model load) | Backend: 30s, RAG: 2-5 min |
| **Scaling** | All or nothing | Independent scaling |
| **Updates** | Entire service restart | Individual service updates |
| **Resource Usage** | ~3-4GB RAM single service | Backend: 500MB, RAG: 3GB |
| **Failure Impact** | Total outage | Partial degradation |

---

## 🎯 Next Steps

1. **Test Locally**
   - Run `start_services.bat` (or .sh on Linux/Mac)
   - Test endpoints at `http://localhost:8001/docs` and `http://localhost:8000/docs`

2. **Deploy to Render**
   - Follow `DEPLOYMENT_GUIDE.md`
   - Deploy RAG service first
   - Deploy Backend with correct `RAG_SERVICE_URL`

3. **Monitor**
   - Check service health endpoints
   - Monitor logs on Render dashboard
   - Set up alerts for failures

4. **Scale**
   - Monitor resource usage
   - Increase plan if needed
   - Add more instances for high traffic

---

## ❓ FAQ

**Q: Why separate RAG into its own service?**
A: The RAG model is memory-intensive (2.4GB) and has long startup time. Separating it allows independent scaling and updates.

**Q: Can I keep them on the same instance?**
A: Yes, but you lose the benefits of microservices. For production, separate instances are recommended.

**Q: What if RAG service goes down?**
A: Backend continues working but can't answer legal questions. API can return helpful error messages.

**Q: How much will this cost on Render?**
A: ~$15-45/month depending on plan size. See DEPLOYMENT_GUIDE.md for details.

**Q: Can I use this with Docker?**
A: Yes! Add Dockerfiles for each service and use docker-compose for local dev.

---

## 📝 Notes

- **Data Sharing:** `data/` and `models/` folders must be accessible to both services
- **Model Loading:** Takes 2-5 minutes on first startup (normal)
- **CORS:** Configured to allow frontend communication
- **Health Checks:** Both services have `/health` endpoints

---

## 🔗 Resources

- **Render Documentation:** https://render.com/docs
- **FastAPI:** https://fastapi.tiangolo.com
- **FAISS:** https://github.com/facebookresearch/faiss
- **Qwen Model:** https://github.com/QwenLM/Qwen

---

**Version:** 1.0.0  
**Last Updated:** April 2024  
**Status:** Production Ready ✓
