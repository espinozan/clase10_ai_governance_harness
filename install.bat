
@echo off
setlocal EnableExtensions
title Clase 10 - AI Governance Harness Installer
cd d %~dp0

echo ============================================
echo   Clase 10 - AI Governance Harness
echo   Instalador para Windows 1011
echo ============================================
echo.

where py nul 2&1
if %errorlevel%==0 (
    set PY=py -3
    goto install
)

where python nul 2&1
if %errorlevel%==0 (
    set PY=python
    goto install
)

echo ERROR Python no esta instalado o no esta en PATH.
echo Instala Python desde httpswww.python.orgdownloadswindows
echo Activa la opcion Add Python to PATH.
pause
exit b 1

install
echo [14] Comprobando Python...
%PY% --version
if errorlevel 1 goto error

echo [24] Creando entorno virtual...
if not exist .venvScriptspython.exe (
    %PY% -m venv .venv
    if errorlevel 1 goto error
)

echo [34] Instalando dependencias...
if not exist requirements.txt (
    echo ERROR No se encuentra requirements.txt.
    echo Ejecuta este instalador dentro de la carpeta del proyecto.
    goto error
)

.venvScriptspython.exe -m pip install --upgrade pip
if errorlevel 1 goto error

.venvScriptspython.exe -m pip install -r requirements.txt
if errorlevel 1 goto error

echo [44] Preparando configuracion...
if not exist .env (
    copy .env.example .env nul
    if errorlevel 1 goto error
)

if not exist data mkdir data

echo.
echo Instalacion completada.
echo.
echo Edita .env para configurar Groq, Hugging Face o mock.
echo Despues ejecuta run.bat para iniciar la aplicacion.
echo.
pause
exit b 0

error
echo.
echo ERROR La instalacion no pudo completarse.
echo Revisa el mensaje anterior.
pause
exit b 1
