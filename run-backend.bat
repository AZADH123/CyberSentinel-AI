@echo off
echo Starting CyberSentinel AI Backend...
cd /d "%~dp0backend"
if exist "..\.venv\Scripts\activate.bat" (
    call "..\.venv\Scripts\activate.bat"
)
python -c "import _ssl" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set "PATH=C:\Users\hp\AppData\Local\Programs\Python\Python312;C:\Users\hp\AppData\Local\Programs\Python\Python312\Scripts;%PATH%"
)
python -m uvicorn cybersentinel.api.main:app --host 0.0.0.0 --port 8000 --reload
pause
