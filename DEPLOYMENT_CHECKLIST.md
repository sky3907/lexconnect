# LexConnect Deployment Preparation Checklist

## Pre-Deployment Checklist

### 1. Local Testing
- [ ] Clone/download the updated repository
- [ ] Run `start_services.bat` (Windows) or `start_services.sh` (Linux/Mac)
- [ ] Verify RAG service starts successfully at `http://localhost:8001`
- [ ] Verify Backend service starts successfully at `http://localhost:8000`
- [ ] Test API endpoints:
  - [ ] GET `http://localhost:8001/health`
  - [ ] GET `http://localhost:8000/`
  - [ ] POST `http://localhost:8001/answer` with test question
  - [ ] POST `http://localhost:8000/chat` with test message

### 2. Code Review
- [ ] Review new files in `rag_service/` directory
- [ ] Check `backend/rag_client.py` for HTTP client implementation
- [ ] Verify `render.yaml` configuration
- [ ] Confirm `DEPLOYMENT_GUIDE.md` is complete and accurate

### 3. Repository Preparation
- [ ] Add new files to Git:
  ```bash
  git add rag_service/
  git add backend/rag_client.py
  git add render.yaml
  git add DEPLOYMENT_GUIDE.md
  git add RAG_SERVICE_STRUCTURE.md
  git add start_services.bat
  git add start_services.sh
  git add docker-compose.yml
  git add rag_service/Dockerfile
  git add backend/Dockerfile
  ```
- [ ] Commit changes:
  ```bash
  git commit -m "feat: Separate RAG service for independent deployment"
  ```
- [ ] Push to GitHub:
  ```bash
  git push origin main
  ```

### 4. Data & Model Management
- [ ] Check if large files (model, FAISS index) are tracked:
  * [ ] If using Git LFS:
    ```bash
    git lfs install
    git lfs track "models/*.gguf"
    git lfs track "data/*.index"
    git add .gitattributes
    git commit -m "chore: Configure Git LFS for large files"
    git push
    ```
  * [ ] Otherwise, prepare to upload to cloud storage (S3, GCS, etc.)

### 5. Environment Configuration
- [ ] Create `.env` files locally:
  - [ ] Copy `rag_service/.env.example` to `rag_service/.env`
  - [ ] Copy `backend/.env.example` to `backend/.env`
- [ ] Update local `.env` values if needed

### 6. Database Setup (if needed)
- [ ] Decide on database type (SQLite for dev, PostgreSQL for production)
- [ ] If using PostgreSQL:
  - [ ] Create Render PostgreSQL database
  - [ ] Note the connection string
  - [ ] Update backend requirements.txt with PostgreSQL driver

---

## Render Deployment Checklist

### Step 1: Create Render Account
- [ ] Go to https://render.com
- [ ] Sign up or log in
- [ ] Link your GitHub account
- [ ] Create new project

### Step 2: Deploy RAG Service First
- [ ] Create new "Web Service" on Render
- [ ] Connect GitHub repository
- [ ] Configure service:
  - [ ] Name: `lexconnect-rag-service`
  - [ ] Runtime: Python 3.10
  - [ ] Build Command:
    ```
    pip install -r rag_service/requirements.txt
    ```
  - [ ] Start Command:
    ```
    cd rag_service && uvicorn rag_app:app --host 0.0.0.0 --port 8001
    ```
  - [ ] Select appropriate plan (Standard or higher for model)
- [ ] Deploy and wait for success
- [ ] Note the URL (e.g., `https://lexconnect-rag-service.onrender.com`)
- [ ] Test health endpoint:
  ```bash
  curl https://lexconnect-rag-service.onrender.com/health
  ```
- [ ] Wait for RAG model to load (2-5 minutes in logs)

### Step 3: Deploy Backend Service
- [ ] Create new "Web Service" on Render
- [ ] Connect to same GitHub repository
- [ ] Configure service:
  - [ ] Name: `lexconnect-backend`
  - [ ] Runtime: Python 3.10
  - [ ] Build Command:
    ```
    pip install -r backend/requirements.txt
    ```
  - [ ] Start Command:
    ```
    cd backend && uvicorn app:app --host 0.0.0.0 --port 8000
    ```
  - [ ] Select appropriate plan (Standard)
- [ ] Configure Environment Variables:
  - [ ] `RAG_SERVICE_URL`: `https://lexconnect-rag-service.onrender.com`
  - [ ] `DATABASE_URL`: (PostgreSQL URL or leave empty for SQLite)
  - [ ] `SECRET_KEY`: Generate a strong random key
  - [ ] `CORS_ORIGINS`: (Your frontend URL when ready)
- [ ] Deploy
- [ ] Test health endpoint:
  ```bash
  curl https://lexconnect-backend.onrender.com/
  ```

### Step 4: Deploy Frontend (Optional)
- [ ] Create new "Web Service" on Render
- [ ] Connect to same GitHub repository
- [ ] Configure service:
  - [ ] Name: `lexconnect-frontend`
  - [ ] Runtime: Node
  - [ ] Build Command:
    ```
    cd frontend && npm install && npm run build
    ```
  - [ ] Start Command:
    ```
    cd frontend && npm run preview
    ```
- [ ] Configure Environment Variables:
  - [ ] `VITE_API_BASE_URL`: `https://lexconnect-backend.onrender.com`
- [ ] Deploy

### Step 5: Verify All Services
- [ ] Check RAG service logs for model loading success
- [ ] Check Backend service logs for successful startup
- [ ] Check Frontend service logs for build success
- [ ] Test cross-service communication:
  ```bash
  # Test RAG or ask
  curl -X POST https://lexconnect-backend.onrender.com/chat \
    -H "Content-Type: application/json" \
    -d '{"message":"What is property dispute?","use_case_context":false}'
  ```

---

## Monitoring Checklist (Post-Deployment)

### Week 1
- [ ] Monitor service logs daily
- [ ] Check for any errors or warnings
- [ ] Test API endpoints from frontend
- [ ] Monitor resource usage (CPU, memory)

### Ongoing
- [ ] Set up alerts for service failures
- [ ] Monitor response times
- [ ] Review logs weekly
- [ ] Plan scaling if needed

---

## Troubleshooting Checklist

### RAG Service Issues
- [ ] Check logs for model loading errors
- [ ] Verify `RAG_SERVICE_URL` is correct
- [ ] Ensure FAISS index file exists
- [ ] Check available memory (needs ~3GB)
- [ ] Verify Python version (3.10)
- [ ] Check dependencies installed correctly

### Backend Service Issues
- [ ] Verify `RAG_SERVICE_URL` environment variable
- [ ] Check RAG service is running and healthy
- [ ] Verify CORS origin is correct
- [ ] Check database connection if using PostgreSQL
- [ ] Review application logs for errors

### Communication Issues
- [ ] Ping RAG service `/health` endpoint from Backend service logs
- [ ] Check network connectivity between services
- [ ] Verify firewall rules (if applicable)
- [ ] Check service URLs in environment variables

---

## Rollback Checklist

If something goes wrong:

### Option 1: Redeploy Previous Version
- [ ] In Render dashboard, go to Deploy History
- [ ] Select previous working deployment
- [ ] Click "Redeploy"
- [ ] Monitor logs for successful startup

### Option 2: Git Rollback
```bash
# Find last working commit
git log --oneline -5

# Revert to previous commit
git revert <commit-hash>
git push origin main

# Render will auto-redeploy
```

---

## Performance Baseline (for comparison)

After successful deployment, record these baselines:

- [ ] RAG Service startup time: _____ seconds
- [ ] Backend Service startup time: _____ seconds
- [ ] RAG answer API response time: _____ ms
- [ ] Backend chat endpoint response time: _____ ms
- [ ] Frontend page load time: _____ ms

Monitor these metrics weekly to detect degradation.

---

## Security Checklist

- [ ] Change `SECRET_KEY` from default value
- [ ] Set `CORS_ORIGINS` to specific domains only
- [ ] Enable HTTPS (Render does this automatically)
- [ ] Review database credentials in `DATABASE_URL`
- [ ] Set up rate limiting if needed
- [ ] Monitor access logs for suspicious activity
- [ ] Keep dependencies updated

---

## Documentation Checklist

- [ ] Update README.md with new architecture
- [ ] Document environment variables needed
- [ ] Create runbooks for common operations
- [ ] Document troubleshooting steps
- [ ] Add architecture diagrams
- [ ] Create team documentation for maintenance

---

## Final Verification

Before declaring deployment complete:

- [ ] [ ] All three services are running and healthy
- [ ] [ ] Cross-service communication works
- [ ] [ ] Frontend can reach backend API
- [ ] [ ] Backend can reach RAG service
- [ ] [ ] CORS is configured correctly
- [ ] [ ] Authentication works
- [ ] [ ] Database operations work (if applicable)
- [ ] [ ] Logs are clean (no critical errors)
- [ ] [ ] Performance meets expectations
- [ ] [ ] Backup/restore plan is documented

---

## Sign-Off

- **Deployed by:** _________________ Date: _______
- **Verified by:** _________________ Date: _______
- **Go-live approved:** ____________ Date: _______

---

## Notes

Use this space for any additional notes or issues encountered:

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

---

**Document Version:** 1.0  
**Last Updated:** April 2024
