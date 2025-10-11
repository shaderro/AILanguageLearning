@echo off
chcp 65001
echo Starting FastAPI server...
echo.
echo Once started, you can access:
echo - Swagger UI: http://localhost:8001/docs
echo - API Health: http://localhost:8001/api/health
echo.
python server.py

