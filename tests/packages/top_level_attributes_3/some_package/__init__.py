#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Test that shows that __file__ and __spec__ are compatible after import by CPython

What CPython does when loading an extension module, like this is going to be, is
to update the "__file__" value afterwards, and then to set the "__spec__" to itself,
which disallows using the Nuitka loader for the module.
"""

from __future__ import print_function

import os


def getPathEnd(filename, elements):
    return os.path.sep.join(filename.split(os.path.sep)[-elements:])


def main():
    try:
        print("SPEC from name", getPathEnd(__spec__.origin, 2))
        print("SPEC from name", getPathEnd(__spec__.submodule_search_locations[0], 1))
    except NameError as e:
        print("No __spec__ name", str(e))

    try:
        print("FILE from name", getPathEnd(__file__, 2))
    except NameError as e:
        print("No __file__ name", str(e))

    # We do not optimize through globals()
    try:
        print("SPEC from globals", getPathEnd(globals()["__spec__"].origin, 2))
    except KeyError as e:
        print("No __spec__ globals name:", str(e))

    try:
        print("FILE from globals", getPathEnd(globals()["__file__"], 2))
    except KeyError as e:
        print("No __file__ globals name:", str(e))

    try:
        from importlib.util import find_spec

        print(getPathEnd(find_spec("some_package.some_module").origin, 2))
    except ImportError as e:
        print("No importlib.util import find_spec:", str(e))


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
