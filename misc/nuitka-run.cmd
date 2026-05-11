@echo off
rem     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

setlocal

"%~dp0nuitka.cmd --run %*"

endlocal

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
