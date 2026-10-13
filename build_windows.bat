@echo off
setlocal
cd /d "%~dp0"

py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo Python 3.12 nao encontrado. Instale o Python 3.12 para Windows e execute este script novamente.
    exit /b 1
)

py -3.12 -m pip install --only-binary=:all: -r requirements.txt pyinstaller
if errorlevel 1 goto :error

py -3.12 -m PyInstaller --noconfirm --clean --onefile --name ValeVerde main.py
if errorlevel 1 goto :error

if exist "dist\ValeVerde" rmdir /S /Q "dist\ValeVerde"
mkdir "dist\ValeVerde"
copy /Y "dist\ValeVerde.exe" "dist\ValeVerde\ValeVerde.exe" >nul
if errorlevel 1 goto :error
xcopy /E /I /Y "assets\characters" "dist\ValeVerde\assets\characters" >nul
if errorlevel 1 goto :error
xcopy /E /I /Y "assets\tileset" "dist\ValeVerde\assets\tileset" >nul
if errorlevel 1 goto :error
xcopy /E /I /Y "sounds" "dist\ValeVerde\sounds" >nul
if errorlevel 1 goto :error
powershell -NoProfile -Command "Compress-Archive -Path 'dist\ValeVerde' -DestinationPath 'dist\ValeVerde-Windows.zip' -Force"
if errorlevel 1 goto :error

echo Build pronta: dist\ValeVerde-Windows.zip
exit /b 0

:error
echo Falha ao gerar a build. Leia a mensagem acima.
exit /b 1
