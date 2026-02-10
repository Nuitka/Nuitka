#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nested loop variable type inference, issue #3696.

When a variable is initialized to None and reassigned inside nested loops,
the optimizer must not conclude the variable is still None at a later
iteration point. These tests attempt to cover every loop combination (for+for,
for+while, while+for) and several container types (list, dict, set).
"""

from __future__ import print_function

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


# for+for: None -> list, iterate after nested loops

def test_for_for_list_iterate():
    data = [[1, 2, 3]]
    collected = None
    for group in data:
        for item in group:
            if collected is None:
                collected = []
            collected.append(item)
    out = []
    if collected is not None:
        for x in collected:
            out.append(x)
    print("for+for list iterate:", out)


run_test(test_for_for_list_iterate)


# for+while: None -> list, iterate after nested loops

def test_for_while_list_iterate():
    data = [[3, 2, 1]]
    collected = None
    for group in data:
        while group:
            item = group.pop()
            if collected is None:
                collected = []
            collected.append(item)
    out = []
    if collected is not None:
        for x in collected:
            out.append(x)
    print("for+while list iterate:", sorted(out))


run_test(test_for_while_list_iterate)


#  while+for: None -> list, iterate after nested loops

def test_while_for_list_iterate():
    data = [[1, 2, 3]]
    collected = None
    idx = 0
    while idx < len(data):
        for item in data[idx]:
            if collected is None:
                collected = []
            collected.append(item)
        idx += 1
    out = []
    if collected is not None:
        for x in collected:
            out.append(x)
    print("while+for list iterate:", out)


run_test(test_while_for_list_iterate)


# for+for: None -> dict, iterate keys after nested loops

def test_for_for_dict_iterate():
    data = [["a", "b"], ["c"]]
    mapping = None
    for group in data:
        for ch in group:
            if mapping is None:
                mapping = {}
            mapping[ch] = ord(ch)
    result = []
    if mapping is not None:
        for k in mapping:
            result.append(k)
    print("for+for dict iterate:", sorted(result))


run_test(test_for_for_dict_iterate)


# for+for: None -> set, iterate members after nested loops

def test_for_for_set_iterate():
    data = [[1, 2, 2], [3, 1]]
    seen = None
    for group in data:
        for item in group:
            if seen is None:
                seen = set()
            seen.add(item)
    result = []
    if seen is not None:
        for x in seen:
            result.append(x)
    print("for+for set iterate:", sorted(result))


run_test(test_for_for_set_iterate)


# Closure with nested loops and callback iteration

def test_closure_callback_iterate():
    output = []
    tasks = [[lambda: output.append("a"), lambda: output.append("b")]]

    def run():
        ready = None
        for batch in tasks:
            while batch:
                fn = batch.pop()
                if ready is None:
                    ready = []
                ready.append(fn)
        if ready is not None:
            for f in ready:
                f()

    run()
    print("closure callback iterate:", sorted(output))


run_test(test_closure_callback_iterate)


# Single loop (no nesting) with iteration — control case

def test_single_loop_iterate():
    data = [1, 2, 3]
    collected = None
    for item in data:
        if collected is None:
            collected = []
        collected.append(item)
    out = []
    if collected is not None:
        for x in collected:
            out.append(x)
    print("single loop iterate:", out)


run_test(test_single_loop_iterate)


# Chained inner loops (canary): inner loop 1 builds list, inner loop 2
# iterates it, within the same outer body.

def test_chain_inner_loops():
    groups = [[1, 2], [3, 4]]
    total = 0
    for group in groups:
        bucket = None
        for val in group:
            if bucket is None:
                bucket = []
            bucket.append(val * 10)
        for item in bucket:
            total += item
    print("chain inner loops:", total)


run_test(test_chain_inner_loops)


# Variable used between outer iterations (canary): shape must propagate
# to outer loop body after inner loop completes.

def test_use_between_outer_iters():
    groups = [[1, 2], [3, 4], [5]]
    result = None
    for group in groups:
        for val in group:
            if result is None:
                result = []
            result.append(val)
        result.append(0)
    print("between outer iters:", result)


run_test(test_use_between_outer_iters)


# Nonlocal scope (canary): variable mutated via nonlocal inside nested loop.

def test_nonlocal_var_in_nested_loop():
    result = None
    def inner():
        nonlocal result
        data = [[1, 2], [3]]
        for group in data:
            for val in group:
                if result is None:
                    result = []
                result.append(val)
    inner()
    print("nonlocal nested loop:", result, len(result))


run_test(test_nonlocal_var_in_nested_loop)

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
