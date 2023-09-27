@echo off

echo Loading environment variables from .env file...

set "venv_dir=.venv"
set "pretrained_models_dir=pretrained_models"

REM Check if CMake and Python are included in Environmental variables
where cmake > nul 2>&1
where python > nul 2>&1
if %errorlevel% neq 0 (
    echo CMake or Python not found in Environmental variables.
    exit /b 1
)

REM Setting Up Environment
if not exist %venv_dir% (
    python -m venv %venv_dir%
)

REM Activate virtual environment
call %venv_dir%\Scripts\activate
where python

REM Install Python packages
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Verify if pretrained model exists
if not exist %pretrained_models_dir%\*.pth (
    echo Pretrained model not found. Please download the model.
    pause
    exit /b 1
) else (
    echo Pretrained model found.
)

REM Run the Django server
python manage.py runsslserver 125.102.193.61:8000

REM Deactivate virtual environment
deactivate

pause