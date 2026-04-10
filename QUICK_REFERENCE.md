# LexConnect Deployment - Quick Reference Guide

## 🚀 Quick Start (Local Development)

### Windows
```bash
# Just run this one command:
.\start_services.bat

# Everything starts automatically
# Services will be available at:
#   RAG:     http://localhost:8001
#   Backend: http://localhost:8000
#   API Docs: http://localhost:8001/docs
```

### Linux/Mac
```bash
# Make executable and run:
chmod +x start_services.sh
./start_services.sh
```

---

## 📚 Documentation Map

| Document | Purpose | Who Should Read |
|----------|---------|-----------------|
| **DEPLOYMENT_GUIDE.md** | Step-by-step deployment | DevOps Engineers |
| **RAG_SERVICE_STRUCTURE.md** | Architecture overview | Developers |
| **RAG_SERVICE_API_REFERENCE.md** | API endpoints | Developers, QA |
| **DEPLOYMENT_CHECKLIST.md** | Verification tasks | DevOps/QA |
| **CHANGES_SUMMARY.md** | What changed | Developers |
| **This File** | Quick reference | Everyone |

---

## 🔧 Manual Service Startup

### Terminal 1: RAG Service
```bash
cd rag_service
pip install -r requirements.txt
uvicorn rag_app:app --reload --port 8001
```

### Terminal 2: Backend API
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

### Terminal 3: Frontend (Optional)
```bash
cd frontend
npm install
npm run dev
```

---

## 🌐 Testing Endpoints

### Health Check
```bash
# RAG Service
curl http://localhost:8001/health

# Backend
curl http://localhost:8000/
```

### Get Legal Answer
```bash
curl -X POST http://localhost:8001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is a property dispute?",
    "case_context": null
  }'
```

### Retrieve Documents
```bash
curl -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "property dispute"}'
```

### Interactive API Docs
- **RAG Service:** http://localhost:8001/docs
- **Backend:** http://localhost:8000/docs

---

## 📦 Deploy to Render

### Step 1: Deploy RAG Service
1. Go to https://render.com
2. Create "Web Service"
3. Select Python 3.10
4. **Build:** `pip install -r rag_service/requirements.txt`
5. **Start:** `cd rag_service && uvicorn rag_app:app --host 0.0.0.0 --port 8001`
6. Deploy → Wait 5-10 minutes → Note the URL

### Step 2: Deploy Backend Service
1. Create another "Web Service"
2. Select Python 3.10
3. **Build:** `pip install -r backend/requirements.txt`
4. **Start:** `cd backend && uvicorn app:app --host 0.0.0.0 --port 8000`
5. **Environment Variables:**
   ```
   RAG_SERVICE_URL=https://lexconnect-rag-service.onrender.com
   DATABASE_URL=sqlite:///./lexconnect.db
   SECRET_KEY=<generate-random-key>
   CORS_ORIGINS=your-frontend-domain.com
   ```
6. Deploy

### Step 3: Test
```bash
# Test RAG Service
curl https://lexconnect-rag-service.onrender.com/health

# Test Backend
curl https://lexconnect-backend.onrender.com/

# Test Integration
curl -X POST https://lexconnect-backend.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"property dispute"}'
```

---

## 🐳 Using Docker

```bash
# Build and start all services
docker-compose up

# Services available at:
#   RAG:     http://localhost:8001
#   Backend: http://localhost:8000
#   Frontend: http://localhost:5173

# Stop services
docker-compose down
```

---

## 📋 Environment Files

### Create .env for RAG Service
```bash
cd rag_service
cp .env.example .env
# Edit .env if needed
```

### Create .env for Backend
```bash
cd backend
cp .env.example .env
# Edit .env with your values
```

---

## 🔍 Debugging Tips

### Check RAG Service Status
```bash
# Health check
curl http://localhost:8001/health

# Service info
curl http://localhost:8001/info

# Check logs (in terminal where you started it)
# Should see FAISS index loaded message
```

### Check Backend Status
```bash
# Health check
curl http://localhost:8000/

# API documentation
# Visit http://localhost:8000/docs
```

### Common Issues

**RAG Service takes forever to load:**
- Normal! Model loading takes 2-5 minutes
- Check logs for "FAISS index loaded" message

**Backend can't connect to RAG:**
- Verify RAG_SERVICE_URL is correct
- Check RAG service is running
- Test: `curl RAG_SERVICE_URL/health`

**Out of memory errors:**
- Need at least 3GB RAM for model
- Close other applications
- Upgrade Render plan if on cloud

---

## 🔗 Key URLs (Local Development)

| Service | URL | Purpose |
|---------|-----|---------|
| RAG Service | http://localhost:8001 | Health check |
| RAG API Docs | http://localhost:8001/docs | Interactive API |
| Backend | http://localhost:8000 | Health check |
| Backend API Docs | http://localhost:8000/docs | Interactive API |
| Frontend | http://localhost:3000 | App (npm dev) |
| Frontend (Vite) | http://localhost:5173 | App (vite preview) |

---

## 🔗 Key URLs (Production Render)

```
RAG Service: https://lexconnect-rag-service.onrender.com
Backend:     https://lexconnect-backend.onrender.com
Frontend:    https://lexconnect-frontend.onrender.com
```

---

## 📊 Service Architecture

```
User/Frontend
    ↓
Backend API (8000)
    ├─ Database operations
    ├─ Auth & user management
    └─ → HTTP Request → RAG Service (8001)
                            ├─ FAISS search
                            ├─ Embeddings
                            └─ LLM inference
                         ← Response ←
Response
```

---

## 🛠️ Common Commands

### Install Dependencies
```bash
# For RAG Service
cd rag_service && pip install -r requirements.txt

# For Backend
cd backend && pip install -r requirements.txt

# For Frontend
cd frontend && npm install
```

### Run Tests
```bash
# Test RAG endpoint
curl http://localhost:8001/answer -H "Content-Type: application/json" \
  -d '{"question":"What is property?"}'

# Test Backend endpoint
curl http://localhost:8000/

# Test specific endpoint
curl http://localhost:8001/docs  # Check interactive docs
```

### View Logs
```bash
# You should see logs in terminal where services are running
# RAG should show "FAISS index loaded: XXXX vectors"
# Check for any errors
```

---

## 🚨 Emergency Procedures

### Stop Services
```
Windows: Press Ctrl+C in each terminal window
Linux/Mac: Press Ctrl+C in the terminal
Docker: docker-compose down
```

### Restart Services
```bash
# Windows
.\start_services.bat

# Linux/Mac
./start_services.sh

# Docker
docker-compose down && docker-compose up
```

### Reset Everything
```bash
# Remove virtual environment (local)
rm -rf venv

# Docker cleanup
docker-compose down --volumes
docker system prune

# Then restart normally
```

---

## 🎯 Quick Verification

**Before going to production, verify:**

- [ ] `http://localhost:8001/health` returns status: healthy
- [ ] `http://localhost:8000/` returns welcome message
- [ ] `http://localhost:8001/docs` shows API documentation
- [ ] RAG Service answer endpoint responds with legal answer
- [ ] Backend can communicate with RAG Service
- [ ] Frontend can communicate with Backend

---

## 💡 Tips & Tricks

### Speed Up Local Development
```bash
# Skip dependency installation if already done
# Just start services directly:
cd rag_service && uvicorn rag_app:app --reload --port 8001
```

### Test Different Questions
```bash
# JSON format for copying-pasting
{
  "question": "What is property dispute?",
  "case_context": null
}
```

### Monitor Service Performance
```bash
# In another terminal, monitor resources
# Windows: Task Manager (Ctrl+Shift+Esc)
# Linux: top or htop
# Mac: Activity Monitor
```

---

## 📞 Help & Support

### Find Documentation
- Main guide: **DEPLOYMENT_GUIDE.md**
- API reference: **RAG_SERVICE_API_REFERENCE.md**
- Architecture: **RAG_SERVICE_STRUCTURE.md**
- Checklist: **DEPLOYMENT_CHECKLIST.md**

### Test Endpoints
1. Open http://localhost:8001/docs
2. Click "Try it out" on any endpoint
3. Fill in request body
4. Click "Execute"

### Check Logs
- Look in the terminal where you started services
- Should see startup messages and any errors
- RAG service should show model loading progress

---

## 🎓 Learning Path

1. **Start:** `start_services.bat` (or .sh)
2. **Explore:** Open `/docs` endpoints
3. **Test:** Use curl examples above
4. **Understand:** Read RAG_SERVICE_STRUCTURE.md
5. **Deploy:** Follow DEPLOYMENT_GUIDE.md
6. **Monitor:** Use DEPLOYMENT_CHECKLIST.md

---

## 📋 Checklist Before Deployment

- [ ] All services start without errors locally
- [ ] Health endpoints respond correctly
- [ ] RAG service returns legal answers
- [ ] Backend service can call RAG service
- [ ] All 21 new files are in the repository
- [ ] .env.example files are present
- [ ] Git LFS configured for large files (or use cloud storage)
- [ ] Render account created
- [ ] GitHub connected to Render
- [ ] All documentation reviewed

---

## ⚡ Performance Expectations

| Operation | Time |
|-----------|------|
| RAG Service Startup | 2-5 minutes (model loading) |
| Backend Service Startup | 30 seconds |
| FAISS Document Search | ~50ms |
| LLM Inference | 1-2 seconds |
| Total Answer Time | 1-3 seconds |

---

**Version:** 1.0.0  
**Last Updated:** April 2024  
**Status:** Quick Reference ✓

For detailed information, see the main documentation files listed above.
