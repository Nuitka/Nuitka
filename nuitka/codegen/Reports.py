#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

from logging import error, info

from nuitka.containers.odict import OrderedDict
from nuitka.containers.oset import OrderedSet

_missing_helpers = OrderedDict()

_missing_operations = OrderedSet()

# _error_for_missing = True
_error_for_missing = False


def doMissingOptimizationReport():
    level = error if _error_for_missing else info

    for helper, source_refs in _missing_helpers.items():
        level("Missing C helper code variant, used fallback: %s", helper)
        for source_ref in source_refs:

            level("Occurred at %s." % source_ref.getAsString())

    for desc in _missing_operations:
        level("Missing optimization, used fallback: %s", desc)


def onMissingHelper(helper_name, source_ref):
    if source_ref:
        if helper_name not in _missing_helpers:
            _missing_helpers[helper_name] = []

        _missing_helpers[helper_name].append(source_ref)


def onMissingOperation(*args):
    _missing_operations.add(args)
