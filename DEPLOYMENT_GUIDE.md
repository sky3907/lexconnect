# LexConnect Separate Deployment Guide for Render

## Overview

This guide shows how to deploy the LexConnect application as two separate microservices on Render:

1. **RAG Model Service** (Port 8001) - Handles document retrieval and LLM inference
2. **Backend API Service** (Port 8000) - Handles business logic, database, and client requests
3. **Frontend Service** (Optional) - React/Vite application

This separation allows:
- Independent scaling of RAG and API services
- Easier maintenance and updates
- Better resource management
- Microservice architecture benefits

---

## Architecture Diagram

```
┌─────────────────────┐
│   Frontend App      │
│   (React/Vite)      │
│   Port: 3000/5173   │
└──────────┬──────────┘
           │
           │ HTTP/REST API calls
           │
┌──────────▼──────────────────────────────────────────────────────┐
│                    Backend API Service                           │
│                   (FastAPI)  Port: 8000                          │
│  - User authentication & registration                            │
│  - Case management                                               │
│  - Lawyer matching & recommendations                             │
│  - Database operations                                           │
│  - Message handling                                              │
└──────────┬──────────────────────────────────────────────────────┘
           │
           │ HTTP/REST calls to RAG service
           │
┌──────────▼──────────────────────────────────────────────────────┐
│                  RAG Model Service                               │
│               (FastAPI) Port: 8001                               │
│  - FAISS vector search                                           │
│  - Semantic document retrieval                                   │
│  - Qwen2.5 3B LLM inference                                      │
│  - Legal answer generation                                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Prepare Your Repository

### Option A: Using Monorepo (Recommended)

Your current structure is already suited for this:

```
lexconnect/
├── backend/                 # Backend API service
│   ├── app.py
│   ├── requirements.txt
│   ├── rag_client.py       # NEW: Client for RAG service
│   └── ...
├── rag_service/            # NEW: Separate RAG service
│   ├── rag_app.py          # NEW: RAG service main app
│   ├── rag_slm.py
│   ├── local_slm.py
│   ├── legal_ground_truth.py
│   ├── config_paths_rag.py
│   ├── requirements.txt
│   └── ...
├── frontend/               # Frontend (optional for Render)
│   ├── package.json
│   ├── vite.config.js
│   └── ...
├── data/                   # Shared data folder
│   ├── faiss_civil.index
│   ├── civil_meta.jsonl
│   └── ...
├── models/                 # Shared models folder
│   └── qwen2.5-3b-instruct.Q4_K_M.gguf
└── render.yaml             # NEW: Render multi-service config
```

### Option B: Separate Repositories

If you prefer separate repositories on GitHub:

1. **lexconnect-backend** - Contains only the `backend/` folder
2. **lexconnect-rag-service** - Contains the `rag_service/` folder plus shared data & models

---

## Step 2: Update Backend Configuration

The backend has been modified to call the RAG service via HTTP instead of using it locally.

### Key Changes in `backend/app.py`:

**BEFORE (Local RAG):**
```python
from .rag_slm import CivilRAGSLM
rag = CivilRAGSLM()

@app.post("/chat")
def chat(payload: ChatInput, db: Session = Depends(get_db)):
    result = rag.answer(payload.message, case_context=ctx)
```

**AFTER (Remote RAG Service):**
```python
from .rag_client import rag_service

@app.post("/chat")
async def chat(payload: ChatInput, db: Session = Depends(get_db)):
    result = await rag_service.get_answer(payload.message, case_context=ctx)
```

---

## Step 3: Create Render Account & Project Setup

### 3.1 Create Render Services

1. Go to https://render.com and sign in/create account
2. Create a new "Web Service"
3. Connect your GitHub repository

### 3.2 Deploy RAG Service First

**Service Details:**
- **Name:** `lexconnect-rag-service`
- **Runtime:** Python
- **Python Version:** 3.10
- **Build Command:**
  ```bash
  pip install -r rag_service/requirements.txt
  ```
- **Start Command:**
  ```bash
  cd rag_service && uvicorn rag_app:app --host 0.0.0.0 --port 8001
  ```
- **Plan:** Standard or Starter
- **Environment Variables:** (optional for RAG service)
  ```
  PYTHON_VERSION=3.10
  PORT=8001
  ```

**Important Notes:**
- Keep RAG service URL for next step (will be like `https://lexconnect-rag-service.onrender.com`)
- RAG service startup takes longer (model loading: 2-5 minutes)
- Ensure sufficient RAM (minimum 2GB recommended for the model)

### 3.3 Deploy Backend Service

**Service Details:**
- **Name:** `lexconnect-backend`
- **Runtime:** Python
- **Python Version:** 3.10
- **Build Command:**
  ```bash
  pip install -r backend/requirements.txt
  ```
- **Start Command:**
  ```bash
  cd backend && uvicorn app:app --host 0.0.0.0 --port 8000
  ```
- **Plan:** Standard
- **Environment Variables:**
  ```
  PYTHON_VERSION=3.10
  PORT=8000
  RAG_SERVICE_URL=https://lexconnect-rag-service.onrender.com
  DATABASE_URL=<your-postgresql-url>
  CORS_ORIGINS=https://lexconnect-frontend.onrender.com,http://localhost:3000
  SECRET_KEY=<generate-a-strong-secret-key>
  ```

### 3.4 Deploy Frontend Service (Optional)

**Service Details:**
- **Name:** `lexconnect-frontend`
- **Runtime:** Node
- **Build Command:**
  ```bash
  cd frontend && npm install && npm run build
  ```
- **Start Command:**
  ```bash
  cd frontend && npm run preview
  ```
- **Environment Variables:**
  ```
  VITE_API_BASE_URL=https://lexconnect-backend.onrender.com
  NODE_ENV=production
  ```

---

## Step 4: Shared Data & Model Management

### Critical Issue: Shared Large Files

The FAISS index and model file are large:
- `faiss_civil.index` - ~100+ MB
- `qwen2.5-3b-instruct.Q4_K_M.gguf` - ~2.4 GB

**Solutions:**

#### Option A: Use GitHub LFS (Recommended)
```bash
# Initialize Git LFS
git lfs install

# Track large files
git lfs track "models/*.gguf"
git lfs track "data/*.index"

# Commit and push
git add .gitattributes
git commit -m "Configure Git LFS"
git push
```

#### Option B: Store on External Cloud Storage
1. Upload model and data to AWS S3, Google Cloud Storage, or similar
2. Modify `config_paths_rag.py` and `config_paths.py` to download on startup:

```python
import os
import urllib.request

def ensure_model_exists():
    model_path = ROOT_DIR / "models" / "qwen2.5-3b-instruct.Q4_K_M.gguf"
    if not model_path.exists():
        os.makedirs(model_path.parent, exist_ok=True)
        print("Downloading model from cloud storage...")
        urllib.request.urlretrieve(
            "https://your-storage-bucket/qwen2.5-3b-instruct.Q4_K_M.gguf",
            str(model_path)
        )
        print("✓ Model downloaded")
```

#### Option C: Use Render's Persistent Disk
- Attach persistent disk to RAG service
- Store model and FAISS index on disk
- Path: `/mnt/data/faiss_civil.index`

---

## Step 5: Add Health Checks

The RAG service includes health check endpoints. Monitor their status:

```bash
# Check RAG Service Health
curl https://lexconnect-rag-service.onrender.com/health

# Check Backend Service Health  
curl https://lexconnect-backend.onrender.com/

# Retrieve documents from RAG
curl -X POST https://lexconnect-rag-service.onrender.com/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "What is property dispute?"}'
```

---

## Step 6: Environment Variables Checklist

### RAG Service (.env or Render Environment)
```
PYTHON_VERSION=3.10
PORT=8001
```

### Backend Service
```
PYTHON_VERSION=3.10
PORT=8000
RAG_SERVICE_URL=https://lexconnect-rag-service.onrender.com
DATABASE_URL=postgresql://user:password@host:5432/lexconnect
SECRET_KEY=your-super-secret-key-here
CORS_ORIGINS=https://lexconnect-frontend.onrender.com,http://localhost:3000
```

### Frontend Service
```
VITE_API_BASE_URL=https://lexconnect-backend.onrender.com
NODE_ENV=production
```

---

## Step 7: Database Setup (Optional)

If using PostgreSQL on Render:

1. Create a PostgreSQL service on Render
2. Get the connection string
3. Add to Backend's `DATABASE_URL` environment variable
4. Run initial migrations:

```bash
python backend/database.py  # or your migration tool
```

---

## Step 8: Testing the Deployment

### Test RAG Service
```bash
curl -X POST https://lexconnect-rag-service.onrender.com/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is a property dispute?",
    "case_context": null
  }'
```

### Test Backend → RAG Service Communication
```bash
curl -X POST https://lexconnect-backend.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is a property dispute?",
    "use_case_context": false,
    "case_id": null
  }'
```

---

## Step 9: Monitoring & Debugging

### View Logs
On Render dashboard:
- Click on each service
- Go to "Logs" tab
- Monitor startup and runtime logs

### Common Issues

**RAG Service takes too long to start:**
- Model loading takes 2-5 minutes - this is normal
- Increase Render build timeout if needed

**Backend can't connect to RAG service:**
- Verify `RAG_SERVICE_URL` environment variable
- Check RAG service is healthy: `/health` endpoint
- Check CORS settings

**Out of memory errors:**
- Increase Render plan (upgrade to Higher tier)
- Reduce number of instances
- Use persistent disk for model file

---

## Step 10: Scaling Considerations

### RAG Service (Heavy on Memory & CPU)
- Run 1 instance (model is heavy)
- Use Standard or larger plan
- Monitor memory usage

### Backend Service (Light to Medium)
- Can scale to 2-3 instances for high traffic
- Use Standard plan minimum
- Database connection pooling recommended

### Frontend (Very Light)
- Can scale to 2+ instances
- Starter plan is usually sufficient

---

## Step 11: Cost Optimization

**Render Pricing (as of 2024):**
- **Starter Plan:** ~$7/month per service
- **Standard Plan:** ~$15/month per service
- **Auto-scaling:** Additional cost per extra instance

**Cost for 3 services:**
- Minimum: ~$21/month (3 × Starter)
- Recommended: ~$45/month (RAG + Backend + Frontend on Standard)

**Ways to Optimize:**
1. Use Starter plan for Frontend
2. Scale RAG service only when needed
3. Use background jobs for non-critical tasks
4. Cache frequent requests

---

## Next Steps

1. **Prepare repository** with the new structure
2. **Deploy RAG service** first
3. **Deploy backend** with correct RAG service URL
4. **Test communication** between services
5. **Deploy frontend** (if using Render)
6. **Set up monitoring** and alerts
7. **Configure CI/CD** for automatic deployments

---

## Support & Resources

- **Render Docs:** https://render.com/docs
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/
- **FAISS Documentation:** https://github.com/facebookresearch/faiss
- **Qwen Model:** https://github.com/QwenLM/Qwen

---

**Last Updated:** April 2024
**Status:** Ready for Deployment ✓
