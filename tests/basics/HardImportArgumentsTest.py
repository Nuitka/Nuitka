#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Argument names of calls to hard imported functions, given as keywords."""

from __future__ import print_function

import os
import warnings

# The deprecated "package" argument of "importlib.resources.files" warns.
warnings.simplefilter("ignore")


def report(name, func):
    # The messages differ between platforms, e.g. "os.path.isdir" is
    # implemented in C on Windows, so only the exception type is checked.
    try:
        result = func()
    except TypeError:
        print(name, "TypeError")
    else:
        print(name, repr(result))


report("isdir positional:", lambda: os.path.isdir("."))
report("isdir keyword 's':", lambda: os.path.isdir(s="."))
report("isdir keyword 'path':", lambda: os.path.isdir(path="."))

try:
    from importlib.resources import files
except ImportError:
    print("No 'importlib.resources.files'.")
else:
    report("files positional:", lambda: files("json").name)
    report("files keyword 'package':", lambda: files(package="json").name)
    report("files keyword 'anchor':", lambda: files(anchor="json").name)
    report("files two positional:", lambda: files("json", "json").name)
    report(
        "files keywords 'anchor' and 'package':",
        lambda: files(anchor="json", package="json").name,
    )
    report(
        "files positional and keyword 'package':",
        lambda: files("json", package="json").name,
    )

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
