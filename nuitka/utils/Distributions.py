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

import os

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Options import isExperimental
from nuitka.PythonFlavors import isAnacondaPython
from nuitka.PythonVersions import python_version

from .FileOperations import searchPrefixPath
from .Importing import getModuleNameAndKindFromFilenameSuffix
from .ModuleNames import ModuleName, checkModuleName
from .Utils import isLinux

_package_to_distribution = None


def getDistributionFiles(distribution):
    if hasattr(distribution, "files"):
        for filename in distribution.files or ():
            filename = filename.as_posix()

            yield filename
    else:
        record_data = _getDistributionMetadataFileContents(distribution, "RECORD")

        if record_data is not None:
            for line in record_data.splitlines():
                filename = line.split(",", 1)[0]

                yield filename


def _getDistributionMetadataFileContents(distribution, filename):
    try:
        if hasattr(distribution, "read_text"):
            result = distribution.read_text(filename)
        else:
            result = "\n".join(distribution.get_metadata_lines(filename))

        return result
    except (FileNotFoundError, KeyError):
        return None


def getDistributionTopLevelPackageNames(distribution):
    """Returns the top level package names for a distribution."""
    top_level_txt = _getDistributionMetadataFileContents(distribution, "top_level.txt")

    if top_level_txt is not None:
        result = [dirname.replace("/", ".") for dirname in top_level_txt.splitlines()]
    else:
        # If the file is not present, fall back to scanning all files in the
        # distribution.
        result = OrderedSet()

        for filename in getDistributionFiles(distribution):
            if filename.startswith("."):
                continue

            first_path_element, _, remainder = filename.partition("/")

            if first_path_element.endswith("dist-info"):
                continue
            if first_path_element == "__pycache__":
                continue

            if remainder:
                module_name = ModuleName(first_path_element)
            else:
                module_name, _kind = getModuleNameAndKindFromFilenameSuffix(
                    first_path_element
                )

                # Ignore top level files that are not modules.
                if module_name is None:
                    continue

            result.add(module_name)

        result = OrderedSet(
            package_name.asString()
            for package_name in result
            if not any(
                package_name.isBelowNamespace(other_package_name)
                for other_package_name in result
            )
        )

    if not result:
        result = (getDistributionName(distribution),)

    return tuple(result)


def _get_pkg_resource_distributions():
    """Small replacement of distributions() of importlib.metadata that uses pkg_resources"""

    # Prepare "site" for the "pip" module to find what it wants.
    import site

    if _user_site_directory is not None:
        site.USER_SITE = _user_site_directory

    # pip and vendored pkg_resources are optional of course, but of course very
    # omnipresent generally, so we don't handle failure here.

    # pylint: disable=I0021,no-name-in-module
    from pip._vendor import pkg_resources

    return lambda: pkg_resources.working_set


def _initPackageToDistributionName():
    try:
        if isExperimental("force-pkg-resources-metadata"):
            raise ImportError

        try:
            from importlib.metadata import distributions
        except ImportError:
            from importlib_metadata import distributions

    except (ImportError, SyntaxError):
        try:
            distributions = _get_pkg_resource_distributions()
        except ImportError:
            # No pip installed, not very many distributions in that case.
            distributions = lambda: ()

    # Cyclic dependency
    result = {}

    for distribution in distributions():
        distribution_name = getDistributionName(distribution)

        for package_name in getDistributionTopLevelPackageNames(distribution):
            # Protect against buggy packages.
            if not checkModuleName(package_name):
                continue

            package_name = ModuleName(package_name)

            if package_name not in result:
                result[package_name] = set()

            # Skip duplicates, e.g. user package vs. site package installation.
            if any(
                distribution_name == getDistributionName(dist)
                for dist in result[package_name]
            ):
                continue

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

    # Go upwards until we find something, such that contained module names are
    # usable too.
    while (
        module_name not in _package_to_distribution
        and module_name.getPackageName() is not None
    ):
        module_name = module_name.getPackageName()

    return tuple(
        sorted(
            _package_to_distribution.get(module_name, ()),
            key=getDistributionName,
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
        if isExperimental("force-pkg-resources-metadata"):
            raise ImportError

        if python_version >= 0x380:
            from importlib import metadata
        else:
            import importlib_metadata as metadata
    except ImportError:
        from pip._vendor.pkg_resources import (
            DistributionNotFound,
            get_distribution,
        )

        try:
            return get_distribution(distribution_name)
        except DistributionNotFound:
            return None
    else:
        try:
            return metadata.distribution(distribution_name)
        except metadata.PackageNotFoundError:
            return None


_distribution_to_installer = {}


def isDistributionCondaPackage(distribution_name):
    if not isAnacondaPython():
        return False

    return getDistributionInstallerName(distribution_name) == "conda"


def isDistributionPipPackage(distribution_name):
    return getDistributionInstallerName(distribution_name) == "pip"


def isDistributionSystemPackage(distribution_name):
    result = not isDistributionPipPackage(
        distribution_name
    ) and not isDistributionCondaPackage(distribution_name)

    # This should only ever happen on Linux, lets know when it does happen
    # elsewhere, since that is most probably a bug in our installer detection on
    # non-Linux as well.
    if result:
        assert isLinux(), (
            distribution_name,
            getDistributionInstallerName(distribution_name),
        )

    return result


_pdm_dir_cache = {}


def isPdmPackageInstallation(distribution):
    distribution_path = getattr(distribution, "_path")
    if distribution_path is None:
        return False

    site_packages_path = searchPrefixPath(str(distribution_path), "site-packages")
    if site_packages_path is None:
        return False

    candidate = os.path.join(site_packages_path, "..", "..", "pyvenv.cfg")

    result = _pdm_dir_cache.get(candidate)
    if result is None:
        _pdm_dir_cache[candidate] = os.path.exists(candidate)

    return _pdm_dir_cache[candidate]


def getDistributionInstallerName(distribution_name):
    """Get the installer name from a distribution object.

    We might care of pip, anaconda, Debian, or whatever installed a
    package.
    """
    if distribution_name not in _distribution_to_installer:
        distribution = getDistribution(distribution_name)

        if distribution is None:
            if distribution_name == "Pip":
                _distribution_to_installer[distribution_name] = "default"
            else:
                _distribution_to_installer[distribution_name] = "not_found"
        else:
            installer_name = _getDistributionMetadataFileContents(
                distribution, "INSTALLER"
            )

            if installer_name:
                _distribution_to_installer[
                    distribution_name
                ] = installer_name.strip().lower()
            elif isAnacondaPython():
                _distribution_to_installer[distribution_name] = "conda"
            elif isPdmPackageInstallation(distribution):
                return "pip"
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
    """Get the distribution name from a distribution object.

    We use importlib.metadata and pkg_resources version tuples interchangeable
    and this is to abstract the difference is how to look up the name from
    one.
    """

    if hasattr(distribution, "metadata"):
        return distribution.metadata["Name"]
    else:
        return distribution.project_name


def getDistributionVersion(distribution):
    """Get the distribution version string from a distribution object.

    We use importlib.metadata and pkg_resources version tuples interchangeable
    and this is to abstract the difference is how to look up the version from
    one.
    """
    # Avoiding use of public interface for pkg_resources, pylint: disable=protected-access
    if hasattr(distribution, "metadata"):
        return distribution.metadata["Version"]
    else:
        return distribution._version


def getDistributionLicense(distribution):
    """Get the distribution license from a distribution object."""

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


# User site directory if any
_user_site_directory = None


def setUserSiteDirectory(user_site_directory):
    global _user_site_directory  # singleton, pylint: disable=global-statement
    _user_site_directory = user_site_directory
