@echo off
setlocal
cd /d "%~dp0"

set "GERADOR=%~dp0ferramentas\projeto_ura.py"
set "PYTHON=C:\Users\fabio.bezerra\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if exist "%PYTHON%" goto executar_python
where py >nul 2>nul
if errorlevel 1 goto python_nao_encontrado

py -3 "%GERADOR%" gerar
goto resultado

:executar_python
"%PYTHON%" "%GERADOR%" gerar
goto resultado

:python_nao_encontrado
echo ERRO: Python nao foi encontrado.
echo Instale o Python e a dependencia lxml conforme o README.md.
set "CODIGO=1"
goto finalizar

:resultado
set "CODIGO=%ERRORLEVEL%"
if "%CODIGO%"=="0" echo.

:finalizar
echo.
pause
exit /b %CODIGO%