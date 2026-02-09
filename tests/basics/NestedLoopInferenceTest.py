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


# Top-level function (not a closure) with nested loops

def test_top_level_for_while(data=None):
    if data is None:
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
    print("top-level for+while iterate:", sorted(out))


run_test(test_top_level_for_while)


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
