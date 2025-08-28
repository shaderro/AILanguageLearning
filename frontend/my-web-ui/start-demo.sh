#!/bin/bash

echo "🚀 Starting React + FastAPI Word Definition Demo"
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

echo "📦 Installing frontend dependencies..."
npm install

echo "🐍 Installing backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

echo ""
echo "✅ Dependencies installed successfully!"
echo ""
echo "🔧 To start the demo:"
echo "1. Start the backend: cd backend && python main.py"
echo "2. In a new terminal, start the frontend: npm run dev"
echo ""
echo "🌐 The demo will be available at:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🎉 Happy coding!" 