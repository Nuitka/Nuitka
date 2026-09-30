#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Walrus targets in generator expressions bind in the scope around them."""


def case1_function_local():
    """The target is a local of the function, readable after the expression."""

    result = tuple(x for v in [1, 2, 3] if (x := v * 10) > 10)

    return result, x


def case2_nested_generator_expressions():
    """Nested generator expressions pass the target on to the function."""

    result = [tuple(y for w in [v, v + 1] if (y := w)) for v in [1, 3]]

    return result, y


def case3_declared_global():
    """A global declaration in the function makes it a module variable."""

    global case3_value  # pylint: disable=global-variable-undefined

    tuple(case3_value for v in [5, 6] if (case3_value := v))

    return case3_value


def case4_lambda():
    """A lambda is a function scope too."""

    function = lambda values: (tuple(z for v in values if (z := v)), z)

    return function([7, 8])


class Case5:
    def method(self):
        """A method's target stays out of the class and the module."""

        result = list(m for v in "ab" if (m := v.upper()))

        return result, m


def case6_read_while_suspended():
    """The function sees each value as the generator assigns it."""

    generator = (c for v in [1, 2] if (c := v))

    first = next(generator)
    seen = c
    rest = list(generator)

    return first, seen, rest, c


def case7_calls_do_not_share():
    """Every call has a target of its own, a generator of another call running."""

    def values(items):
        return (w for v in items if (w := v))

    first = values("ab")
    second = values("xy")

    return next(first), next(second), next(first), next(second)


case8_result = tuple(case8_value for v in [1, 2] if (case8_value := v))

print("case1", case1_function_local())
print("case2", case2_nested_generator_expressions())
print("case3", case3_declared_global())
print("case4", case4_lambda())
print("case5", Case5().method())
print("case6", case6_read_while_suspended())
print("case7", case7_calls_do_not_share())
print("case8", case8_result, case8_value)

# Only the module level target and the declared global are module variables.
for name in ("x", "y", "z", "m", "c", "w", "case3_value", "case8_value"):
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
