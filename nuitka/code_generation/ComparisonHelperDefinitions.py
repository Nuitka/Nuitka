#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Shared definitions of what comparison operation helpers are available.

These are functions to work with helper names, as well as sets of functions to
generate specialized code variants for.

Note: These are ordered, so we can define the order they are created in the
code generation of specialized helpers, as this set is used for input there
too.

"""

from nuitka.containers.OrderedSets import buildOrderedSet

# Mapping of rich comparison Python level name, to C level name of helpers.
rich_comparison_codes = {
    "Lt": "LT",
    "LtE": "LE",
    "Eq": "EQ",
    "NotEq": "NE",
    "Gt": "GT",
    "GtE": "GE",
}

# Subset of comparisons which will be used for identical types.
rich_comparison_subset_codes = {
    "Lt": "LT",
    "LtE": "LE",
    "Eq": "EQ",
}


def _makeDefaultOps():
    for comparator in rich_comparison_codes.values():
        yield "RICH_COMPARE_%s_OBJECT_OBJECT_OBJECT" % comparator
        yield "RICH_COMPARE_%s_NBOOL_OBJECT_OBJECT" % comparator


def _makeTypeOps(type_name, may_raise_same_type, shortcut=False):
    for result_part in "OBJECT", "CBOOL", "NBOOL":
        for comparator in rich_comparison_codes.values():
            if result_part == "CBOOL":
                continue

            # TODO: We want those as well, but we don't need them immediately.
            if type_name in ("NILONG",):
                continue

            yield "RICH_COMPARE_%s_%s_OBJECT_%s" % (comparator, result_part, type_name)
            yield "RICH_COMPARE_%s_%s_%s_OBJECT" % (comparator, result_part, type_name)

        if may_raise_same_type and result_part == "CBOOL":
            continue
        if not may_raise_same_type and result_part == "NBOOL":
            continue

        for comparator in (
            rich_comparison_codes.values()
            if not shortcut
            else rich_comparison_subset_codes.values()
        ):
            yield "RICH_COMPARE_%s_%s_%s_%s" % (
                comparator,
                result_part,
                type_name,
                type_name,
            )


def _makeFriendOps(type_name1, type_name2, may_raise, shortcut):
    assert type_name1 != type_name2

    for result_part in "OBJECT", "CBOOL", "NBOOL":
        if not may_raise:
            if result_part == "NBOOL":
                continue

        for comparator in (
            rich_comparison_codes.values()
            if not shortcut
            else rich_comparison_subset_codes.values()
        ):
            yield "RICH_COMPARE_%s_%s_%s_%s" % (
                comparator,
                result_part,
                type_name1,
                type_name2,
            )


specialized_cmp_helpers_set = buildOrderedSet(
    # Default implementation.
    _makeDefaultOps(),
    # Pure types:
    _makeTypeOps("STR", may_raise_same_type=False, shortcut=True),
    _makeTypeOps("UNICODE", may_raise_same_type=False, shortcut=True),
    _makeTypeOps("BYTES", may_raise_same_type=False, shortcut=True),
    _makeTypeOps("INT", may_raise_same_type=False, shortcut=True),
    _makeTypeOps("LONG", may_raise_same_type=False, shortcut=True),
    _makeTypeOps("FLOAT", may_raise_same_type=False, shortcut=True),
    # Dual types
    _makeTypeOps("NILONG", may_raise_same_type=False, shortcut=True),
    # TODO: What would shortcut mean, how do tuples compare their elements then?
    _makeTypeOps("TUPLE", may_raise_same_type=True, shortcut=False),
    _makeTypeOps("LIST", may_raise_same_type=True, shortcut=False),
    # Mixed Python types:
    # TODO: Absolutely possible to shortcut, why aren't we doing it?
    _makeFriendOps("LONG", "INT", may_raise=False, shortcut=False),
    # Partial Python with C types
    # TODO: Absolutely possible to shortcut, why aren't we doing it?
    _makeFriendOps("INT", "CLONG", may_raise=False, shortcut=False),
    _makeFriendOps("LONG", "DIGIT", may_raise=False, shortcut=False),
    _makeFriendOps("FLOAT", "CFLOAT", may_raise=False, shortcut=False),
    # Partial dual types with C types, cannot shortcut as reverse argument versions are used.
    _makeFriendOps("NILONG", "CLONG", may_raise=False, shortcut=False),
    _makeFriendOps("NILONG", "DIGIT", may_raise=False, shortcut=False),
    # TODO: Add "CLONG_CLONG" type ops once we use that for local variables too.
)

_non_specialized_cmp_helpers_set = set()


def getSpecializedComparisonOperations():
    return specialized_cmp_helpers_set


def getNonSpecializedComparisonOperations():
    return _non_specialized_cmp_helpers_set


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
