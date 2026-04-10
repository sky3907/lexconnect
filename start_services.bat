@echo off
REM Start Both Services Locally
REM Make sure you have the Python environment set up with all dependencies

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     LexConnect - Start Both Services (Local Development)   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Python is not installed or not in PATH
    echo   Please install Python 3.10+ from https://www.python.org
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "backend" (
    echo ✗ Error: backend folder not found
    echo   Please run this script from the root directory (lexconnect/)
    pause
    exit /b 1
)

if not exist "rag_service" (
    echo ✗ Error: rag_service folder not found
    echo   Please run this script from the root directory (lexconnect/)
    pause
    exit /b 1
)

echo ✓ Folders found
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
) else (
    call venv\Scripts\activate.bat
)

echo ✓ Virtual environment activated
echo.

REM Install requirements
echo 📥 Installing RAG Service dependencies...
pip install -q -r rag_service/requirements.txt
if %errorlevel% neq 0 (
    echo ✗ Failed to install RAG service dependencies
    pause
    exit /b 1
)

echo ✓ RAG Service dependencies installed
echo.

echo 📥 Installing Backend Service dependencies...
pip install -q -r backend/requirements.txt
if %errorlevel% neq 0 (
    echo ✗ Failed to install Backend dependencies
    pause
    exit /b 1
)

echo ✓ Backend dependencies installed
echo.

REM Create .env files if they don't exist
if not exist "rag_service\.env" (
    copy rag_service\.env.example rag_service\.env
    echo ✓ Created rag_service\.env
)

if not exist "backend\.env" (
    copy backend\.env.example backend\.env
    echo ✓ Created backend\.env
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  Starting Services...                                      ║
echo ║  (This will open two terminal windows)                     ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Start RAG Service in a new window
echo 🚀 Starting RAG Service (http://localhost:8001)...
start "LexConnect - RAG Service" cmd /k "cd rag_service && uvicorn rag_app:app --reload --host 0.0.0.0 --port 8001"

REM Wait a bit for RAG service to start
timeout /t 3 /nobreak

REM Start Backend Service in a new window
echo 🚀 Starting Backend Service (http://localhost:8000)...
start "LexConnect - Backend API" cmd /k "cd backend && uvicorn app:app --reload --host 0.0.0.0 --port 8000"

echo.
echo ✓ Services are starting up!
echo.
echo 🔗 Service URLs:
echo   - RAG Service:       http://localhost:8001
echo   - Backend API:       http://localhost:8000
echo   - Frontend:          http://localhost:3000 (or 5173 with npm run dev)
echo.
echo 📚 API Documentation:
echo   - RAG Service:       http://localhost:8001/docs
echo   - Backend API:       http://localhost:8000/docs
echo.
echo ⏱ RAG Service Startup: Takes 2-5 minutes to load the model
echo.
echo Press ENTER to close this window (services will keep running)
pause
