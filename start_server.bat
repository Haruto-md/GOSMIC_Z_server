REM Are CMake, python included in Environmental variables?
REM Setting Up Environment
python -m venv .venv

REM venv環境の有効化
call .venv\Scripts\activate
where python

REM install python packages
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM verifiy if pretrained model exists
mkdir myapp\modules\vits\pretrained_models
pushd myapp\modules\vits\pretrained_models
if exist "*.pth" (
    echo .pthファイルが存在します
) else (
    echo Please Download model.
    pause
    exit
)
popd

REM Now Starting Server

python manage.py migrate
python manage.py runserver

deactivate
pause
