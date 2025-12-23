#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Caching of Python AST trees.

This module provides persistent caching of parsed Python AST trees.
By caching the AST, we can skip expensive parsing for unchanged Python source files.

The cache is content-dependent only, so optimization flags and compilation modes
don't invalidate it. Cache keys are based on:
- Source code content (SHA256 hash)
- Nuitka version
- Python version
- Plugin contributions
"""

import os
import pickle
import sys
import tempfile

from nuitka.plugins.Hooks import getPluginsCacheContributionValues
from nuitka.Tracing import general
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import makePath, replaceFileAtomic
from nuitka.utils.Hashing import Hash, getStringHash
from nuitka.utils.Json import loadJsonFromFilename, writeJsonToFilename
from nuitka.Version import version_string


def getSourceASTCacheDir():
    """Get the directory where AST caches are stored.

    Security note: The cache directory must be trusted (user-only, non-world-writable)
    because cached ASTs are loaded via pickle.load, which can execute arbitrary code.
    By default, this uses a per-user cache directory. If overridden via
    NUITKA_CACHE_DIR_SOURCE_AST_CACHE, ensure it points to a secure location.
    """
    return getCacheDir("source-ast-cache")


def _getCacheFilename(cache_name, extension):
    """Get the full path for a cache file."""
    return os.path.join(getSourceASTCacheDir(), "%s.%s" % (cache_name, extension))


def makeCacheName(module_name, source_code):
    """Generate a cache name based on module name, config, and source content.

    The module name is hashed to keep cache paths short even for deeply
    nested or very long module names, avoiding filesystem path length limits.

    Args:
        module_name: ModuleName object
        source_code: String containing the source code

    Returns:
        String in format: module_name_hash@config_hash@source_hash
    """
    module_config_hash = _getModuleConfigHash(module_name)
    module_name_hash = getStringHash(module_name.asString())

    return (
        module_name_hash
        + "@"
        + module_config_hash
        + "@"
        + getStringHash(source_code)
    )


def _getModuleConfigHash(full_name):
    """Calculate hash value for configuration affecting module compilation.

    This includes:
    - Plugin contributions (plugins can modify source or tree building)
    - Nuitka version (different versions may build different trees)
    - Python version (AST differs between Python versions)

    Args:
        full_name: ModuleName object

    Returns:
        Hex digest string of the configuration hash
    """
    hash_value = Hash()

    # Plugins may change their influence
    hash_value.updateFromValues(*getPluginsCacheContributionValues(full_name))

    # Take Nuitka and Python version into account as well
    hash_value.updateFromValues(version_string, sys.version)

    return hash_value.asHexDigest()


# Bump this if format is changed or enhanced implementation might create different trees
_cache_format_version = 1


# Statistics tracking
_cache_hits = 0
_cache_misses = 0
_cache_restored_modules = []


def _validateCacheMetadata(meta_filename, tree_filename, module_name):
    """Load and validate AST cache metadata.

    This centralizes metadata validation logic used by both cache probing
    and loading functions.

    Args:
        meta_filename: Path to the metadata JSON file
        tree_filename: Path to the pickled AST file
        module_name: ModuleName object

    Returns:
        dict or None: Validated metadata dict if cache is valid, None otherwise
    """
    # Check if both files exist
    if not os.path.exists(tree_filename) or not os.path.exists(meta_filename):
        return None

    # Load and validate metadata
    try:
        metadata = loadJsonFromFilename(meta_filename)
        if metadata is None:
            return None

        # Verify format version
        if metadata.get("file_format_version") != _cache_format_version:
            return None

        # Verify module name matches
        if metadata.get("module_name") != module_name.asString():
            return None

        return metadata
    except Exception:
        return None


def getCachedAST(module_name, source_code):
    """Load a cached AST from disk.

    Args:
        module_name: ModuleName object
        source_code: String containing the source code

    Returns:
        AST object if cache exists and is valid, None otherwise
    """
    global _cache_hits, _cache_misses, _cache_restored_modules

    cache_name = makeCacheName(module_name, source_code)
    tree_filename = _getCacheFilename(cache_name, "pkl")
    meta_filename = _getCacheFilename(cache_name, "json")

    # Validate cache metadata using shared helper
    metadata = _validateCacheMetadata(meta_filename, tree_filename, module_name)
    if metadata is None:
        _cache_misses += 1
        return None

    # Load the pickled AST
    try:
        with open(tree_filename, "rb") as f:
            ast_tree = pickle.load(f)

        # Record cache hit
        _cache_hits += 1
        _cache_restored_modules.append(module_name.asString())

        return ast_tree

    except Exception as e:
        general.warning(
            "Failed to load cached tree for module '%s': %s" % (module_name, e)
        )
        _cache_misses += 1
        return None


def writeCachedAST(module_name, source_code, ast_tree):
    """Write an AST to the cache.

    Args:
        module_name: ModuleName object
        source_code: String containing the source code
        ast_tree: The Python AST object to cache
    """
    cache_name = makeCacheName(module_name, source_code)
    tree_filename = _getCacheFilename(cache_name, "pkl")
    meta_filename = _getCacheFilename(cache_name, "json")

    try:
        # Create cache directory if it doesn't exist
        cache_dir = os.path.dirname(tree_filename)
        makePath(cache_dir)

        # Serialize the AST to a temporary file, then atomically move it
        fd, temp_tree_filename = tempfile.mkstemp(dir=cache_dir, suffix=".pkl.tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                pickle.dump(ast_tree, f, protocol=pickle.HIGHEST_PROTOCOL)
            replaceFileAtomic(temp_tree_filename, tree_filename)
        except Exception:
            # Clean up temp file if something went wrong
            if os.path.exists(temp_tree_filename):
                os.unlink(temp_tree_filename)
            raise

        # Write metadata
        metadata = {
            "file_format_version": _cache_format_version,
            "module_name": module_name.asString(),
            "nuitka_version": version_string,
            "python_version": sys.version,
        }
        writeJsonToFilename(filename=meta_filename, contents=metadata)

    except Exception as e:
        general.warning(
            "Failed to cache AST for '%s': %s" % (module_name, e)
        )


def getCacheStatistics():
    """Get cache hit/miss statistics.

    Returns:
        Dictionary with cache statistics
    """
    return {
        "hits": _cache_hits,
        "misses": _cache_misses,
        "hit_rate": (
            _cache_hits / (_cache_hits + _cache_misses)
            if (_cache_hits + _cache_misses) > 0
            else 0.0
        ),
        "restored_modules": _cache_restored_modules,
    }


def reportCacheStatistics():
    """Report cache statistics to the user."""
    stats = getCacheStatistics()

    total = stats["hits"] + stats["misses"]
    if total > 0:
        general.info(
            "Source AST cache: %d hits, %d misses (%.1f%% hit rate)"
            % (stats["hits"], stats["misses"], stats["hit_rate"] * 100)
        )

        if stats["restored_modules"]:
            general.info(
                "Restored %d module(s) AST from cache: %s"
                % (
                    len(stats["restored_modules"]),
                    ", ".join(stats["restored_modules"][:10])
                    + ("..." if len(stats["restored_modules"]) > 10 else "")
                )
            )


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
