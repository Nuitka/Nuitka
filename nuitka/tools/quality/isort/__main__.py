#!/usr/bin/env python
#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Sort import statements using isort for Nuitka source.

"""

from __future__ import print_function

import os
import re
import subprocess
import sys
from optparse import OptionParser

from nuitka.tools.quality.autoformat.Autoformat import cleanupWindowsNewlines

# Unchanged, running from checkout, use the parent directory, the nuitka
# package ought be there.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".."
        )
    )
)

from nuitka.tools.Basics import goHome, addPYTHONPATH, setupPATH # isort:skip
from nuitka.tools.quality.ScanSources import scanTargets # isort:skip


def main():
    goHome()

    # So isort finds nuitka package.
    addPYTHONPATH(os.getcwd())

    parser = OptionParser()

    parser.add_option(
        "--verbose",
        action  = "store_true",
        dest    = "verbose",
        default = False,
        help    = """\
        Default is %default."""
    )

    _options, positional_args = parser.parse_args()

    if not positional_args:
        positional_args = [
            "bin",
            "nuitka",
            "tests/reflected/compile_itself.py"
        ]

    target_files = []
    for filename in scanTargets(positional_args, (".py", ".scons")):
        # This breaks the PyLint annotations currently.
        if os.path.basename(filename) == "Autoformat.py":
            continue

        package_name = os.path.dirname(filename)

        # Make imports local if possible.
        if package_name.startswith("nuitka" + os.path.sep):
            package_name = package_name.replace(os.path.sep, '.')

            source_code = open(filename).read()
            updated_code = re.sub(r"from %s import" % package_name, "from . import", source_code)
            updated_code = re.sub(r"from %s\." % package_name, "from .", source_code)

            if source_code != updated_code:
                with open(filename, 'w') as out_file:
                    out_file.write(updated_code)


        target_files.append(filename)

    setupPATH()
    subprocess.check_call(
        [
            "isort",
            "-ot", # Order imports by type in addition to alphabetically
            "-m3", # "vert-hanging"
            "-up", # Prefer braces () over \ for line continuation.
            "-ns", # Do not ignore those:
            "__init__.py"
        ] + target_files
    )

    # For Windows, work around that isort changes encoding.
    if os.name == "nt":
        for filename in target_files:
            cleanupWindowsNewlines(filename)

if __name__ == "__main__":
    main()
