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


def case12_nested_walrus_in_and_or(flag):
    """A walrus in the right value overwrites the left value of a boolean operation."""

    value = ("x" * 1000) if flag else ""
    result = ((value or "a") and (value := "b")) + (value := "c")

    return len(result), result[:1], value


def case13_nested_walrus_in_conditional(flag):
    """A walrus in one conditional branch overwrites the value of the other."""

    value = "x" * 1000
    result = value if flag else (value := "y")
    result = result + (value := "z")

    return len(result), result[:1], value


def case14_nested_walrus_in_or(flag):
    """A walrus in a boolean operation overwrites an earlier read of the variable."""

    value = ("x" * 1000) if flag else ""
    result = value + (value or (value := "y"))

    return len(result), result[:1], len(value), value[:1]


def case15_nested_walrus_in_branch(flag):
    """A walrus in a conditional branch overwrites an earlier read of the variable."""

    value = "x" * 1000
    result = value + (value if flag else (value := "y"))

    return len(result), result[:1], len(value), value[:1]


def case16_nested_walrus_in_augmented_assignment():
    """A walrus in the right value overwrites the target of an augmented assignment."""

    string_value = "x" * 1000
    string_value += (string_value := "y")

    list_value = [1] * 1000
    list_value += (list_value := [2])

    return (
        len(string_value),
        string_value[:1],
        len(list_value),
        list_value[:2],
    )


def case17_nested_walrus_in_augmented_nonlocal():
    """A walrus in the right value overwrites the nonlocal target."""

    value = "x" * 1000

    def inner():
        nonlocal value
        value += (value := "y")

    inner()

    return len(value), value[:1]


def case18_nested_walrus_in_augmented_global():
    """A walrus in the right value overwrites the global target."""

    global module_augmented_value

    module_augmented_value = "x" * 1000
    module_augmented_value += (module_augmented_value := "y")

    return len(module_augmented_value), module_augmented_value[:1]


def case19_nested_walrus_in_augmented_attribute():
    """A walrus in the right value rebinds the object of an attribute target."""

    class Container:
        pass

    container = Container()
    container.value = "x" * 1000
    old = container
    container.value += (container := Container()).__class__.__name__

    return len(old.value), container is not old


def case20_nested_walrus_in_augmented_subscript():
    """A walrus in the right value overwrites the subscript target."""

    mapping = {0: "x" * 1000}
    key = 0
    mapping[key] += (key := "y")

    return len(mapping[0]), key


def case21_nested_walrus_in_augmented_generator():
    """A walrus in a generator expression overwrites the augmented target."""

    value = [1]
    old = value
    value += ((value := item) for item in range(3))

    return len(old), old, value


module_augmented_value = None

module_augmented_string = "x" * 1000
module_augmented_string += (module_augmented_string := "y")

module_augmented_list = [1] * 1000
module_augmented_list += (module_augmented_list := [2])

module_augmented_generator = [1]
module_augmented_generator_old = module_augmented_generator
module_augmented_generator += (
    (module_augmented_generator := item) for item in range(3)
)


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
print("case12-true", case12_nested_walrus_in_and_or(True))
print("case12-false", case12_nested_walrus_in_and_or(False))
print("case13-true", case13_nested_walrus_in_conditional(True))
print("case13-false", case13_nested_walrus_in_conditional(False))
print("case14-true", case14_nested_walrus_in_or(True))
print("case14-false", case14_nested_walrus_in_or(False))
print("case15-true", case15_nested_walrus_in_branch(True))
print("case15-false", case15_nested_walrus_in_branch(False))
print("case16", case16_nested_walrus_in_augmented_assignment())
print("case17", case17_nested_walrus_in_augmented_nonlocal())
print("case18", case18_nested_walrus_in_augmented_global())
print("case19", case19_nested_walrus_in_augmented_attribute())
print("case20", case20_nested_walrus_in_augmented_subscript())
print("case21", case21_nested_walrus_in_augmented_generator())
print(
    "module-augmented-string",
    len(module_augmented_string),
    module_augmented_string[:1],
)
print(
    "module-augmented-list",
    len(module_augmented_list),
    module_augmented_list[:2],
)
print(
    "module-augmented-generator",
    len(module_augmented_generator_old),
    module_augmented_generator_old,
    module_augmented_generator,
)


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
