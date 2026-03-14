#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Cleanup of caches for Nuitka.

This is triggered by "--clean-cache=" usage, and can cleanup all kinds of
caches and is supposed to run before or instead of Nuitka compilation.
"""

import os

from nuitka.Tracing import cache_logger
from nuitka.utils.AppDirs import getCacheDir, removeCacheDir


def _cleanCacheDirectory(cache_name, cache_basename):
    from nuitka.options.Options import shallCleanCache

    if shallCleanCache(cache_name):
        cache_dir = getCacheDir(cache_basename, create=False)

        if os.path.exists(cache_dir):
            cache_logger.info(
                "Cleaning cache '%s' directory '%s'." % (cache_name, cache_dir)
            )
            removeCacheDir(
                cache_basename=cache_basename,
                logger=cache_logger,
                ignore_errors=False,
                extra_recommendation=None,
            )
            cache_logger.info("Done.")


def cleanCaches():
    _cleanCacheDirectory("ccache", "ccache")
    _cleanCacheDirectory("clcache", "clcache")
    _cleanCacheDirectory("zig", "zig")
    _cleanCacheDirectory("bytecode", "module-cache")
    _cleanCacheDirectory("dll-dependencies", "library_dependencies")


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
