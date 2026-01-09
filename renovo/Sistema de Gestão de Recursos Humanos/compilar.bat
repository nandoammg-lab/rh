@echo off
chcp 65001 >nul
echo ========================================
echo   COMPILADOR FLET - PyInstaller
echo ========================================
echo.

cd /d "%~dp0"

REM Detectar comando Python disponível
set PYTHON_CMD=
py --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py
    echo Python encontrado: py
    goto :python_found
)

python --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python
    echo Python encontrado: python
    goto :python_found
)

echo.
echo ❌ Python não encontrado!
echo Certifique-se de que Python está instalado e no PATH.
echo.
pause
exit /b 1

:python_found
echo.

REM Criar e ativar ambiente virtual
set VENV_DIR=venv_compilacao
echo [0/5] Configurando ambiente virtual...

if not exist "%VENV_DIR%\" (
    echo Criando ambiente virtual em %VENV_DIR%...
    %PYTHON_CMD% -m venv %VENV_DIR%
    if errorlevel 1 (
        echo ❌ Erro ao criar ambiente virtual
        pause
        exit /b 1
    )
)

echo Ativando ambiente virtual...
call %VENV_DIR%\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Erro ao ativar ambiente virtual
    pause
    exit /b 1
)
echo ✅ Ambiente virtual ativado
echo.

REM Solicitar nome do arquivo Python
set /p ARQUIVO_PY="Digite o nome do arquivo .py (sem extensão): "

if not exist "%ARQUIVO_PY%.py" (
    echo.
    echo ❌ Arquivo %ARQUIVO_PY%.py não encontrado!
    echo.
    pause
    exit /b 1
)

echo.
echo Arquivo a compilar: %ARQUIVO_PY%.py
echo.

REM Perguntar sobre ícone
set /p ICONE="Digite o nome do arquivo de ícone (sem .ico, deixe vazio se não tiver): "
if not "%ICONE%"=="" set ICONE=%ICONE%.ico

echo.
echo [1/5] Instalando dependências...
%PYTHON_CMD% -m pip install --upgrade pip setuptools wheel --quiet

REM Verificar se requirements.txt existe e instalar dependências
if exist "requirements.txt" (
    echo Instalando dependências do requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo ❌ Erro ao instalar dependências do requirements.txt
        pause
        exit /b 1
    )
    echo ✅ Dependências do requirements.txt instaladas
) else (
    REM Fallback: instalar dependências individualmente
    echo requirements.txt não encontrado, instalando dependências básicas...
    
    REM Instalar flet-cli (necessário para flet pack)
    echo Instalando flet-cli...
    %PYTHON_CMD% -m pip install flet-cli --quiet
    if errorlevel 1 (
        echo ❌ Erro ao instalar flet-cli
        pause
        exit /b 1
    )

    REM Instalar PyInstaller (necessário para flet pack)
    echo Instalando PyInstaller...
    %PYTHON_CMD% -m pip install pyinstaller --quiet
    if errorlevel 1 (
        echo ❌ Erro ao instalar PyInstaller
        pause
        exit /b 1
    )

    REM Forçar reinstalação do flet-desktop para compatibilidade
    echo Reinstalando flet-desktop para compatibilidade...
    %PYTHON_CMD% -m pip install --force-reinstall flet-desktop --quiet
)

echo Analisando código para detectar dependências...
echo (Verificando arquivo principal e subpastas...)

REM =====================================================================
REM FLET - Framework de interface gráfica
REM =====================================================================
findstr /s /i "import flet\|from flet" *.py >nul 2>&1
if %errorlevel%==0 (
    echo Detectado: flet - Instalando...
    %PYTHON_CMD% -m pip install flet flet-desktop --quiet
)

REM =====================================================================
REM REPORTLAB - Geração de PDF
REM =====================================================================
findstr /s /i "from reportlab\|import reportlab" *.py >nul 2>&1
if %errorlevel%==0 (
    echo Detectado: reportlab - Instalando...
    %PYTHON_CMD% -m pip install reportlab --quiet
)

REM =====================================================================
REM OPENPYXL - Manipulação de Excel
REM =====================================================================
findstr /s /i "import openpyxl\|from openpyxl" *.py >nul 2>&1
if %errorlevel%==0 (
    echo Detectado: openpyxl - Instalando...
    %PYTHON_CMD% -m pip install openpyxl --quiet
)

REM =====================================================================
REM PYTHON-DATEUTIL - Manipulação de datas
REM =====================================================================
findstr /s /i "from dateutil\|import dateutil" *.py >nul 2>&1
if %errorlevel%==0 (
    echo Detectado: python-dateutil - Instalando...
    %PYTHON_CMD% -m pip install python-dateutil --quiet
)

REM =====================================================================
REM PILLOW - Manipulação de imagens
REM =====================================================================
findstr /s /i "from PIL\|import PIL" *.py >nul 2>&1
if %errorlevel%==0 (
    echo Detectado: PIL/Pillow - Instalando...
    %PYTHON_CMD% -m pip install pillow --quiet
)

REM =====================================================================
REM REQUESTS - Requisições HTTP
REM =====================================================================
findstr /s /i "import requests\|from requests" *.py >nul 2>&1
if %errorlevel%==0 (
    echo Detectado: requests - Instalando...
    %PYTHON_CMD% -m pip install requests --quiet
)

REM =====================================================================
REM NUMPY - Computação numérica
REM =====================================================================
findstr /s /i "import numpy\|from numpy" *.py >nul 2>&1
if %errorlevel%==0 (
    echo Detectado: numpy - Instalando...
    %PYTHON_CMD% -m pip install numpy --quiet
)

echo ✅ Dependências instaladas
echo.

echo [2/5] Limpando compilações anteriores...
if exist "build\" rmdir /s /q build
if exist "dist\" rmdir /s /q dist
if exist "%ARQUIVO_PY%.spec" del /q "%ARQUIVO_PY%.spec"
echo ✅ Limpeza concluída
echo.

echo [3/5] Preparando comando de compilação...
echo.

REM Montar argumentos do PyInstaller
set "PYINST_ARGS=--onefile --noconsole --name %ARQUIVO_PY%"

REM Adicionar ícone se fornecido
if not "%ICONE%"=="" (
    if exist "%ICONE%" (
        set "PYINST_ARGS=%PYINST_ARGS% --icon=%ICONE%"
        echo Ícone: %ICONE%
    ) else (
        echo ⚠️ Arquivo de ícone %ICONE% não encontrado!
    )
)

REM Adicionar pastas de recursos se existirem
if exist "images\" (
    set "PYINST_ARGS=%PYINST_ARGS% --add-data=images;images"
    echo Incluindo pasta: images\
)

if exist "imagens\" (
    set "PYINST_ARGS=%PYINST_ARGS% --add-data=imagens;imagens"
    echo Incluindo pasta: imagens\
)

if exist "utilities\" (
    set "PYINST_ARGS=%PYINST_ARGS% --add-data=utilities;utilities"
    echo Incluindo pasta: utilities\
)

if exist "assets\" (
    set "PYINST_ARGS=%PYINST_ARGS% --add-data=assets;assets"
    echo Incluindo pasta: assets\
)

REM Adicionar hidden imports para flet
set "PYINST_ARGS=%PYINST_ARGS% --hidden-import=flet --hidden-import=flet_core --hidden-import=flet_runtime"
set "PYINST_ARGS=%PYINST_ARGS% --collect-all=flet --collect-all=flet_core --collect-all=flet_runtime"

REM Adicionar distpath e flag -y
set "PYINST_ARGS=%PYINST_ARGS% --distpath=dist -y"

echo.
echo [4/5] Compilando executável com PyInstaller...
echo (Isso pode levar alguns minutos)
echo Comando: pyinstaller %PYINST_ARGS% %ARQUIVO_PY%.py
echo.

pyinstaller %PYINST_ARGS% %ARQUIVO_PY%.py

if errorlevel 1 (
    echo.
    echo ❌ ERRO na compilação!
    echo.
    echo Verifique os erros acima e tente novamente.
    echo.
    echo [5/5] Desativando ambiente virtual...
    call deactivate 2>nul
    pause
    exit /b 1
)

echo.
echo [5/5] Desativando ambiente virtual...
call deactivate 2>nul
echo ✅ Ambiente virtual desativado

echo.
echo ========================================
echo   ✅ COMPILAÇÃO CONCLUÍDA COM SUCESSO!
echo ========================================
echo.
echo O executável está em:
echo   %~dp0dist\%ARQUIVO_PY%.exe
echo.
pause
