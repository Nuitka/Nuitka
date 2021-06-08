#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Reports about code generation.

Initially this is about missing optimization only, but it should expand into
real stuff.
"""

from nuitka.containers.odict import OrderedDict
from nuitka.containers.oset import OrderedSet
from nuitka.Tracing import codegen_logger, optimization_logger

_missing_helpers = OrderedDict()

_missing_operations = OrderedSet()

_missing_trust = OrderedDict()

_error_for_missing = False
# _error_for_missing = True


def doMissingOptimizationReport():
    for helper, source_refs in _missing_helpers.items():
        message = "Missing C helper code variant, used fallback: %s at %s" % (
            ",".join(source_ref.getAsString() for source_ref in source_refs),
            helper,
        )

        if _error_for_missing:
            codegen_logger.warning(message)
        else:
            codegen_logger.info(message)

    for desc in _missing_operations:
        message = "Missing optimization, used fallback: %s" % (desc,)
        if _error_for_missing:
            optimization_logger.warning(message)
        else:
            optimization_logger.info(message)

    for desc, source_refs in _missing_trust.items():
        message = desc[0] % desc[1:]
        message += " at %s" % ",".join(
            source_ref.getAsString() for source_ref in source_refs
        )

        if _error_for_missing:
            optimization_logger.warning(message)
        else:
            optimization_logger.info(message)


def onMissingHelper(helper_name, source_ref):
    if source_ref:
        if helper_name not in _missing_helpers:
            _missing_helpers[helper_name] = []

        _missing_helpers[helper_name].append(source_ref)


def onMissingOperation(operation, left, right):
    # Avoid the circular dependency on tshape_uninit from StandardShapes.
    if right.__class__.__name__ != "ShapeTypeUninit":
        _missing_operations.add((operation, left, right))


def onMissingTrust(operation, source_ref, *args):
    key = (operation,) + args

    if key not in _missing_trust:
        _missing_trust[key] = OrderedSet()

    _missing_trust[key].add(source_ref)
