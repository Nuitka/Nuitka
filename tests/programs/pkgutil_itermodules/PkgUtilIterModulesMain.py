#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

import importlib
import pkgutil

import some_package.sub_package1.SomeModuleC
import some_package.sub_package1.SomeModuleD
import some_package.sub_package2.SomeModuleA
import some_package.sub_package2.SomeModuleB

# nuitka-skip-unless-imports: importlib


# Use the original "__file__" value normally, at least one case warns
# about things with filename included, but for pkgutil iteration, make
# sure we do not see original Python dirs.

# nuitka-project: --file-reference-choice=runtime

# nuitka-project: --follow-imports

print("Checking with 'pkg_util.iter_modules' what was included:")
pkg = __import__("some_package")
print("Package is", pkg)

it = pkgutil.iter_modules(pkg.__path__)
for r in it:
    print(r[1], r[2])

    if r[2]:
        sub_pkg = importlib.import_module("some_package." + r[1])
        for r2 in pkgutil.iter_modules(sub_pkg.__path__):
            print("  ", r2[1], r2[2])


print("Done")

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
