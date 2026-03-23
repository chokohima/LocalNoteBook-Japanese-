@echo off
echo ========================================
echo   LocalNotebook
echo ========================================
echo.
echo Starting server on http://localhost:8765
echo Open index.html in your browser.
echo Press Ctrl+C to stop.
echo ----------------------------------------

start "" /b cmd /c "timeout /t 3 > nul && start "" "%~dp0index.html""

python "%~dp0server.py"
pause
