#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Python version specifics.

This abstracts the Python version decisions. This makes decisions based on
the numbers, and attempts to give them meaningful names. Where possible it
should attempt to make run time detections.

"""

import re
import sys


def getSupportedPythonVersions():
    return ("2.6", "2.7", "3.2", "3.3", "3.4")


def getSupportedPythonVersionStr():
    supported_python_versions = getSupportedPythonVersions()

    supported_python_versions_str = repr(supported_python_versions)[1:-1]
    supported_python_versions_str = re.sub(
        r"(.*),(.*)$",
        r"\1, or\2",
        supported_python_versions_str
    )

    return supported_python_versions_str


def _getPythonVersion():
    big, major, minor = sys.version_info[0:3]

    return big * 100 + major * 10 + minor

python_version = _getPythonVersion()

python_version_full_str = '.'.join(str(s) for s in sys.version_info[0:3])
python_version_str = '.'.join(str(s) for s in sys.version_info[0:2])

def isAtLeastSubVersion(version):
    if version // 10 != python_version // 10:
        return False

    return python_version >= version


def doShowUnknownEncodingName():
    # Python 3.3.3 or higher does it, 3.4 always did.
    if python_version >= 333:
        return True

    # Python2.7 after 2.7.6 does it.
    if isAtLeastSubVersion(276):
        return True

    # Debian back ports do it.
    if  "2.7.5+" in sys.version or "3.3.2+" in sys.version:
        return True

    return False


def getErrorMessageExecWithNestedFunction():
    """ Error message of the concrete Python in case an exec occurs in a
        function that takes a closure variable.
    """

    assert python_version < 300

    # Need to use "exec" to detect the syntax error, pylint: disable=W0122

    try:
        exec("""
def f():
   exec ""
   def nested():
      return closure""")
    except SyntaxError as e:
        return e.message.replace("'f'", "'%s'")
