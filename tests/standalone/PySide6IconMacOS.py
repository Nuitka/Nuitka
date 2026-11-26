#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Check that Qt uses the macOS application bundle icon."""

# nuitka-project: --mode=app-dist
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --macos-app-icon={MAIN_DIRECTORY}/../../doc/images/Nuitka-Logo-Symbol.png
# nuitka-skip-unless-imports: PySide6.QtWidgets

from PySide6.QtWidgets import QApplication

app = QApplication([])

if "__compiled__" in globals():
    assert not app.windowIcon().isNull()

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
