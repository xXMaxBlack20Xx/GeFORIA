@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "PYTHONUTF8=1"
set "PROJECT=%~dp0"
set "PYTHON="
set "PYTHON_ARGS="

if not exist "%PROJECT%main.py" goto incomplete
if not exist "%PROJECT%geforia\windows_launcher.py" goto incomplete
if not exist "%PROJECT%requirements.txt" goto incomplete

rem Reutilizar primero el entorno de Windows, sin tocar el de Fedora.
if not exist "%PROJECT%.venv-windows\Scripts\python.exe" goto find_python
"%PROJECT%.venv-windows\Scripts\python.exe" -c "import sys, tkinter; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if errorlevel 1 goto find_python
set "PYTHON=%PROJECT%.venv-windows\Scripts\python.exe"
goto launch

:find_python
py -3 -c "import sys, tkinter; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if errorlevel 1 goto try_python
set "PYTHON=py"
set "PYTHON_ARGS=-3"
goto launch

:try_python
python -c "import sys, tkinter; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if errorlevel 1 goto try_python3
set "PYTHON=python"
goto launch

:try_python3
python3 -c "import sys, tkinter; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if errorlevel 1 goto missing_python
set "PYTHON=python3"

:launch
"%PYTHON%" %PYTHON_ARGS% "%PROJECT%geforia\windows_launcher.py" %*
set "RESULT=%ERRORLEVEL%"
if "%RESULT%"=="0" exit /b 0
echo.
echo GeFORIA no pudo iniciarse o se cerro con un error.
echo Conserva el mensaje de arriba: puedes copiarlo o tomarle una foto.
goto failed

:missing_python
echo No se encontro Python 3.10 o posterior con Tkinter.
echo Instala Python desde https://www.python.org/downloads/windows/
echo Activa pip, Tcl/Tk y Add python.exe to PATH en el instalador.
echo Despues vuelve a abrir este archivo.
goto failed

:incomplete
echo La carpeta de GeFORIA esta incompleta.
echo Extrae TODO el ZIP antes de abrir iniciar_geforia.bat.

:failed
echo.
echo Consulta GUIA_WINDOWS.md en la carpeta del programa o en:
echo https://github.com/xXMaxBlack20Xx/GeFORIA/blob/main/GUIA_WINDOWS.md
echo.
echo Pulsa una tecla cuando hayas guardado el mensaje.
pause >nul
exit /b 1
