#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Walrus operation corner cases."""


def case1_pop3_unknown_key(key, **kwargs):
    """Walrus with 'kwargs.pop(key, None)' where key hash-ability is unknown."""

    if (value := kwargs.pop(key, None)) is not None:
        return value

    return None


def case2_pop3_union_key(flag, **kwargs):
    """Walrus pop with runtime key being hashable string or unhashable list."""

    key = [] if flag else "x"

    if (value := kwargs.pop(key, None)) is not None:
        return value

    return None


def case3_pop3_nested_walrus(key, **kwargs):
    """Nested walrus pop calls to stress short-circuit ordering and side effects."""

    if (left := kwargs.pop(key, None)) is not None and (
        right := kwargs.pop("y", None)
    ) is not None:
        return left, right

    return None


def case4_setdefault3_unknown_key(key, **kwargs):
    """Walrus with 'kwargs.setdefault(key, 123)' for unknown key hash-ability."""

    if (value := kwargs.setdefault(key, 123)) is not None:
        return value

    return None


def case5_pop3_in_try(key, **kwargs):
    """Walrus pop inside explicit try/except to exercise try node exception tracking."""

    try:
        if (value := kwargs.pop(key, None)) is not None:
            return value
    except TypeError:
        return "caught"

    return None


def case6_shadows_outer_function():
    """Without a declaration, a variable of an outer function is not written."""

    f = "outer"

    def inner():
        result = tuple(f for v in [1, 2] if (f := v))

        return result, f

    return inner(), f


async def asyncSource():
    yield 1
    yield 2


async def case7_asynchronous_generator_expression():
    """An asynchronous generator expression is a generator expression too."""

    generator = (o async for v in asyncSource() if (o := v + 100))
    results = [item async for item in generator]

    return results, o


def runCoroutine(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as stop:
        return stop.value


def case8_slice_with_walrus():
    """A slice start read before a walrus assignment must stay alive."""

    data = bytes(range(256)) * 2
    cur = 1
    upper_values = iter(range(300, 317))
    lengths = []

    for _i in range(17):
        value = data[cur : (cur := cur + 2, next(upper_values))[1]]
        lengths.append(len(value))
        cur += 14

    return lengths, cur


def case9_operation_with_walrus():
    """A left operand read before a walrus assignment must stay alive."""

    value = "".join(["a"] * 1000)
    other = value + (value := "b")

    return len(other), other[:2], value


def case10_call_argument_with_walrus():
    """Call arguments read before a walrus assignment must stay alive."""

    value = "".join(["a"] * 1000)

    def collect(*args):
        return len(args[0]), args[0][:2], args[1]

    result = collect(value, (value := "b"))

    return result, value


def case11_dict_key_with_walrus():
    """A dictionary key read before a walrus assignment must stay alive."""

    value = "".join(["a"] * 1000)
    mapping = {value: (value := "b")}

    return len(list(mapping)[0]), list(mapping.values())[0], value


print("case1-hit", case1_pop3_unknown_key("x", x=1))
print("case1-miss", case1_pop3_unknown_key("x"))

print("case2-false", case2_pop3_union_key(False, x=1))

try:
    print("case2-true", case2_pop3_union_key(True, x=1))
except TypeError:
    print("case2-true", "TypeError")

print("case3-both", case3_pop3_nested_walrus("x", x=1, y=2))
print("case3-missing", case3_pop3_nested_walrus("x", x=1))

print("case4", case4_setdefault3_unknown_key("x"))

print("case5-hit", case5_pop3_in_try("x", x=1))
print("case5-miss", case5_pop3_in_try("x"))
print("case5-caught", case5_pop3_in_try([], x=1))

print("case6", case6_shadows_outer_function())
print("case7", runCoroutine(case7_asynchronous_generator_expression()))
print("case8", case8_slice_with_walrus())
print("case9", case9_operation_with_walrus())
print("case10", case10_call_argument_with_walrus())
print("case11", case11_dict_key_with_walrus())


# TODO: This is not a walrus operation, it should be a separate test case, but
# currently this avoids the overhead of another test run.
def returnInFinallyWithContinue():
    """Return in tried block with continue in final block."""

    for i in range(2):
        try:
            return "abandoned"
        finally:
            print("continue in final block", i)

            if i == 0:
                continue
            break

    return "done"


print("return-in-finally-with-continue", returnInFinallyWithContinue())

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
