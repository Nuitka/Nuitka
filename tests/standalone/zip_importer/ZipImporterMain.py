#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
# nuitka-project: --standalone
# nuitka-project: --include-data-file={MAIN_DIRECTORY}/for_import.zip=for_import.zip

# isort:start

import os
import sys

zip_filename = os.path.join(os.path.dirname(__file__) or ".", "for_import.zip")

assert os.path.exists(zip_filename)
sys.path.insert(0, zip_filename)

# Import after it can work now.
import zip_module  # isort:skip
