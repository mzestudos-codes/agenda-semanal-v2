@echo off
setlocal
cd /d "%~dp0"
py -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
py -m PyInstaller --noconfirm --clean --onefile --windowed --name AgendaSemanal main.py
if errorlevel 1 exit /b 1
copy /Y config.json dist\config.json >nul
if errorlevel 1 exit /b 1
echo.
echo Executavel criado em dist\AgendaSemanal.exe
echo Configure dist\config.json com seu repositorio publico do GitHub.
echo Distribua AgendaSemanal.exe e config.json juntos.
endlocal
