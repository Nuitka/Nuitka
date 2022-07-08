#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Shared definitions of what comparison operation helpers are available.

These are functions to work with helper names, as well as sets of functions to
generate specialized code variants for.

Note: These are ordered, so we can define the order they are created in the
code generation of specialized helpers, as this set is used for input there
too.

"""

from nuitka.containers.OrderedSets import buildOrderedSet


def _makeDefaultOps():
    yield "RICH_COMPARE_xx_OBJECT_OBJECT_OBJECT"
    yield "RICH_COMPARE_xx_CBOOL_OBJECT_OBJECT"
    yield "RICH_COMPARE_xx_NBOOL_OBJECT_OBJECT"


def _makeTypeOps(type_name):
    for result_part in "OBJECT", "CBOOL", "NBOOL":
        yield "RICH_COMPARE_xx_%s_OBJECT_%s" % (result_part, type_name)
        yield "RICH_COMPARE_xx_%s_%s_OBJECT" % (result_part, type_name)
        yield "RICH_COMPARE_xx_%s_%s_%s" % (result_part, type_name, type_name)


def _makeFriendOps(*type_names):
    for type_name1 in type_names:
        for type_name2 in type_names:
            if type_name1 == type_name2:
                continue

            for result_part in "OBJECT", "CBOOL", "NBOOL":
                yield "RICH_COMPARE_xx_%s_%s_%s" % (result_part, type_name1, type_name2)
                yield "RICH_COMPARE_xx_%s_%s_%s" % (result_part, type_name2, type_name1)


specialized_cmp_helpers_set = buildOrderedSet(
    # Default implementation.
    _makeDefaultOps(),
    _makeTypeOps("STR"),
    _makeTypeOps("UNICODE"),
    _makeTypeOps("BYTES"),
    _makeTypeOps("INT"),
    _makeTypeOps("LONG"),
    _makeTypeOps("FLOAT"),
    _makeTypeOps("TUPLE"),
    _makeTypeOps("LIST"),
    _makeFriendOps("INT", "CLONG"),
    _makeFriendOps("INT", "LONG"),
    _makeFriendOps("LONG", "DIGIT"),
    _makeFriendOps("INT", "LONG"),
    # TODO: Add "CLONG_CLONG" type ops once we use that for local variables too.
)

_non_specialized_cmp_helpers_set = set()


def getSpecializedComparisonOperations():
    return specialized_cmp_helpers_set


def getNonSpecializedComparisonOperations():
    return _non_specialized_cmp_helpers_set
