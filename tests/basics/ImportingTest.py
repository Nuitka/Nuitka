#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

import os

from nuitka.importing import Importing as ImportingModule
from nuitka.importing.Importing import (
    flushImportCache,
    normalizedListDirCached,
)


def testNormalizedListDirCacheKeepsCaseVariants():
    original_list_dir_cached = ImportingModule.listDirCached
    original_normcase = ImportingModule.os.path.normcase

    try:

        def fakeListDirCached(path):
            return (
                (os.path.join(path, "Spam.py"), "Spam.py"),
                (os.path.join(path, "spam.py"), "spam.py"),
            )

        def fakeNormcase(path):
            return path.lower()

        ImportingModule.listDirCached = fakeListDirCached
        ImportingModule.os.path.normcase = fakeNormcase
        flushImportCache()

        temp_dir = "/virtual/import-test"
        normalized_entries = normalizedListDirCached(temp_dir)
        case_key = fakeNormcase(os.path.join(temp_dir, "Spam.py"))

        assert case_key in normalized_entries
        assert normalized_entries[case_key] == [
            os.path.join(temp_dir, "Spam.py"),
            os.path.join(temp_dir, "spam.py"),
        ]
    finally:
        ImportingModule.listDirCached = original_list_dir_cached
        ImportingModule.os.path.normcase = original_normcase


testNormalizedListDirCacheKeepsCaseVariants()
print("Normalized import directory cache keeps case variants")


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
