#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


print("Main importing nearby package")

import pyexpat  # isort:skip
from some_package import normal_importing, star_importing  # isort:skip

try:
    print(pyexpat.defined_in_pyexpat)
except AttributeError:
    print("Must be Python3, where absolute imports are default.")
print("Main importing from package doing star import")
print("Main importing from package doing normal import")

print("Done.")

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
