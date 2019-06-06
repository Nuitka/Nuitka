#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
from __future__ import print_function

import some_package.sub_package1.SomeModuleC
import some_package.sub_package1.SomeModuleD
import some_package.sub_package2.SomeModuleA
import some_package.sub_package2.SomeModuleB

print("Checking with 'pkg_util.iter_modules' what was included:")
import pkgutil
pkg = __import__("some_package")
it = pkgutil.iter_modules(pkg.__path__)
for r in it:
    print(r[1], r[2])

    if r[2]:
        sub_pkg = __import__("some_package." + r[1])
        for r2 in pkgutil.iter_modules(sub_pkg.__path__):
            print("  ", r2[1], r2[2])


print("Done")
