#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Build directory local include paths for stable compiler command lines.

Nuitka adds absolute include paths derived from its own installation location
and the Python installation to the compiler command lines. When those
locations differ between machines, e.g. due to per-run package caches or
virtual environments, identical sources produce different compiler command
lines. That prevents sharing of "ccache" results between machines and makes
builds less reproducible.

This module replaces those paths with build directory local paths that go
through symbolic links of stable names, without changing what is compiled.
"""

import os

from nuitka.Tracing import scons_details_logger
from nuitka.utils.FileOperations import (
    getNormalizedPath,
    getNormalizedPathJoin,
    resetDirectory,
)

from .SconsUtils import getArgumentBool, getArgumentDefaulted

# spell-checker: ignore cpppath

stable_includes_dirname = "stable_includes"


def _isPathBelow(path, parent_path):
    """Check if a path is the parent path or located below it.

    Args:
        path: Path to check.
        parent_path: Potential parent path.

    Returns:
        bool: True if path is the parent path or below it.
    """
    path = os.path.normcase(os.path.normpath(path))
    parent_path = os.path.normcase(os.path.normpath(parent_path))

    return path == parent_path or path.startswith(parent_path + os.sep)


def _getSafeIncludeLinkName(name):
    """Get a file name that is safe to use as an include link name.

    Args:
        name: Base name to sanitize.

    Returns:
        str: Sanitized name.
    """
    result = "".join(
        character if character.isalnum() or character in "._-" else "_"
        for character in name
    )

    return result or "include"


def _createIncludeLink(stable_includes_dir, link_name, target_path):
    """Create a symbolic link for an include directory.

    Args:
        stable_includes_dir: Directory to create the link in.
        link_name: Name of the link below the directory.
        target_path: Absolute path the link points to.

    Returns:
        bool: True if the link was created, False otherwise.
    """
    try:
        os.symlink(target_path, getNormalizedPathJoin(stable_includes_dir, link_name))
    except (AttributeError, OSError):
        # Windows may lack permission for symbolic links, or "os.symlink" may
        # not exist at all there for older Python versions.
        return False

    return True


def _getIncludeRoots(env):
    """Get the roots of include paths that get stable names.

    Args:
        env: The Scons environment to work with.

    Returns:
        list of tuples of stable name and absolute directory.
    """
    roots = [("nuitka", os.path.dirname(env.nuitka_src))]

    python_include_path = getArgumentDefaulted("python_include_path", None)
    if python_include_path:
        roots.append(("python", python_include_path))

    return roots


def _getIncludeRootName(include_roots, include_path):
    """Get names to use for an include path below a known root.

    Args:
        include_roots: Sequence of stable name and absolute directory tuples.
        include_path: Absolute include path to check.

    Returns:
        Tuple of link name, link target and local name, or None if the include
        path is not below one of the roots.
    """
    for root_name, root_path in include_roots:
        if not _isPathBelow(include_path, root_path):
            continue

        relative_path = os.path.relpath(include_path, root_path)

        if relative_path == os.curdir:
            local_name = getNormalizedPathJoin(stable_includes_dirname, root_name)
        else:
            local_name = getNormalizedPathJoin(
                stable_includes_dirname, root_name, relative_path
            )

        return root_name, root_path, local_name

    return None


def _getIncludeFallbackName(
    include_path, reserved_link_names, failed_link_names, link_targets
):
    """Get names to use for an include path without a known root.

    Args:
        include_path: Absolute include path to check.
        reserved_link_names: Names that must not be used for fallbacks.
        failed_link_names: Names that already failed to be linked.
        link_targets: Mapping of created link names to their target path.

    Returns:
        Tuple of link name, link target and local name.
    """
    base_name = _getSafeIncludeLinkName(
        os.path.basename(getNormalizedPath(include_path))
    )

    link_name = base_name

    counter = 2
    while (
        link_name in reserved_link_names
        or link_name in failed_link_names
        or (link_name in link_targets and link_targets[link_name] != include_path)
    ):
        link_name = "%s-%d" % (base_name, counter)
        counter += 1

    return (
        link_name,
        include_path,
        getNormalizedPathJoin(stable_includes_dirname, link_name),
    )


def makeIncludePathsStable(env):
    """Replace external include paths with build directory local ones.

    Notes:
        This creates a "stable_includes" directory in the build directory with
        symbolic links, and uses those relative paths instead of the original
        absolute paths in the compiler command lines. The link names are
        derived from stable roots and base names only, so they are the same on
        every machine, while the linked to directories are not.

    Args:
        env: The Scons environment to work with.
    """
    if env.msvc_mode:
        return

    # Debugger mode insists on full names for a better debugging experience.
    if getArgumentBool("full_names", False):
        return

    include_paths = env["CPPPATH"]

    stable_includes_dir = getNormalizedPathJoin(env.source_dir, stable_includes_dirname)

    resetDirectory(
        path=stable_includes_dir,
        logger=scons_details_logger,
        ignore_errors=False,
        extra_recommendation=None,
    )

    include_roots = _getIncludeRoots(env)

    # Names of the roots are not available for base name derived links.
    reserved_link_names = set(root_name for root_name, _root_path in include_roots)

    link_targets = {}
    failed_link_names = set()

    new_include_paths = []

    for include_path in include_paths:
        if not os.path.isabs(include_path):
            new_include_paths.append(include_path)
            continue

        if not os.path.isdir(include_path):
            new_include_paths.append(include_path)
            continue

        link_name_data = _getIncludeRootName(
            include_roots=include_roots, include_path=include_path
        )

        if link_name_data is None:
            link_name_data = _getIncludeFallbackName(
                include_path=include_path,
                reserved_link_names=reserved_link_names,
                failed_link_names=failed_link_names,
                link_targets=link_targets,
            )

        link_name, link_target, local_name = link_name_data

        if link_name in failed_link_names:
            new_include_paths.append(include_path)
            continue

        if link_name not in link_targets:
            if not _createIncludeLink(
                stable_includes_dir=stable_includes_dir,
                link_name=link_name,
                target_path=link_target,
            ):
                failed_link_names.add(link_name)
                new_include_paths.append(include_path)
                continue

            link_targets[link_name] = link_target

        new_include_paths.append(local_name)

    if link_targets:
        scons_details_logger.info(
            "Using %d build local include paths from '%s'."
            % (len(link_targets), stable_includes_dir)
        )

    env["CPPPATH"] = new_include_paths


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
