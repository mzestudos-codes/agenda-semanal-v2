@echo off
setlocal
cd /d "%~dp0"
py -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
py -m PyInstaller --noconfirm --clean --onefile --windowed --name AgendaMercado main.py
if errorlevel 1 exit /b 1
copy /Y config.json dist\config.json >nul
if errorlevel 1 exit /b 1
echo Executavel criado em dist\AgendaMercado.exe
endlocal
