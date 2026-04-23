#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-project: --mode=standalone

# nuitka-skip-unless-imports: flet_desktop

from pathlib import Path

import flet_desktop

app_dir = Path(flet_desktop.get_package_bin_dir())
flet_runtime_dir = app_dir / "flet"

assert app_dir.is_dir(), app_dir
assert flet_runtime_dir.is_dir(), flet_runtime_dir

entries = tuple(path for path in flet_runtime_dir.iterdir() if path.is_file())
entry_names = tuple(sorted(path.name for path in entries))

assert any(path.name.casefold() == "flet.exe" for path in entries), entry_names
assert any(path.suffix.casefold() == ".dll" for path in entries), entry_names

print("OK.")

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
