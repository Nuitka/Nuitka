#!/usr/bin/env python
#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Tool to compare output of CPython and Nuitka.

"""

from __future__ import print_function

import os
import sys
import tempfile

from nuitka.tools.testing.Common import compileLibraryTest, createSearchMode, setup
from nuitka.Tracing import my_print
from nuitka.utils.SharedLibraries import getSxsFromDLL


def decide(root, filename):
    return (
        filename.endswith((".so", ".pyd"))
        and not filename.startswith("libpython")
        and getSxsFromDLL(os.path.join(root, filename))
    )


def action(stage_dir, root, path):
    # We need only the actual path, pylint: disable=unused-argument

    sxs = getSxsFromDLL(path)
    if sxs:
        my_print(path, sxs)


def main():
    if os.name != "nt":
        sys.exit("Error, this is only for use on Windows where SxS exists.")

    setup(needs_io_encoding=True)
    search_mode = createSearchMode()

    tmp_dir = tempfile.gettempdir()

    compileLibraryTest(
        search_mode=search_mode,
        stage_dir=os.path.join(tmp_dir, "find_sxs_modules"),
        decide=decide,
        action=action,
    )

    my_print("FINISHED, all extension modules checked.")


if __name__ == "__main__":
    main()
