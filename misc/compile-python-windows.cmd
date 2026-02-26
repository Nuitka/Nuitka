@echo off
rem     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

setlocal

:: --- Configuration ---
:: Set the Python version you want to build.
set PY_VER=3.14.0

set TARBALL=Python-%PY_VER%.tgz
set SOURCE_DIR=Python-%PY_VER%

:: --- Argument Parsing ---
set BUILD_CONFIG=Release
set PGO_FLAG=--pgo
set PYTHON_BINARY=PCbuild\amd64\python.exe

set EXTERNALS_FLAG=
set EXTERNALS_DIR=%CD%\python-externals-%PY_VER%
set BUILD_TARGET=Build

:parse_args
if "%~1"=="--debug" (
    set BUILD_CONFIG=Debug
    set PGO_FLAG=
    set PYTHON_BINARY=PCbuild\amd64\python_d.exe
    set EXTERNALS_FLAG=--no-llvm
    shift
    goto parse_args
)

if "%~1"=="--rebuild" (
    set BUILD_TARGET=Rebuild
    shift
    goto parse_args
)

echo --- Starting Python %PY_VER% build for Nuitka on Windows ---
echo Configuration: %BUILD_CONFIG%
if "%BUILD_CONFIG%"=="Release" (
    echo PGO is Enabled.
) else (
    echo PGO is Disabled. Assertions are Enabled.
)

:: --- 1. Download and Extract Source ---
if not exist "%TARBALL%" (
    echo Downloading %TARBALL%...
    curl -L -o "%TARBALL%" "https://www.python.org/ftp/python/%PY_VER%/%TARBALL%" || (
        echo Error: Failed to download %TARBALL%
        exit /b 1
    )
) else (
    echo Using existing %TARBALL%...
)

if exist "%SOURCE_DIR%" (
    echo Using existing source directory %SOURCE_DIR%...
) else (
    echo Extracting %TARBALL%...
    tar -xf "%TARBALL%" || (
        echo Error: Failed to extract %TARBALL%
        exit /b 1
    )

    if exist "%EXTERNALS_DIR%" (
        echo Restoring externals from cache...
        mkdir "%SOURCE_DIR%\externals"
        xcopy /s /e /y /q "%EXTERNALS_DIR%\*" "%SOURCE_DIR%\externals\"
    )
)

:: --- 2. Configure and Build ---
cd "%SOURCE_DIR%" || exit /b 1

echo Fetching external dependencies...
call PCbuild\get_externals.bat %EXTERNALS_FLAG% || (
    echo Error: Failed to fetch external dependencies
    exit /b 1
)

echo Building Python...
:: -e: Fetch external dependencies (often redundant with get_externals, but safe)
:: -p x64: Build for 64-bit architecture
:: -c: Configuration (Release or Debug)
:: -t: Target (Build or Rebuild)
:: --pgo: Enable Profile Guided Optimization (empty if debug)
:: "/p:PlatformToolset=v143": Use MSVC 2022/2024 Platform Toolset instead of a legacy one
call PCbuild\build.bat -e -p x64 -t %BUILD_TARGET% -c %BUILD_CONFIG% %PGO_FLAG% "/p:PlatformToolset=v143" || (
    echo Build failed!
    exit /b 1
)

echo Installing dependencies via pip...
%PYTHON_BINARY% -m ensurepip

:: Write dependencies to a temporary requirements file
echo # Onefile compression > reqs.txt
echo zstandard ^>= 0.15; python_version ^>= '3.5' >> reqs.txt
echo. >> reqs.txt
echo # Wheels >> reqs.txt
echo wheel >> reqs.txt

%PYTHON_BINARY% -m pip install -r reqs.txt
del reqs.txt

echo --- Build Complete ---
echo The uninstalled self-compiled Python is located at "%CD%\%PYTHON_BINARY%"

rem     Part of "Nuitka", an optimizing Python compiler that is compatible and
rem     integrates with CPython, but also works on its own.
rem
rem     Licensed under the GNU Affero General Public License, Version 3 (the "License");
rem     you may not use this file except in compliance with the License.
rem     You may obtain a copy of the License at
rem
rem        http://www.gnu.org/licenses/agpl.txt
rem
rem     Unless required by applicable law or agreed to in writing, software
rem     distributed under the License is distributed on an "AS IS" BASIS,
rem     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
rem     See the License for the specific language governing permissions and
rem     limitations under the License.
