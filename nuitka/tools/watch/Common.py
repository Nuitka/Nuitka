#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Shared code for nuitka-watch backends.

"""

import os
import sys


def getPlatformRequirements(installed_python, case_data):
    requirements = list(case_data["requirements"])

    # Nuitka house keeping, these are from setup.py but we ignore onefile needs
    # as that is not currently covered in watches.
    # spell-checker: ignore orderedset,imageio
    needs_onefile = False

    if installed_python.getHexVersion() >= 0x370:
        requirements.append("ordered-set >= 4.1.0")
    if installed_python.getHexVersion() < 0x300:
        requirements.append("subprocess32")
    if needs_onefile and installed_python.getHexVersion() >= 0x370:
        requirements.append("zstandard >= 0.15")
    if (
        os.name != "nt"
        and sys.platform != "darwin"
        and installed_python.getHexVersion() < 0x370
    ):
        requirements.append("orderedset >= 2.0.3")
    if sys.platform == "darwin" and installed_python.getHexVersion() < 0x370:
        requirements.append("orderedset >= 2.0.3")

    # For icon conversion.
    if case_data.get("icons", "no") == "yes":
        requirements.append("imageio")

    return requirements


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
