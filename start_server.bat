REM Are CMake, python included in Environmental variables?
REM Setting Up Environment
python -m venv .venv

REM venv activation
call .venv\Scripts\activate
where python

REM install python packages
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM verifiy if pretrained model exists
mkdir pretrained_models
pushd pretrained_models
if exist "*.pth" (
    echo .pth exists already
) else (
    echo Please Download model.
    pause
    exit
)
popd

python manage.py runserver
deactivate
pause