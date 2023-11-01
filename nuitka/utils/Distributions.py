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

    if not result:
        result = (distribution.metadata["Name"],)

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
    """Get the distribution names associated with a module name.

    This can be more than one in case of namespace modules.
    """

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


def getDistributionFromModuleName(module_name):
    """Get the distribution name associated with a module name."""
    distributions = getDistributionsFromModuleName(module_name)

    if not distributions:
        return None
    elif len(distributions) == 1:
        return distributions[0]
    else:
        return min(distributions, key=lambda dist: len(getDistributionName(dist)))


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


_distribution_to_installer = {}


def isDistributionCondaPackage(distribution_name):
    if not isAnacondaPython():
        return False

    return getDistributionInstallerName(distribution_name) == "conda"


def isDistributionPipPackage(distribution_name):
    return getDistributionInstallerName(distribution_name) == "pip"


def isDistributionSystemPackage(distribution_name):
    return not isDistributionPipPackage(
        distribution_name
    ) and not isDistributionCondaPackage(distribution_name)


def getDistributionInstallerName(distribution_name):
    if distribution_name not in _distribution_to_installer:
        distribution = getDistribution(distribution_name)

        if distribution is None:
            if distribution_name == "Pip":
                _distribution_to_installer[distribution_name] = "default"
            else:
                _distribution_to_installer[distribution_name] = "not_found"
        else:
            installer_name = distribution.read_text("INSTALLER")

            if installer_name:
                _distribution_to_installer[
                    distribution_name
                ] = installer_name.strip().lower()
            else:
                if hasattr(distribution, "_path"):
                    distribution_path_parts = str(getattr(distribution, "_path")).split(
                        "/"
                    )

                    if (
                        "dist-packages" in distribution_path_parts
                        and "local" not in distribution_path_parts
                    ):
                        _distribution_to_installer[distribution_name] = "Debian"
                    else:
                        _distribution_to_installer[distribution_name] = "Unknown"
                else:
                    _distribution_to_installer[distribution_name] = "Unknown"

    return _distribution_to_installer[distribution_name]


def getDistributionName(distribution):
    return distribution.metadata["Name"]


def getDistributionLicense(distribution):
    license_name = distribution.metadata["License"]

    if not license_name or license_name == "UNKNOWN":
        for classifier in (
            value
            for (key, value) in distribution.metadata.items()
            if "Classifier" in key
        ):
            parts = [part.strip() for part in classifier.split("::")]
            if not parts:
                continue

            if parts[0] == "License":
                license_name = parts[-1]
                break

    return license_name
