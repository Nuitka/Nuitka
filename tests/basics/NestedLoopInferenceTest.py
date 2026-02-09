#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nested loop variable type inference, issue #3696.

When a variable is initialized to None and reassigned inside nested loops,
the optimizer must not conclude the variable is still None at a later
iteration point. These tests attempt to cover every loop combination (for+for,
for+while, while+for) and several container types (list, dict, set).
"""

from __future__ import print_function


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


try:
    test_for_for_list_iterate()
except Exception as e:
    print("FAILED test_for_for_list_iterate:", type(e).__name__, e)


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


try:
    test_for_while_list_iterate()
except Exception as e:
    print("FAILED test_for_while_list_iterate:", type(e).__name__, e)


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


try:
    test_while_for_list_iterate()
except Exception as e:
    print("FAILED test_while_for_list_iterate:", type(e).__name__, e)


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


try:
    test_for_for_dict_iterate()
except Exception as e:
    print("FAILED test_for_for_dict_iterate:", type(e).__name__, e)


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


try:
    test_for_for_set_iterate()
except Exception as e:
    print("FAILED test_for_for_set_iterate:", type(e).__name__, e)


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


try:
    test_top_level_for_while()
except Exception as e:
    print("FAILED test_top_level_for_while:", type(e).__name__, e)


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


try:
    test_closure_callback_iterate()
except Exception as e:
    print("FAILED test_closure_callback_iterate:", type(e).__name__, e)


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


try:
    test_single_loop_iterate()
except Exception as e:
    print("FAILED test_single_loop_iterate:", type(e).__name__, e)


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
