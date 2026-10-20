@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title DraveDice - exe bouwen

if not exist ".venv\Scripts\python.exe" (
    echo Geen .venv gevonden. Draai eerst run.bat of herstel.bat.
    pause
    exit /b 1
)

echo PyInstaller controleren/installeren...
".venv\Scripts\python.exe" -m pip install --only-binary=:all: pyinstaller
if errorlevel 1 ( echo Kon PyInstaller niet installeren. & pause & exit /b 1 )

echo.
echo Bouwen ^(een enkel .exe-bestand^)...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean dravedice.spec
if errorlevel 1 ( echo. & echo Bouwen mislukt. & pause & exit /b 1 )

echo.
echo Klaar. De app staat als "dist\DraveDice.exe".
pause
endlocal
