@echo off
setlocal enabledelayedexpansion

echo ======================================================
echo    Cursor Studio - Compilation en EXE
echo ======================================================
echo.

:: Vérifier si Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Erreur : Python n'est pas installe ou pas dans le PATH.
    pause
    exit /b
)

:: Installation de PyInstaller
echo [1/3] Installation de PyInstaller...
pip install pyinstaller --quiet
if %errorlevel% neq 0 (
    echo Erreur lors de l'installation de PyInstaller.
    pause
    exit /b
)

:: Correction du conflit pathlib (obsolète dans Python 3+)
echo [1.5/3] Vérification des conflits de bibliothèques...
python -m pip uninstall pathlib -y --quiet >nul 2>&1

:: Nettoyage des dossiers de build précédents
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: Compilation avec PyInstaller
echo [2/3] Compilation en cours (cela peut prendre une minute)...
:: --noconsole : Pas de fenêtre CMD au lancement
:: --onefile : Un seul fichier EXE
:: --add-data : Inclure le dossier app pour les ressources
pyinstaller --noconsole --onefile --name "CursorStudio" --add-data "app;app" main.py

if %errorlevel% neq 0 (
    echo.
    echo Erreur lors de la compilation.
    pause
    exit /b
)

echo.
echo [3/3] Nettoyage...
if exist CursorStudio.spec del CursorStudio.spec

echo.
echo ======================================================
echo    SUCCES : Votre application est prete !
echo    Le fichier se trouve ici : dist\CursorStudio.exe
echo ======================================================
echo.
pause
