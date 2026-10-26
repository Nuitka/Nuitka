#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-project: --follow-import-to=SelfReplacingModule

from __future__ import print_function

import SelfReplacingModule

print("Valid", SelfReplacingModule.valid)
try:
    print("InValid", SelfReplacingModule.invalid)
except Exception as e:
    print("Occurred", repr(e))
else:
    print("No Exception!")

# The replacement must not become the globals of the compiled code of the
# module, they have to remain the module dictionary it was compiled against,
# or else C code inspecting frame globals, e.g. "pyo3" based extension modules,
# will find a module dictionary that lacks "__builtins__".
print("Own Globals", SelfReplacingModule.own_globals_used())
print("Marker", SelfReplacingModule.marker_found())
print("Builtins", SelfReplacingModule.builtins_found())

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
