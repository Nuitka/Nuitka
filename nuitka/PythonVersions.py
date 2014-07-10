#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
the numbers, and attempts to give them meaningful names.

"""

import sys

from nuitka.Options import isFullCompat


def _getPythonVersion():
    big, major, minor = sys.version_info[0:3]

    return big * 100 + major * 10 + minor

python_version = _getPythonVersion()

def isAtLeastSubVersion(version):
    if version // 10 != python_version // 10:
        return False

    return python_version >= version


def doShowUnknownEncodingName():
    # It's best to do it.
    if not isFullCompat():
        return True

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

def doForceShowEncodingProblem():
    # Best to show newest message.
    if not isFullCompat():
        return True

    if isAtLeastSubVersion(277):
        return True

    if isAtLeastSubVersion(268):
        return True

    return False