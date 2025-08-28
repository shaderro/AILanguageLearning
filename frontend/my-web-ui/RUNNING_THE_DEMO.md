# 🚀 How to Run the Demo

## ✅ Current Status
Both services are now running successfully!

- **Backend (FastAPI)**: http://localhost:8000 ✅
- **Frontend (React)**: http://localhost:5173 ✅

## 🌐 Access the Demo

1. **Open your web browser**
2. **Go to**: http://localhost:5173
3. **You should see**: The Word Definition API Demo with 4 word cards (apple, banana, orange, grape)

## 🔧 Manual Setup (for future reference)

### Step 1: Install Dependencies

```bash
# Frontend dependencies (already installed)
npm install

# Backend dependencies (using virtual environment)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

### Step 2: Start the Backend

```bash
cd backend
source venv/bin/activate
python main.py
```

You should see:
```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 3: Start the Frontend (in a new terminal)

```bash
npm run dev
```

You should see:
```
  VITE v7.1.2  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## 🧪 Test the API

You can test the backend API directly:

```bash
# Test the root endpoint
curl http://localhost:8000/

# Test the word endpoint
curl "http://localhost:8000/api/word?text=apple"
```

## 📚 API Documentation

Once the backend is running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 🎯 What You Should See

1. **4 Word Cards**: apple, banana, orange, grape
2. **Loading Animation**: Each card shows a skeleton loader while fetching data
3. **Word Information**: Definition and example for each word
4. **Responsive Design**: Cards adapt to different screen sizes

## 🔍 Debugging

### If the frontend shows errors:
1. Check that the backend is running on port 8000
2. Open browser dev tools (F12) and check the Console tab
3. Look for CORS errors or network issues

### If the backend won't start:
1. Make sure you're in the virtual environment: `source venv/bin/activate`
2. Check that all dependencies are installed: `pip list`
3. Try a different port if 8000 is busy

## 🛑 Stopping the Services

- **Backend**: Press `Ctrl+C` in the backend terminal
- **Frontend**: Press `Ctrl+C` in the frontend terminal

## 🎉 Success!

You now have a working React + FastAPI integration with:
- ✅ CORS properly configured
- ✅ Real-time API communication
- ✅ Beautiful UI with TailwindCSS
- ✅ Error handling and loading states 