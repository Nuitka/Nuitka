#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Requirement parsing and checking helpers."""

import os
import re

from .Distributions import getDistribution, getDistributionVersion
from .RequirementsParser import FallbackRequirement
from .RequirementsParser import (
    InvalidRequirement as FallbackInvalidRequirement,
)


def _normalizeProjectRequirementText(requirement_text):
    # Poetry renders wildcard versions as "(*)"; that is not valid PEP 508.
    return re.sub(r"\s*\(\*\)", "", requirement_text)


def _isIgnoredProjectRequirementName(requirement_name):
    return requirement_name.lower() in ("python", "nuitka")


def _getRequirementParser():
    """Get the classes for parsing PEP 508 requirements.

    Notes:
        'packaging' is not a dependency of Nuitka, and 'pip' is not installed
        in e.g. a 'uv venv', so both have to be optional. The fallback is the
        compact implementation in 'nuitka.utils.RequirementsParser'.

    Returns:
        Tuple of 'InvalidRequirement' and 'Requirement' classes.
    """
    try:
        from packaging.requirements import InvalidRequirement, Requirement
    except ImportError:
        try:
            from pip._vendor.packaging.requirements import (
                InvalidRequirement,
                Requirement,
            )
        except ImportError:
            return FallbackInvalidRequirement, FallbackRequirement

    return InvalidRequirement, Requirement


def getUnmetRequirements(requirements):
    """Get requirements that are not satisfied by installed distributions.

    Args:
        requirements: Sequence of requirement strings.

    Returns:
        List of requirement descriptions that are missing or have an
        unsatisfied version.
    """
    if not requirements:
        return []

    InvalidRequirement, Requirement = _getRequirementParser()

    missing = []

    for requirement_text in requirements:
        requirement_text = _normalizeProjectRequirementText(requirement_text)

        try:
            requirement = Requirement(requirement_text)
        except InvalidRequirement:
            missing.append("%s (invalid requirement)" % requirement_text)
            continue

        if _isIgnoredProjectRequirementName(requirement.name):
            continue

        if requirement.marker is not None:
            try:
                if not requirement.marker.evaluate():
                    continue
            except Exception:  # pylint: disable=broad-except
                # If the marker cannot be evaluated, check the requirement
                # rather than silently ignoring it.
                pass

        distribution = getDistribution(requirement.name)

        if distribution is None:
            missing.append(requirement_text)
            continue

        installed_version = getDistributionVersion(distribution)

        if requirement.specifier:
            try:
                if not requirement.specifier.contains(
                    installed_version, prereleases=True
                ):
                    missing.append(
                        "%s (installed %s)" % (requirement_text, installed_version)
                    )
            except Exception:  # pylint: disable=broad-except
                missing.append(
                    "%s (installed version %r is invalid)"
                    % (requirement_text, installed_version)
                )

    return missing


def isNuitkaInstallRequire(requirement):
    """Check if a requirement is Nuitka.

    Args:
        requirement (str): The requirement string.

    Returns:
        bool: True if the requirement is Nuitka, False otherwise.
    """
    # Check if it starts with "nuitka" followed by end of string or a non-name
    # character, valid name chars: [a-z0-9_.-]
    if re.match(r"^nuitka(?:[<>=!~;@\s]|$)", requirement.lower()):
        return True

    # Check for a file URL pointing to Nuitka.
    match = re.search(r"file://([^;\s]+)", requirement)
    if match:
        path = match.group(1)

        if os.path.exists(path) and os.path.isdir(path):
            if os.path.exists(
                os.path.join(path, "nuitka", "MainControl.py")
            ) and os.path.exists(os.path.join(path, "nuitka", "Version.py")):
                return True

    # Check for GitHub URLs pointing to Nuitka or Nuitka extensions.
    if re.search(
        r"github\.com/Nuitka/Nuitka(?:-[a-zA-Z0-9_-]+)?(?:\.git|/|#|@|$)", requirement
    ):
        return True

    return False


def filterInstallRequires(install_requires):
    """Filter out Nuitka from install_requires.

    Args:
        install_requires (list): List of install requirements.

    Returns:
        list: Filtered list of install requirements.
    """
    if install_requires is None:
        return []

    return [req for req in install_requires if not isNuitkaInstallRequire(req)]


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
