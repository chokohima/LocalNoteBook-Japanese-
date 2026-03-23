@echo off
echo Setup: LocalNotebook
echo.

python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Please install from https://www.python.org/
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

echo Installing packages...
echo.

echo [1/9] fastapi
pip install fastapi

echo [2/9] uvicorn
pip install uvicorn

echo [3/9] httpx
pip install httpx

echo [4/9] python-multipart
pip install python-multipart

echo [5/9] chromadb
pip install chromadb

echo [6/9] pypdf
pip install pypdf

echo [7/9] python-docx  (Word)
pip install python-docx

echo [8/9] openpyxl  (Excel / CSV)
pip install openpyxl

echo [9/9] python-pptx  (PowerPoint)
pip install python-pptx

echo.
echo Done! Run start.bat to launch.
echo.
echo Required Ollama models:
echo   ollama pull gemma3:4b
echo   ollama pull nomic-embed-text
echo.
echo Optional (for image support):
echo   ollama pull llava
echo.
pause
