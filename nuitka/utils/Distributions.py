#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Tools for accessing distributions and resolving package names for them. """

import os

from nuitka.__past__ import (  # pylint: disable=redefined-builtin
    FileNotFoundError,
    unicode,
)
from nuitka.containers.Namedtuples import makeNamedtupleClass
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Options import isExperimental
from nuitka.PythonFlavors import (
    isAnacondaPython,
    isMSYS2MingwPython,
    isPosixWindows,
)
from nuitka.PythonVersions import python_version
from nuitka.Tracing import metadata_logger

from .FileOperations import searchPrefixPath
from .Importing import getModuleNameAndKindFromFilenameSuffix
from .ModuleNames import ModuleName, checkModuleName
from .Utils import isMacOS, isWin32Windows

_package_to_distribution = None


def getDistributionFiles(distribution):
    try:
        hasattr_files = hasattr(distribution, "files")
    except OSError:
        metadata_logger.warning(
            """\
Error, failure to access '.files()' of distribution '%s', path '%s', this \
is typically caused by corruption of its installation."""
            % (distribution, _getDistributionPath(distribution))
        )
        hasattr_files = False

    if hasattr_files:
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
    except OSError:
        metadata_logger.warning(
            """\
Error, failure to access '%s' of distribution '%s', path '%s', this \
is typically caused by corruption of its installation."""
            % (filename, distribution, _getDistributionPath(distribution))
        )
        return None


def _getDistributionInstallerFileContents(distribution):
    installer_name = _getDistributionMetadataFileContents(distribution, "INSTALLER")

    if installer_name:
        installer_name = installer_name.strip().lower()

    return installer_name


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
            if not checkModuleName(first_path_element) or first_path_element == ".":
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


def _get_pkg_resources_module():
    # pip and vendored pkg_resources are optional of course, but of course very
    # omnipresent generally, so we don't handle failure here.

    # pylint: disable=I0021,no-name-in-module
    from pip._vendor import pkg_resources

    return pkg_resources


def _get_pkg_resource_distributions():
    """Small replacement of distributions() of importlib.metadata that uses pkg_resources"""

    # Prepare "site" for the "pip" module to find what it wants.
    import site

    if _user_site_directory is not None:
        site.USER_SITE = _user_site_directory

    pkg_resources = _get_pkg_resources_module()

    return lambda: pkg_resources.working_set


def _initPackageToDistributionName():
    try:
        if isExperimental("force-pkg-resources-metadata"):
            raise ImportError

        try:
            from importlib.metadata import distributions
        except ImportError:
            from importlib_metadata import distributions

    except (ImportError, SyntaxError, RuntimeError):
        try:
            distributions = _get_pkg_resource_distributions()
        except ImportError:
            # No pip installed, not very many distributions in that case.
            distributions = lambda: ()

    # Cyclic dependency
    result = {}

    for distribution in distributions():
        distribution_name = getDistributionName(distribution)

        if distribution_name is None:
            metadata_logger.warning(
                """\
Error, failure to detect name of distribution '%s', path '%s', this \
is typically caused by corruption of its installation."""
                % (distribution, _getDistributionPath(distribution))
            )
            continue

        assert isValidDistributionName(distribution_name), (
            distribution,
            distribution_name,
            _getDistributionPath(distribution),
        )

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

    module_name = ModuleName(module_name)
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
    assert isValidDistributionName(distribution_name), distribution_name

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


def isDistributionMsys2Package(distribution_name):
    if not isAnacondaPython():
        return False

    return getDistributionInstallerName(distribution_name).startswith("MSYS2")


def isDistributionPipPackage(distribution_name):
    return getDistributionInstallerName(distribution_name) == "pip"


def isDistributionPoetryPackage(distribution_name):
    return getDistributionInstallerName(distribution_name).startswith("poetry")


def isDistributionSystemPackage(distribution_name):
    return (
        not isMacOS()
        and not isWin32Windows()
        and not isDistributionPipPackage(distribution_name)
        and not isDistributionPoetryPackage(distribution_name)
        and not isDistributionCondaPackage(distribution_name)
    )


_pdm_dir_cache = {}


def _getDistributionPath(distribution):
    return getattr(distribution, "_path", None)


def isPdmPackageInstallation(distribution):
    distribution_path = _getDistributionPath(distribution)
    if distribution_path is None:
        return False

    site_packages_path = searchPrefixPath(str(distribution_path), "site-packages")
    if site_packages_path is None:
        return False

    # spell-checker: ignore pyvenv
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

    # many cases due to fallback variants, pylint: disable=too-many-branches

    if distribution_name not in _distribution_to_installer:
        distribution = getDistribution(distribution_name)

        if distribution is None:
            if distribution_name == "Pip":
                _distribution_to_installer[distribution_name] = "default"
            else:
                _distribution_to_installer[distribution_name] = "not_found"
        else:
            installer_name = _getDistributionInstallerFileContents(distribution)

            if installer_name:
                _distribution_to_installer[distribution_name] = installer_name
            elif isAnacondaPython():
                _distribution_to_installer[distribution_name] = "conda"
            elif isPdmPackageInstallation(distribution):
                _distribution_to_installer[distribution_name] = "pip"
            elif isMSYS2MingwPython():
                _distribution_to_installer[distribution_name] = "MSYS2 MinGW"
            elif isPosixWindows():
                _distribution_to_installer[distribution_name] = "MSYS2 Posix"
            else:
                distribution_path = _getDistributionPath(distribution)
                if distribution_path is not None:
                    distribution_path_parts = str(distribution_path).split("/")

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


def isValidDistributionName(distribution_name):
    return type(distribution_name) in (str, unicode)


def getDistributionName(distribution):
    """Get the distribution name from a distribution object.

    We use importlib.metadata and pkg_resources version tuples interchangeable
    and this is to abstract the difference is how to look up the name from
    one.
    """

    if hasattr(distribution, "metadata"):
        result = distribution.metadata["Name"]

        if result is None:
            installer_name = _getDistributionInstallerFileContents(distribution)

            if installer_name == "debian":
                distribution_path = _getDistributionPath(distribution)

                if distribution_path is not None:
                    dir_name = os.path.basename(distribution_path)

                    if dir_name.endswith(".dist-info"):
                        dir_name = dir_name[:-10]

                        result = dir_name.rsplit("-", 1)[0]
    else:
        result = distribution.project_name

    return result


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


def _getEntryPointGroup(group_name):
    try:
        if isExperimental("force-pkg-resources-metadata"):
            raise ImportError

        try:
            from importlib.metadata import entry_points
        except ImportError:
            from importlib_metadata import entry_points

    except (ImportError, SyntaxError, RuntimeError):
        pkg_resources = _get_pkg_resources_module()

        entry_points = pkg_resources.entry_points

    return entry_points(group=group_name)


EntryPointDescription = makeNamedtupleClass(
    "EntryPointDescription",
    (
        "distribution_name",
        "distribution",
        "module_name",
    ),
)


def getEntryPointGroup(group_name):
    result = OrderedSet()

    for entry_point in _getEntryPointGroup(group_name):
        result.add(
            EntryPointDescription(
                distribution_name=getDistributionName(entry_point.dist),
                distribution=entry_point.dist,
                module_name=ModuleName(entry_point.module),
            )
        )

    return result


# User site directory if any
_user_site_directory = None


def setUserSiteDirectory(user_site_directory):
    global _user_site_directory  # singleton, pylint: disable=global-statement
    _user_site_directory = user_site_directory


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
