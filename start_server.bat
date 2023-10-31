@echo off

echo Loading environment variables from .env file...

set "venv_dir=.venv"
set "pretrained_models_dir=pretrained_models"

REM Setting Up Environment
if not exist %venv_dir% (
    python -m venv %venv_dir%
    pause
)

REM Activate virtual environment
call %venv_dir%\Scripts\activate

REM Install Python packages
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Verify if pretrained model exists
if not exist %pretrained_models_dir%\*.pth (
    echo Pretrained model not found. Please download the model.
    pause
) else (
    echo Pretrained model found.
)
where python
python -V
nvidia-smi
nvcc -V
pause
REM Run the Django server
python manage.py runsslserver 10.20.202.158:8000

REM Deactivate virtual environment
deactivate

pause