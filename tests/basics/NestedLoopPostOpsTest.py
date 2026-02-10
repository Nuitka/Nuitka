#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tests for optimizer miscompilation due to nested loop type shape loss.

When the optimizer loses track of a variable's type shape across nested
loops (seeing tshape_unknown or the pre-loop type instead of the actual
converged type), it can misoptimize many different operations — not just
iter(). This file exercises each category of operation that relies on
correct type shape information.

Regression tests for https://github.com/Nuitka/Nuitka/issues/3696
"""

from __future__ import print_function

# nuitka-project: --python-flag=no_warnings

_passed = 0
_failed = 0


def run_test(func):
    global _passed, _failed
    try:
        func()
        _passed += 1
    except Exception as e:
        _failed += 1
        print("FAILED %s: %s %s" % (func.__name__, type(e).__name__, e))


# ---------------------------------------------------------------------------
# 1. Attribute / method calls (canary — currently passes)
# ---------------------------------------------------------------------------

def test_method_append():
    """list.append() on variable built in nested loop."""
    data = [[1, 2], [3]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    result.append(99)
    print("method_append:", result)


# ---------------------------------------------------------------------------
# 2. Subscript / indexing (canary — currently passes)
# ---------------------------------------------------------------------------

def test_list_indexing():
    """Indexing a list built in nested loop."""
    data = [[10, 20], [30]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    print("indexing:", result[0], result[-1])


# ---------------------------------------------------------------------------
# 3. Binary / augmented operations
#    Wrong type -> wrong operator specialization or TypeError.
# ---------------------------------------------------------------------------

def test_list_concatenation():
    """List + list where left operand is from nested loop."""
    data = [[1, 2], [3]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    combined = result + [4, 5]
    print("list_concat:", combined)


def test_list_multiply():
    """List * int where list is from nested loop."""
    data = [[1], [2]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    doubled = result * 2
    print("list_mult:", doubled)


def test_list_iadd():
    """List += on variable from nested loop."""
    data = [[1, 2], [3]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    result += [4]
    print("list_iadd:", result)


def test_int_arithmetic():
    """Arithmetic on int accumulated in nested loop."""
    data = [[1, 2], [3, 4]]
    total = None
    for group in data:
        for val in group:
            if total is None:
                total = 0
            total = total + val
    result = total * 2 + 1
    print("int_arith:", result)


def test_float_arithmetic():
    """Float arithmetic on value from nested loop."""
    data = [[1.5, 2.5], [3.0]]
    total = None
    for group in data:
        for val in group:
            if total is None:
                total = 0.0
            total = total + val
    result = total / 2.0
    print("float_arith:", result)


def test_str_concatenation():
    """String + string where left operand is from nested loop."""
    data = [["ab", "cd"], ["ef"]]
    text = None
    for group in data:
        for w in group:
            if text is None:
                text = ""
            text = text + w
    full = text + "!"
    print("str_concat:", full)


def test_str_multiply():
    """String * int where string is from nested loop."""
    data = [["a"], ["b"]]
    text = None
    for group in data:
        for w in group:
            if text is None:
                text = ""
            text = text + w
    print("str_mult:", text * 3)


# ---------------------------------------------------------------------------
# 4. Boolean context / truthiness (canary — currently passes)
# ---------------------------------------------------------------------------

def test_truthiness_if():
    """if <var>: where var is built in nested loop."""
    data = [[1, 2], [3]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    if result:
        print("truthiness_if: non-empty", len(result))
    else:
        print("truthiness_if: empty")


# ---------------------------------------------------------------------------
# 5. Membership testing (canary — currently passes)
# ---------------------------------------------------------------------------

def test_in_list():
    """'val in list' where list is from nested loop."""
    data = [[1, 2], [3, 4]]
    items = None
    for group in data:
        for val in group:
            if items is None:
                items = []
            items.append(val)
    print("in_list:", 3 in items, 99 in items)


# ---------------------------------------------------------------------------
# 6. Unpacking
#    Optimizer must know the variable is iterable to allow unpacking.
# ---------------------------------------------------------------------------

def test_unpack_list():
    """Unpack a 2-element list built in nested loop."""
    data = [[1], [2]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    a, b = result
    print("unpack_list:", a, b)


def test_star_unpack():
    """Star unpacking from list built in nested loop."""
    data = [[1, 2], [3, 4]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    first, *rest = result
    print("star_unpack:", first, rest)


def test_unpack_in_loop():
    """Unpack variable from nested loop inside a for loop."""
    data = [[(1, "a")], [(2, "b")]]
    pairs = None
    for group in data:
        for val in group:
            if pairs is None:
                pairs = []
            pairs.append(val)
    nums = []
    for n, c in pairs:
        nums.append(n)
    print("unpack_in_loop:", nums)


# ---------------------------------------------------------------------------
# 7. len() and builtins (canary — currently passes)
# ---------------------------------------------------------------------------

def test_len_list():
    """len() on list from nested loop."""
    data = [[1, 2], [3, 4, 5]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    print("len_list:", len(result))


# ---------------------------------------------------------------------------
# 8. Comparison specialization
# ---------------------------------------------------------------------------

def test_eq_comparison():
    """== comparison on variable from nested loop."""
    data = [[1, 2], [3]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    print("eq:", result == [1, 2, 3], result == [])


def test_list_ordering():
    """< > comparisons on lists from nested loop."""
    data1 = [[1, 2], [3]]
    data2 = [[4, 5], [6]]
    r1 = None
    r2 = None
    for group in data1:
        for val in group:
            if r1 is None:
                r1 = []
            r1.append(val)
    for group in data2:
        for val in group:
            if r2 is None:
                r2 = []
            r2.append(val)
    print("ordering:", r1 < r2, r1 > r2)


# ---------------------------------------------------------------------------
# 9. Iteration protocol (canary — currently passes)
# ---------------------------------------------------------------------------

def test_iter_next():
    """iter() + next() on variable from nested loop."""
    data = [[10, 20], [30]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    it = iter(result)
    print("iter_next:", next(it), next(it))


# ---------------------------------------------------------------------------
# 10. Comprehension iteration
# ---------------------------------------------------------------------------

def test_list_comp_on_loop_var():
    """List comprehension over variable from nested loop."""
    data = [[1, 2], [3]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    doubled = [x * 2 for x in result]
    print("list_comp:", doubled)


def test_set_comp_on_loop_var():
    """Set comprehension over variable from nested loop."""
    data = [[1, 2, 2], [3, 1]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    uniq = {x for x in result}
    print("set_comp:", sorted(uniq))


# Execute all tests.
run_test(test_method_append)
run_test(test_list_indexing)
run_test(test_list_concatenation)
run_test(test_list_multiply)
run_test(test_list_iadd)
run_test(test_int_arithmetic)
run_test(test_float_arithmetic)
run_test(test_str_concatenation)
run_test(test_str_multiply)
run_test(test_truthiness_if)
run_test(test_in_list)
run_test(test_unpack_list)
run_test(test_star_unpack)
run_test(test_unpack_in_loop)
run_test(test_len_list)
run_test(test_eq_comparison)
run_test(test_list_ordering)
run_test(test_iter_next)
run_test(test_list_comp_on_loop_var)
run_test(test_set_comp_on_loop_var)

print("Summary: %d passed, %d failed, %d total" % (_passed, _failed, _passed + _failed))

#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
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
