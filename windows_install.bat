@echo off
pip install pip --upgrade
pip install -r requirements.txt --upgrade
pip install PyQt4-4.11.4-cp27-cp27m-win32.whl
echo Write the password
set /p input=""
cls
echo {"WS_PASSWORD":"%input%"} > .env.json
