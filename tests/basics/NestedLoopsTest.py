#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nested loop variable type inference and post-loop operations."""

from __future__ import print_function

# nuitka-project: --python-flag=no_warnings


# for+for: None -> list, iterate after nested loops


def functionForForListIterate():
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


# for+while: None -> list, iterate after nested loops


def functionForWhileListIterate():
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


#  while+for: None -> list, iterate after nested loops


def functionWhileForListIterate():
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


# for+for: None -> dict, iterate keys after nested loops


def functionForForDictIterate():
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


# for+for: None -> set, iterate members after nested loops


def functionForForSetIterate():
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


# Closure with nested loops and callback iteration


def functionClosureCallbackIterate():
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


# Single loop (no nesting) with iteration — control case


def functionSingleLoopIterate():
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


# Chained inner loops (canary): inner loop 1 builds list, inner loop 2
# iterates it, within the same outer body.


def functionChainInnerLoops():
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


# Variable used between outer iterations (canary): shape must propagate
# to outer loop body after inner loop completes.


def functionUseBetweenOuterIters():
    groups = [[1, 2], [3, 4], [5]]
    result = None
    for group in groups:
        for val in group:
            if result is None:
                result = []
            result.append(val)
        result.append(0)
    print("between outer iters:", result)


# Nonlocal scope (canary): variable mutated via nonlocal inside nested loop.


def functionNonlocalVarInNestedLoop():
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


# ---------------------------------------------------------------------------
# 1. Attribute / method calls (canary — currently passes)
# ---------------------------------------------------------------------------


def functionMethodAppend():
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


def functionListIndexing():
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


def functionListConcatenation():
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


def functionListMultiply():
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


def functionListIadd():
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


def functionIntArithmetic():
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


def functionFloatArithmetic():
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


def functionStrConcatenation():
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


def functionStrMultiply():
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


def functionTruthinessIf():
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


def functionInList():
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


def functionUnpackList():
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


def functionStarUnpack():
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


def functionUnpackInLoop():
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


def functionLenList():
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


def functionEqComparison():
    """== comparison on variable from nested loop."""
    data = [[1, 2], [3]]
    result = None
    for group in data:
        for val in group:
            if result is None:
                result = []
            result.append(val)
    print("eq:", result == [1, 2, 3], result == [])


def functionListOrdering():
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


def functionIterNext():
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


def functionListCompOnLoopVar():
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


def functionSetCompOnLoopVar():
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
functionForForListIterate()
functionForWhileListIterate()
functionWhileForListIterate()
functionForForDictIterate()
functionForForSetIterate()
functionClosureCallbackIterate()
functionSingleLoopIterate()
functionChainInnerLoops()
functionUseBetweenOuterIters()
functionNonlocalVarInNestedLoop()
functionMethodAppend()
functionListIndexing()
functionListConcatenation()
functionListMultiply()
functionListIadd()
functionIntArithmetic()
functionFloatArithmetic()
functionStrConcatenation()
functionStrMultiply()
functionTruthinessIf()
functionInList()
functionUnpackList()
functionStarUnpack()
functionUnpackInLoop()
functionLenList()
functionEqComparison()
functionListOrdering()
functionIterNext()
functionListCompOnLoopVar()
functionSetCompOnLoopVar()

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
