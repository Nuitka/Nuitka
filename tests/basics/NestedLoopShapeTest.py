#!/usr/bin/env python
#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file
"""
Test cases for nested loop variable type inference.

These tests verify that Nuitka's optimizer correctly handles variables
that may have different types depending on control flow, particularly
in nested loop scenarios where a variable starts as None and may be
assigned a different type inside the loop.

Issue: https://github.com/Nuitka/Nuitka/issues/3696
"""

from __future__ import print_function

import sys


def test_iteration_nested_for():
    """Test iteration over variable assigned in nested for loop."""
    value = None
    for outer in [[1, 2, 3]]:
        for inner in outer:
            value = [inner]
    for item in value:
        pass
    print("test_iteration_nested_for: PASSED")


def test_iteration_nested_while():
    """Test iteration over variable assigned in nested while loop."""
    value = None
    items = [[1, 2, 3]]
    i = 0
    while i < len(items):
        j = 0
        inner = items[i]
        while j < len(inner):
            value = [inner[j]]
            j += 1
        i += 1
    for item in value:
        pass
    print("test_iteration_nested_while: PASSED")


def test_iteration_for_while():
    """Test iteration over variable assigned in for-while nested loop."""
    value = None
    for outer in [[1, 2, 3]]:
        i = 0
        while i < len(outer):
            value = [outer[i]]
            i += 1
    for item in value:
        pass
    print("test_iteration_for_while: PASSED")


def test_len_nested_loop():
    """Test len() on variable assigned in nested loop."""
    value = None
    for outer in [[1, 2, 3]]:
        for inner in outer:
            value = [inner, inner + 1]
    result = len(value)
    assert result == 2, f"Expected 2, got {result}"
    print("test_len_nested_loop: PASSED")


def test_abs_nested_loop():
    """Test abs() on variable assigned in nested loop."""
    value = None
    for outer in [[-5, -10]]:
        for inner in outer:
            value = inner
    result = abs(value)
    assert result == 10, f"Expected 10, got {result}"
    print("test_abs_nested_loop: PASSED")


def test_int_nested_loop():
    """Test int() on variable assigned in nested loop."""
    value = None
    for outer in [["42", "100"]]:
        for inner in outer:
            value = inner
    result = int(value)
    assert result == 100, f"Expected 100, got {result}"
    print("test_int_nested_loop: PASSED")


def test_float_nested_loop():
    """Test float() on variable assigned in nested loop."""
    value = None
    for outer in [["3.14", "2.71"]]:
        for inner in outer:
            value = inner
    result = float(value)
    assert abs(result - 2.71) < 0.01, f"Expected 2.71, got {result}"
    print("test_float_nested_loop: PASSED")


def test_all_nested_loop():
    """Test all() on variable assigned in nested loop."""
    value = None
    for outer in [[[True, True, True]]]:
        for inner in outer:
            value = inner
    result = all(value)
    assert result is True, f"Expected True, got {result}"
    print("test_all_nested_loop: PASSED")


def test_any_nested_loop():
    """Test any() on variable assigned in nested loop."""
    value = None
    for outer in [[[False, False, True]]]:
        for inner in outer:
            value = inner
    result = any(value)
    assert result is True, f"Expected True, got {result}"
    print("test_any_nested_loop: PASSED")


def test_in_operator_nested_loop():
    """Test 'in' operator on variable assigned in nested loop."""
    value = None
    for outer in [[[1, 2, 3]]]:
        for inner in outer:
            value = inner
    result = 2 in value
    assert result is True, f"Expected True, got {result}"
    print("test_in_operator_nested_loop: PASSED")


def test_conditional_assignment():
    """Test variable conditionally assigned based on loop iteration."""
    value = None
    for i in range(3):
        if i == 2:
            value = [1, 2, 3]
    result = len(value)
    assert result == 3, f"Expected 3, got {result}"
    print("test_conditional_assignment: PASSED")


def test_deep_nesting():
    """Test deeply nested loops (3 levels)."""
    value = None
    for a in [[[1, 2]]]:
        for b in a:
            for c in b:
                value = [c]
    for item in value:
        pass
    print("test_deep_nesting: PASSED")


def test_multiple_operations():
    """Test multiple operations on same variable."""
    value = None
    for outer in [[1, 2, 3]]:
        for inner in outer:
            value = [inner]

    # All these should work without TypeError
    len_result = len(value)
    iter_result = list(value)
    in_result = value[0] in value
    all_result = all([True for _ in value])

    assert len_result == 1
    assert iter_result == [3]
    assert in_result is True
    assert all_result is True
    print("test_multiple_operations: PASSED")


def test_while_condition_variable():
    """Test variable that controls while loop condition."""
    value = None
    data = [[1, 2], [3, 4]]
    for group in data:
        for item in group:
            value = [item * 2]
    # Use in iteration after loop
    total = sum(value)
    assert total == 8, f"Expected 8, got {total}"
    print("test_while_condition_variable: PASSED")


def test_mixed_types_per_iteration():
    """Test variable that could be different types per iteration."""
    value = None
    for i, item in enumerate([["a", "b"], [1, 2]]):
        for x in item:
            value = [x]
    # Last value should be [2]
    result = len(value)
    assert result == 1
    print("test_mixed_types_per_iteration: PASSED")


def test_break_in_inner_loop():
    """Test variable assigned before break in inner loop."""
    value = None
    for outer in [[1, 2, 3]]:
        for inner in outer:
            value = [inner]
            if inner == 2:
                break
    for item in value:
        pass
    print("test_break_in_inner_loop: PASSED")


def test_continue_in_inner_loop():
    """Test variable assigned with continue in inner loop."""
    value = None
    for outer in [[1, 2, 3]]:
        for inner in outer:
            if inner == 2:
                continue
            value = [inner]
    for item in value:
        pass
    print("test_continue_in_inner_loop: PASSED")


def test_exception_in_loop():
    """Test variable assigned in try block within loop."""
    value = None
    for outer in [[1, 2, 3]]:
        for inner in outer:
            try:
                value = [inner]
            except Exception:
                pass
    for item in value:
        pass
    print("test_exception_in_loop: PASSED")


def test_string_operations():
    """Test string operations on loop-assigned variable."""
    value = None
    for outer in [["hello", "world"]]:
        for inner in outer:
            value = inner
    result = len(value)
    assert result == 5, f"Expected 5, got {result}"
    print("test_string_operations: PASSED")


def test_bytes_nested_loop():
    """Test bytes() on variable assigned in nested loop."""
    value = None
    for outer in [[[72, 105]]]:  # "Hi" in ASCII
        for inner in outer:
            value = inner
    result = bytes(value)
    assert result == b"Hi", f"Expected b'Hi', got {result}"
    print("test_bytes_nested_loop: PASSED")


def test_complex_nested_loop():
    """Test complex() on variable assigned in nested loop."""
    value = None
    for outer in [["3+4j", "1+2j"]]:
        for inner in outer:
            value = inner
    result = complex(value)
    assert result == (1+2j), f"Expected (1+2j), got {result}"
    print("test_complex_nested_loop: PASSED")


def test_contains_nested_loop():
    """Test 'in' containment on variable assigned in nested loop."""
    value = None
    for outer in [[{1, 2, 3}, {4, 5, 6}]]:
        for inner in outer:
            value = inner
    result = 5 in value
    assert result is True, f"Expected True, got {result}"
    print("test_contains_nested_loop: PASSED")


if __name__ == "__main__":
    print("Running nested loop shape tests...")
    print("-" * 50)

    test_iteration_nested_for()
    test_iteration_nested_while()
    test_iteration_for_while()
    test_len_nested_loop()
    test_abs_nested_loop()
    test_int_nested_loop()
    test_float_nested_loop()
    test_all_nested_loop()
    test_any_nested_loop()
    test_in_operator_nested_loop()
    test_conditional_assignment()
    test_deep_nesting()
    test_multiple_operations()
    test_while_condition_variable()
    test_mixed_types_per_iteration()
    test_break_in_inner_loop()
    test_continue_in_inner_loop()
    test_exception_in_loop()
    test_string_operations()
    test_bytes_nested_loop()
    test_complex_nested_loop()
    test_contains_nested_loop()

    print("-" * 50)
    print("All tests passed!")
    sys.exit(0)


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
