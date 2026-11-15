@echo off
rem     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

setlocal

pushd "%~dp0.."

where ruff >nul 2>nul
if not errorlevel 1 goto :run_ruff

python -m ruff --version >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    goto :run_py_ruff
)

set "PYTHON_EXE="
if exist ".vscode\.python_alias_path" (
    for /f "usebackq delims=" %%p in (".vscode\.python_alias_path") do set "PYTHON_EXE=%%p"
)

if defined PYTHON_EXE (
    "%PYTHON_EXE%" -m ruff --version >nul 2>nul
    if not errorlevel 1 goto :run_py_ruff
)

popd
echo Error: ruff not found. Install 'ruff' or add it to PATH.
exit /b 1

:run_ruff
if "%~1"=="" (
    ruff check nuitka/
) else (
    ruff check %*
)
set "RC=%errorlevel%"
popd
exit /b %RC%

:run_py_ruff
if "%~1"=="" (
    "%PYTHON_EXE%" -m ruff check nuitka/
) else (
    "%PYTHON_EXE%" -m ruff check %*
)
set "RC=%errorlevel%"
popd
exit /b %RC%

rem     Part of "Nuitka", an optimizing Python compiler that is compatible and
rem     integrates with CPython, but also works on its own.
rem
rem     Licensed under the GNU Affero General Public License, Version 3 (the "License");
rem     you may not use this file except in compliance with the License.
rem     You may obtain a copy of the License at
rem
rem        https://www.gnu.org/licenses/agpl-3.0.txt
rem
rem     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
rem     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
rem
rem     Unless required by applicable law or agreed to in writing, software
rem     distributed under the License is distributed on an "AS IS" BASIS,
rem     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
rem     See the License for the specific language governing permissions and
rem     limitations under the License.
