#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Walrus targets in generator expressions bind in the scope around them."""


def case1_function_local():
    """The target is a local of the function, readable after the expression."""

    result = tuple(x for v in [1, 2, 3] if (x := v * 10) > 10)

    return result, x


def case2_generator_expression_in_list_contraction():
    """A list contraction around it is no scope of its own."""

    result = [tuple(y for w in [v, v + 1] if (y := w)) for v in [1, 3]]

    return result, y


def case3_nested_generator_expressions():
    """Generator expressions around it are passed through, however many."""

    two = tuple(tuple(a for w in [v, v + 1] if (a := w)) for v in [1, 3])
    three = tuple(tuple(tuple(b for u in [w] if (b := u)) for w in [v]) for v in [1, 2])

    return two, a, three, b


def case4_list_contraction_in_generator_expression():
    """A list contraction inside one binds in the function as well."""

    result = tuple([d for w in [v] if (d := w * 7)] for v in [1, 2])

    return result, d


def case5_parameter(p):
    """The target may be a parameter of the function."""

    result = tuple(p for v in [1, 2] if (p := v + 100))

    return result, p


def case6_used_before_and_after():
    """The target may be a variable the function uses itself."""

    e = 0
    result = tuple(e for v in [1, 2] if (e := e + v))

    return result, e


def case7_shadows_outer_function():
    """Without a declaration, a variable of an outer function is not written."""

    f = "outer"

    def inner():
        result = tuple(f for v in [1, 2] if (f := v))

        return result, f

    return inner(), f


def case8_declared_nonlocal():
    """A non-local declaration in the function makes it the outer variable."""

    g = "outer"

    def inner():
        nonlocal g

        return tuple(g for v in [1, 2] if (g := v))

    return inner(), g


def case9_declared_global():
    """A global declaration in the function makes it a module variable."""

    global case9_value  # pylint: disable=global-variable-undefined

    tuple(case9_value for v in [5, 6] if (case9_value := v))

    return case9_value


def case10_lambda():
    """A lambda is a function scope too."""

    function = lambda values: (tuple(h for v in values if (h := v)), h)

    return function([7, 8])


class Case11:
    def method(self):
        """A method's target stays out of the class and the module."""

        result = list(i for v in "ab" if (i := v.upper()))

        return result, i

    # A class body itself may not contain the construct, a lambda in it may.
    function = lambda self: (tuple(j for v in [1, 2] if (j := v)), j)


def case12_generator_function():
    """A generator function is a function scope too."""

    result = tuple(k for v in [1, 2] if (k := v * 2))

    yield result
    yield k


async def case13_coroutine():
    """So is a coroutine."""

    result = tuple(l for v in [1, 2] if (l := v * 3))

    return result, l


def case14_read_while_suspended():
    """The function sees each value as the generator assigns it."""

    generator = (m for v in [1, 2] if (m := v))

    first = next(generator)
    seen = m
    rest = list(generator)

    return first, seen, rest, m


def case15_calls_do_not_share():
    """Every call has a target of its own, a generator of another call running."""

    def values(items):
        return (n for v in items if (n := v))

    first = values("ab")
    second = values("xy")

    return next(first), next(second), next(first), next(second)


def runCoroutine(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as stop:
        return stop.value


case16_result = tuple(case16_value for v in [1, 2] if (case16_value := v))
case17_result = tuple(
    tuple(case17_value for w in [v] if (case17_value := w)) for v in [1, 2]
)

print("case1", case1_function_local())
print("case2", case2_generator_expression_in_list_contraction())
print("case3", case3_nested_generator_expressions())
print("case4", case4_list_contraction_in_generator_expression())
print("case5", case5_parameter(0))
print("case6", case6_used_before_and_after())
print("case7", case7_shadows_outer_function())
print("case8", case8_declared_nonlocal())
print("case9", case9_declared_global())
print("case10", case10_lambda())
print("case11", Case11().method(), Case11().function())
print("case12", list(case12_generator_function()))
print("case13", runCoroutine(case13_coroutine()))
print("case14", case14_read_while_suspended())
print("case15", case15_calls_do_not_share())
print("case16", case16_result, case16_value)
print("case17", case17_result, case17_value)

# Only the module level targets and the declared global are module variables.
for name in (
    "a",
    "b",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "p",
    "x",
    "y",
    "case9_value",
    "case16_value",
    "case17_value",
):
    print("global", name, name in globals())

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
