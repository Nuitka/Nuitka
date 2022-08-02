#!/usr/bin/env python
#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Main program for DLL checker tool.

"""

import os
import sys
import tempfile
from optparse import OptionParser

from nuitka.freezer.DllDependenciesWin32 import (
    detectBinaryPathDLLsWindowsDependencyWalker,
)
from nuitka.Tracing import my_print
from nuitka.utils.SharedLibraries import getDLLVersion, getSxsFromDLL
from nuitka.utils.Timing import TimerReport


def main():
    parser = OptionParser()

    _options, positional_args = parser.parse_args()

    if not positional_args:
        sys.exit("No DLLs given.")

    for filename in positional_args:
        my_print("Filename: %s" % filename)
        my_print("Version Information: %s" % (getDLLVersion(filename),))

        my_print("SXS information (manifests):")
        sxs = getSxsFromDLL(filename=filename, with_data=True)
        if sxs:
            my_print(sxs)

        my_print("DLLs recursively depended (depends.exe):")

        with TimerReport(
            message="Finding dependencies for %s took %%.2f seconds" % filename
        ):
            r = detectBinaryPathDLLsWindowsDependencyWalker(
                is_main_executable=False,
                source_dir=tempfile.gettempdir(),
                original_dir=os.path.dirname(filename),
                binary_filename=filename,
                package_name=None,
                use_cache=False,
                update_cache=False,
            )

            for dll_filename in sorted(r):
                my_print("   %s" % dll_filename)

            my_print("Total: %d" % len(r))


if __name__ == "__main__":
    main()
