#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Policies of Nuitka.

These are decisions during compilation, which are the future point of adding
user control. They are kept here to avoid circular imports of "Options" and
"ModuleRegistry" modules.
"""

# TODO: Move the frame locals optimization policy and the annotations policy
# into this module as well.

from nuitka.ModuleRegistry import hasDoneModule
from nuitka.options.Options import (
    hasNonDeploymentIndicator,
    isExperimental,
    isStandaloneMode,
    shallMakeModule,
)
from nuitka.States import states

_default_pgo_assertion_policy = None


def decidePGOClassDictAssertionPolicy(static_qualname):
    """Decide how to check PGO data for a class dictionary.

    Args:
        static_qualname: Statically known qualified name of the class, for
            future per class configuration decisions.

    Notes:
        This is the future point for user control of this decision.

    Returns:
        One of 'ignore', 'exception' or 'assertion'.
    """
    # TODO: Add Nuitka package configuration for deciding this per class name.
    # pylint: disable=unused-argument

    # Cached, since options do not change during a compilation.
    global _default_pgo_assertion_policy  # pylint: disable=global-statement

    if _default_pgo_assertion_policy is None:
        if states.is_debug:
            # Debug mode must reveal mismatches that user code might swallow.
            _default_pgo_assertion_policy = "assertion"
        elif hasNonDeploymentIndicator("pgo-assertions"):
            _default_pgo_assertion_policy = "exception"
        else:
            _default_pgo_assertion_policy = "ignore"

    return _default_pgo_assertion_policy


def decideImportLoweringToFixed(module_name):
    """Decide if imports can be lowered to fixed imports.

    Args:
        module_name: Name of the imported module.

    Notes:
        This is the future point for user control of this decision.

    Returns:
        bool
    """
    # TODO: Add Nuitka package configuration for deciding this per module name.
    # pylint: disable=unused-argument

    if isExperimental("standalone-imports"):
        # Module mode is user provided code, but for the fixed conversion, it is
        # treated the same as standalone mode.
        if isStandaloneMode() or shallMakeModule():
            return True

    return False


def decideImportDropNotFound(module_name):
    """Decide if not found imports can be dropped from the imports.

    Args:
        module_name: Name of the imported module.

    Notes:
        This is the future point for user control of this decision.

    Returns:
        bool
    """
    if isStandaloneMode() and isExperimental("standalone-imports"):
        return True

    if shallMakeModule():
        # TODO: Add Nuitka package configuration to decide if the module name is
        # in a user namespace that is to be included. If a parent package is
        # part of the compiled modules, the not found imports cannot be dropped,
        # as the runtime may still provide modules for it.
        return not any(
            hasDoneModule(parent_package_name)
            for parent_package_name in module_name.getParentPackageNames()
        )

    return False


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
