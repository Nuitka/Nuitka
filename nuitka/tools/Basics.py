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
""" Basics for Nuitka tools.

"""

import os
import sys


def goHome():
    """ Go its own directory, to have it easy with path knowledge.

    """
    os.chdir(
        getHomePath()
    )

my_abs_path = os.path.abspath(__file__)

def getHomePath():
    return os.path.normpath(
        os.path.join(
            os.path.dirname(my_abs_path),
            "..",
            ".."
        )
    )

def setupPATH():
    """ Make sure installed tools are in PATH.

    For Windows, add this to the PATH, so pip installed PyLint will be found
    near the Python executing this script.
    """
    os.environ["PATH"] = os.environ["PATH"] + \
                         os.pathsep + \
                         os.path.join(os.path.dirname(sys.executable),"scripts")

def addPYTHONPATH(path):
    python_path = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = os.pathsep.join(
        python_path.split(os.pathsep) + \
        [path]
    )
