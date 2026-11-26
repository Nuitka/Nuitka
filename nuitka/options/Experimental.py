#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Experimental feature indications.

This is a low level module without dependencies, so it can be used by option
parsing and distribution handling without creating import cycles.
"""

_experimental = None


def setExperimental(experimental_indications):
    """Set the experimental feature indications.

    Args:
        experimental_indications: Iterable of experimental feature names.
    """
    global _experimental  # singleton, pylint: disable=global-statement
    _experimental = set(experimental_indications)


def isExperimental(indication):
    """Check whether a given experimental feature is enabled.

    Args:
        indication: (str) feature name

    Returns:
        bool
    """
    assert _experimental is not None, "Experimental indications have not been set yet."

    return indication in _experimental


def enableExperimental(indication):
    """Enable an experimental feature at runtime.

    Args:
        indication: (str) feature name
    """
    assert _experimental is not None, "Experimental indications have not been set yet."

    _experimental.add(indication)


def getExperimentalIndications():
    """*tuple*, items of ``--experimental=`` and runtime enabled indications."""
    assert _experimental is not None, "Experimental indications have not been set yet."

    return tuple(sorted(_experimental))


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
