#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

# PowerShell workspace profile for Nuitka

# Smuggle python aliases referencing the active VS Code python interpreter
if (Test-Path .vscode\.python_alias_path) {
    $p = (Get-Content .vscode\.python_alias_path).Trim()
    function python { & $p @args }
    function py { & $p @args }

    $pip = Join-Path (Join-Path (Split-Path $p) 'Scripts') 'pip.exe'
    if (Test-Path $pip) {
        function pip { & $pip @args }
    }
}

# Add Git's usr\bin directory to PATH so we get grep, ls, etc.
$gitCmd = Get-Command git.exe -ErrorAction SilentlyContinue
if ($gitCmd) {
    # Typically git.exe is in ...\Git\cmd\git.exe
    if ($gitCmd.Path -match "^(.+)\\cmd\\git\.exe$") {
        $gitUsrBin = Join-Path $Matches[1] "usr\bin"
        if (Test-Path $gitUsrBin) {
            $env:PATH = "$gitUsrBin;$env:PATH"
        }
    }
}

#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
