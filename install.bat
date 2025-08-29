@echo off
echo Installing ...

REM Check if Python is installed
call python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in the PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)
REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    call python -m venv venv
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment...
call %~dp0\venv\Scripts\activate.bat

echo Installing pip and setuptools...
call pip install --upgrade pip setuptools wheel

echo Installing dependencies...
call pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error installing dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

REM Check if config.py exists, if not copy from config_example.py
if not exist config.py (
    if exist config_example.py (
        echo Creating config.py from config_example.py...
        copy config_example.py config.py >nul
        echo Config file created successfully!
    ) else (
        echo Warning: config_example.py not found. You may need to create config.py manually.
    )
) else (
    echo Config file already exists.
)

echo.
echo Installation completed successfully!

echo.
pause
