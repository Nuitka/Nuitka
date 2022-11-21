#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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


def localImporter1():
    import os

    return os


def localImporter1a():
    import os as my_os_name

    return my_os_name


def localImporter2():
    from os import path

    return path


def localImporter2a():
    from os import path as renamed

    return renamed


print("Direct module import", localImporter1())
print("Direct module import using rename", localImporter1a())

print("From module import", localImporter2())
print("From module import using rename", localImporter2a())

from os import *  # isort:skip

print("Star import gave us", path)

import os.path as myname  # isort:skip

print("As import gave", myname)


def localImportFailure():
    try:
        from os import listdir, listdir2, path
    except Exception as e:
        print("gives", type(e), repr(e))

    try:
        print(path)
    except UnboundLocalError:
        print("and path was not imported", end=" ")

    print("but listdir was", listdir)


print("From import that fails in the middle", end=" ")
localImportFailure()


def nonPackageImportFailure():
    try:
        # Not allowed without being a package, should raise ValueError
        from . import whatever
    except Exception as e:
        print(type(e), repr(e))


print("Package import fails in non-package:", end=" ")
nonPackageImportFailure()


def importBuiltinTupleFailure():
    try:
        value = ("something",)
        # Not allowed to not be constant string, optimization might be fooled
        # though.
        __import__(value)
    except Exception as e:
        print(type(e), repr(e))


print("The __import__ built-in optimization can handle tuples:", end=" ")

importBuiltinTupleFailure()
