#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Using pkgutil to read data from a package.

This test can use the commercial code, which includes the file inside
the binary, inaccessible to the user, as as well a the free code, where
the file must exist in the file system.
"""

# nuitka-project: --include-package=package
# nuitka-project: --follow-imports
# nuitka-project-if: {Commercial} is not None:
#  nuitka-project: --embed-data-files-runtime-pattern=*
#  nuitka-project: --include-package-data=package

# test code, pylint: disable=unused-import

import package

#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
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
