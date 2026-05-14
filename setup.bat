@echo off
REM Quick setup script for Medicine Identifier (Windows)

echo.
echo Medicine Identifier - Setup Script (Windows)
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo ✓ Python found
python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ✓ Setup complete!
echo.
echo Next steps:
echo 1. Place 'Medicine_Details.csv' in the 'data\' folder
echo 2. Run: python scripts\rag_ingest.py
echo 3. Run: python app.py
echo 4. Open: http://localhost:5000
echo.
pause
