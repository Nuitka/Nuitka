@echo off
rem     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
rem 
rem     Part of "Nuitka", an optimizing Python compiler that is compatible and
rem     integrates with CPython, but also works on its own.
rem 
rem     Licensed under the Apache License, Version 2.0 (the "License");
rem     you may not use this file except in compliance with the License.
rem     You may obtain a copy of the License at
rem 
rem        http://www.apache.org/licenses/LICENSE-2.0
rem 
rem     Unless required by applicable law or agreed to in writing, software
rem     distributed under the License is distributed on an "AS IS" BASIS,
rem     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
rem     See the License for the specific language governing permissions and
rem     limitations under the License.
rem 

setlocal

if exist "%~dp0..\python.exe" (
"%~dp0..\python" -m nuitka %*
) else (
"%~dp0python" -m nuitka %*
)

endlocal
