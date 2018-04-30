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
""" Wrapper around appdir from PyPI

We do not assume to be installed and fallback to an inline copy and if that
is not installed, we use our own code for best effort.
"""

from __future__ import absolute_import

import os
import sys
import tempfile

from .FileOperations import makePath

try:
    import appdirs
except ImportError:
    # Temporarily add the inline copy of appdir to the import path.
    sys.path.append(
        os.path.join(
            os.path.dirname(__file__),
            "..", "build", "inline_copy", "appdirs"
        )
    )

    # Handle case without inline copy too.
    try:
        import appdirs
    except ImportError:
        appdirs = None

    # Do not forget to remove it again.
    del sys.path[-1]


def getCacheDir():
    if appdirs is not None:
        result = appdirs.user_cache_dir("Nuitka", None)
    else:
        result = os.path.join(os.path.expanduser('~'), ".cache", "Nuitka")

    # For people that build with HOME set this, e.g. Debian.
    if result.startswith(("/nonexistent/", "/sbuild-nonexistent/")):
        result = os.path.join(tempfile.gettempdir(), "Nuitka")

    makePath(result)
    return result


def getAppDir():
    if appdirs is not None:
        result = appdirs.user_data_dir("Nuitka", None)
    else:
        result = os.path.join(os.path.expanduser('~'), ".config", "Nuitka")

    # For people that build with HOME set this, e.g. Debian.
    if result.startswith(("/nonexistent/", "/sbuild-nonexistent/")):
        result = os.path.join(tempfile.gettempdir(), "Nuitka")

    makePath(result)
    return result
