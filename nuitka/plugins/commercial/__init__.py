#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
""" Commercial plugins package.

This may load code from places indicated by a heuristics.
"""


# Auto extend to a Nuitka commercial installation, by adding it to the package
# path. That aims at making extending Nuitka with these plugins easier.
import os

if "NUITKA_COMMERCIAL" in os.environ:
    path = os.environ["NUITKA_COMMERCIAL"]

    for candidate in "nuitka/plugins/commercial", ".":
        candidate = os.path.join(path, candidate)
        if os.path.isdir(candidate) and os.path.isfile(
            os.path.join(candidate, "__init__.py")
        ):
            __path__.append(candidate)
