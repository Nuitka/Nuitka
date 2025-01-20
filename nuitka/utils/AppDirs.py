#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Wrapper around appdirs from PyPI

We do not assume to be installed and fallback to an inline copy and if that
is not installed, we use our own code for best effort.
"""

from __future__ import absolute_import

import errno
import os
import tempfile

from nuitka.__past__ import (  # pylint: disable=redefined-builtin
    PermissionError,
)
from nuitka.Tracing import general

from .FileOperations import makePath
from .Importing import importFromInlineCopy

appdirs = importFromInlineCopy("appdirs", must_exist=False, delete_module=True)

if appdirs is None:
    try:
        import appdirs  # pylint: disable=I0021,import-error
    except ImportError:
        appdirs = None


def getAppdirsModule():
    return appdirs


_cache_dir = None


def _getCacheDir():
    global _cache_dir  # singleton, pylint: disable=global-statement

    if _cache_dir is None:
        _cache_dir = os.getenv("NUITKA_CACHE_DIR")

        if _cache_dir:
            _cache_dir = os.path.expanduser(_cache_dir)
        elif appdirs is not None:
            _cache_dir = appdirs.user_cache_dir("Nuitka", None)
        else:
            _cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "Nuitka")

        # For people that build with HOME set this, e.g. Debian, and other package
        # managers. spell-checker: ignore sbuild
        if _cache_dir.startswith(
            ("/nonexistent/", "/sbuild-nonexistent/", "/homeless-shelter/")
        ):
            _cache_dir = os.path.join(tempfile.gettempdir(), "Nuitka")

        try:
            makePath(_cache_dir)
        except PermissionError as e:
            if e.errno != errno.EACCES:
                raise

            general.sysexit(
                """\
Error, failed to create cache directory '%s'. If this is due to a special environment, \
please consider making a PR for a general solution that adds support for it, or use \
'NUITKA_CACHE_DIR' set to a writable directory."""
                % _cache_dir
            )

    return _cache_dir


def getCacheDirEnvironmentVariableName(cache_basename):
    env_name = cache_basename.replace("-", "_").upper()

    return "NUITKA_CACHE_DIR_" + env_name


def getCacheDir(cache_basename):
    cache_dir = os.getenv(getCacheDirEnvironmentVariableName(cache_basename))
    if cache_dir is None:
        cache_dir = os.path.join(_getCacheDir(), cache_basename)

    return cache_dir


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
