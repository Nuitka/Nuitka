#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" In this test, we show external data files to be found.

"""

# nuitka-project: --mode=onefile
# nuitka-project: --include-data-dir={MAIN_DIRECTORY}/external-data=external-data
# nuitka-project: --include-data-files-external=external-data

from __future__ import print_function

import os
import sys

for line in open(
    os.path.join(os.path.dirname(sys.argv[0]), "external-data/external-data.txt")
):
    print("External data:", line)

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
