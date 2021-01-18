#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
""" Common tests for built-ins.

Attempting to cover generic run time behavior. Static optimization of these is
not expected.
"""


def yield_helper():
    print("Yielding 40")
    yield 40
    print("Yielding 60")
    yield 60
    print("Yielding 30")
    yield 30


class CommonOptimizationTest:
    _list_tests = {
        "Test on empty list": [],
        "Test on all None": [None, None, None],
        "Test on single True and rest None": [None, True, None],
        "Test on zero list 20000 times": [0] * 20000,
        "Test on zero list 255 times": [0] * 255,
    }

    _range_tests = {
        "Test on range with single argument": range(260),
        "Test on range with two arguments": range(1, 270),
        "Test on range with three arguments": range(2, 1024, 5),
    }

    _yeild_tests = {"Yield Test": yield_helper()}

    _non_iterable_tests = {
        "Float value": 1.0,
        "Type value": float,
        "Int value": 1,
        "Complex value": 1j,
    }

    _set_tests = {"Test on set": set([0, 1, 2, 3, 3])}

    _dict_tests = {"Test on dict": {1: "One", 2: "Two"}}

    _other_tests = {
        "Test for string": "String",
        "Test for unicode": u"Unicode",
        "Test for byte": b"byte",
    }

    def __init__(self, builtin):
        self.builtin = builtin

    def print_tests(self, test):
        for desc, value in sorted(test.items()):
            try:
                print("{}: {}".format(desc, self.builtin(value)))
            except Exception as e:  # pylint: disable=broad-except
                print("caught ", repr(e))

    def run_all_tests(self):
        print("Calling without args:")
        try:
            print(self.builtin())
        except Exception as e:  # pylint: disable=broad-except
            print("caught ", repr(e))

        tests = [
            self._list_tests,
            self._range_tests,
            self._set_tests,
            self._dict_tests,
            self._yeild_tests,
            self._non_iterable_tests,
            self._other_tests,
        ]

        for test in tests:
            self.print_tests(test)


# TODO: Right now this tests NOTHING of Nuitka, only the Python built-in
print("Test for any")
any_test = CommonOptimizationTest(any)
any_test.run_all_tests()

print("Test for all")
all_test = CommonOptimizationTest(all)
all_test.run_all_tests()
