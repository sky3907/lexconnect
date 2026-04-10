#!/bin/bash

# Start Both Services Locally
# Make sure you have the Python environment set up with all dependencies

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     LexConnect - Start Both Services (Local Development)   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "✗ Python is not installed"
    echo "  Please install Python 3.10+ from https://www.python.org"
    exit 1
fi

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "rag_service" ]; then
    echo "✗ Error: backend or rag_service folder not found"
    echo "  Please run this script from the root directory (lexconnect/)"
    exit 1
fi

echo "✓ Folders found"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
else
    source venv/bin/activate
fi

echo "✓ Virtual environment activated"
echo ""

# Install requirements
echo "📥 Installing RAG Service dependencies..."
pip install -q -r rag_service/requirements.txt
if [ $? -ne 0 ]; then
    echo "✗ Failed to install RAG service dependencies"
    exit 1
fi

echo "✓ RAG Service dependencies installed"
echo ""

echo "📥 Installing Backend Service dependencies..."
pip install -q -r backend/requirements.txt
if [ $? -ne 0 ]; then
    echo "✗ Failed to install Backend dependencies"
    exit 1
fi

echo "✓ Backend dependencies installed"
echo ""

# Create .env files if they don't exist
if [ ! -f "rag_service/.env" ]; then
    cp rag_service/.env.example rag_service/.env
    echo "✓ Created rag_service/.env"
fi

if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "✓ Created backend/.env"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Starting Services...                                      ║"
echo "║  (Using tmux for multiple panes - optional)               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Start RAG Service in background
echo "🚀 Starting RAG Service (http://localhost:8001)..."
(cd rag_service && uvicorn rag_app:app --reload --host 0.0.0.0 --port 8001) &
RAG_PID=$!

# Wait a bit for RAG service to start
sleep 3

# Start Backend Service in background
echo "🚀 Starting Backend Service (http://localhost:8000)..."
(cd backend && uvicorn app:app --reload --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

echo ""
echo "✓ Services are starting up!"
echo ""
echo "🔗 Service URLs:"
echo "   - RAG Service:       http://localhost:8001"
echo "   - Backend API:       http://localhost:8000"
echo "   - Frontend:          http://localhost:3000 (or 5173 with npm run dev)"
echo ""
echo "📚 API Documentation:"
echo "   - RAG Service:       http://localhost:8001/docs"
echo "   - Backend API        http://localhost:8000/docs"
echo ""
echo "⏱ RAG Service Startup: Takes 2-5 minutes to load the model"
echo ""
echo "🛑 To stop services, press Ctrl+C"
echo ""

# Wait for both services
wait $RAG_PID $BACKEND_PID
