#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Python PGO test with an unused module that plugins provide fake modules for.

The profiling run takes the early exit, so "multiprocessing" is unused and
demoted to bytecode, for which the plugin provided modules have to follow.
"""

# nuitka-project: --pgo-python
# nuitka-project: --pgo-python-policy-unused-module=bytecode
# nuitka-project: --pgo-args=profiling
# nuitka-project: --disable-cache=bytecode

import multiprocessing
import sys

if "profiling" in sys.argv:
    print("Profiling run.")
    sys.exit(0)


print("Has cpu_count:", callable(multiprocessing.cpu_count))

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
