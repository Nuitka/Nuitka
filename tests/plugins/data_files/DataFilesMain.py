#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

import os

import data_files_package

# nuitka-project: --mode=standalone
# nuitka-project: --user-package-configuration-file={MAIN_DIRECTORY}/test_case.nuitka-package.config.yml
# nuitka-project-if: {Commercial} is not None:
#   nuitka-project: --embed-data-files-runtime-pattern=lala.txt

assert os.path.exists(
    os.path.join(os.path.dirname(data_files_package.__file__), "lala.txt")
)
assert os.path.exists(
    os.path.join(os.path.dirname(data_files_package.__file__), "sub_dir/lulu.txt")
)

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
