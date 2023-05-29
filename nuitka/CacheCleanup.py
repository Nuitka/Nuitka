#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Cleanup of caches for Nuitka.

This is triggered by "--clean-cache=" usage, and can cleanup all kinds of
caches and is supposed to run before or instead of Nuitka compilation.
"""

import os

from nuitka.BytecodeCaching import getBytecodeCacheDir
from nuitka.Tracing import cache_logger
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import removeDirectory


def _cleanCacheDirectory(cache_name, cache_dir):
    from nuitka.Options import shallCleanCache

    if shallCleanCache(cache_name) and os.path.exists(cache_dir):
        cache_logger.info(
            "Cleaning cache '%s' directory '%s'." % (cache_name, cache_dir)
        )
        removeDirectory(cache_dir, ignore_errors=False)
        cache_logger.info("Done.")


def cleanCaches():
    _cleanCacheDirectory("ccache", os.path.join(getCacheDir(), "ccache"))
    _cleanCacheDirectory("clcache", os.path.join(getCacheDir(), "clcache"))
    _cleanCacheDirectory("bytecode", getBytecodeCacheDir())
    _cleanCacheDirectory(
        "dll-dependencies", os.path.join(getCacheDir(), "library_dependencies")
    )
