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
""" Tools for accessing distributions and resolving package names for them. """

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.PythonFlavors import isAnacondaPython
from nuitka.PythonVersions import python_version

from .ModuleNames import ModuleName, checkModuleName

_package_to_distribution = None


def getDistributionTopLevelPackageNames(distribution):
    """Returns the top level package names for a distribution."""
    top_level_txt = distribution.read_text("top_level.txt")

    if top_level_txt:
        result = top_level_txt.split()
        result = [dirname.replace("/", ".") for dirname in result]
    else:
        result = OrderedSet()

        for filename in distribution.files or ():
            filename = filename.as_posix()

            if not filename.endswith(".py"):
                continue

            if filename.startswith("."):
                continue

            filename = filename[:-3]

            result.add(filename.split("/")[0])

    return tuple(result)


def _initPackageToDistributionName():
    try:
        try:
            from importlib.metadata import distributions
        except ImportError:
            from importlib_metadata import distributions
    except ImportError:
        return {}

    # Cyclic dependency

    result = {}

    for distribution in distributions():
        for package_name in getDistributionTopLevelPackageNames(distribution):
            # Protect against buggy packages.
            if not checkModuleName(package_name):
                continue

            package_name = ModuleName(package_name)

            if package_name not in result:
                result[package_name] = set()

            result[package_name].add(distribution)

    return result


def getDistributionsFromModuleName(module_name):
    """Get the distribution name associated with a module name."""

    # Cached result, pylint: disable=global-statement

    global _package_to_distribution
    if _package_to_distribution is None:
        _package_to_distribution = _initPackageToDistributionName()

    return tuple(
        sorted(
            _package_to_distribution.get(module_name, ()),
            key=lambda dist: dist.metadata["Name"],
        )
    )


def getDistribution(distribution_name):
    """Get a distribution by name."""
    try:
        if python_version >= 0x380:
            from importlib import metadata
        else:
            import importlib_metadata as metadata
    except ImportError:
        return None

    try:
        return metadata.distribution(distribution_name)
    except metadata.PackageNotFoundError:
        # If not found, lets assume package name was given, and resolve to
        # the distribution.
        dists = getDistributionsFromModuleName(distribution_name)

        if len(dists) == 1:
            return dists[0]

        return None


_distribution_to_conda_package = {}


def isDistributionCondaPackage(distribution_name):
    if not isAnacondaPython():
        return False

    if distribution_name not in _distribution_to_conda_package:
        distribution = getDistribution(distribution_name)

        if distribution is None:
            _distribution_to_conda_package[distribution_name] = False
        else:
            installer_txt = distribution.read_text("INSTALLER") or ""

            _distribution_to_conda_package[distribution_name] = (
                installer_txt.upper() == "CONDA"
            )

    return _distribution_to_conda_package[distribution_name]
