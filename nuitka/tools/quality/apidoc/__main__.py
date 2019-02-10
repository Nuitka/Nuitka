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

""" Generated API documentation for Nuitka source.

"""

from __future__ import print_function

import os
import shutil
import subprocess
import sys
from optparse import OptionParser

# Unchanged, running from checkout, use the parent directory, the nuitka
# package ought be there.
sys.path.insert(
    0,
    os.path.abspath(
        os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
        )
    ),
)

from nuitka.tools.Basics import goHome  # isort:skip


def main():
    goHome()

    parser = OptionParser()

    parser.add_option(
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="""\
        Default is %default.""",
    )

    # TODO: No actual options yet.
    _options, _positional_args = parser.parse_args()

    shutil.rmtree("html", ignore_errors=True)

    print("Running doxygen:")
    subprocess.check_call(["doxygen", "doc/Doxyfile"])

    # Update the repository on the web site.
    assert (
        os.system(
            "rsync -avz --delete html --chown www-data root@nuitka.net:/var/www/apidoc/"
        )
        == 0
    )

    print("Finished.")


if __name__ == "__main__":
    main()
