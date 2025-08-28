# FastAPI Word Backend

A simple FastAPI server that provides word definitions and examples.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

## API Endpoints

- `GET /` - Health check
- `GET /api/word?text=apple` - Get word information

## API Documentation

Once the server is running, visit:
- `http://localhost:8000/docs` - Interactive API documentation (Swagger UI)
- `http://localhost:8000/redoc` - Alternative API documentation

## CORS

CORS is enabled for React development server (`http://localhost:5173`). 