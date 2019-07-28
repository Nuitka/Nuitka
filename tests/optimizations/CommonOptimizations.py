#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
class CommonOptimizationTest:
    _list_tests = {
            "Test on empty list" : [],
            "Test on all None" : [None, None, None],
            "Test on single True and rest None": [None, True, None],
            "Test on zero list 20000 times": [0]*20000,
            "Test on zero list 255 times": [0]*255
        }

    _range_tests = {
            "Test on range with single argument" : range(260),
            "Test on range with two arguments" : range(1, 270),
            "Test on range with three arguments" : range(2, 1024, 5),
        }

    def yield_helper():
        print("Yielding 40")
        yield 40
        print("Yielding 60")
        yield 60
        print("Yielding 30")
        yield 30

    _yeild_tests = {
        "Yield Test": x > 42 for x in yield_helper()
        }

    _exception_tests = [
        1.0,
        float
    ]

    _set_tests = {
        "Test on set" : set([0, 1, 2, 3, 3]),
    }

    _dict_tests = {
        "Test on dict" : {1:"One", 2:"Two"},
    }

    _other_tests = {
        "Test for string" : "String",
        "Test for unicode" : u"Unicode",
        "Test for byte" : b"byte",
    }

    def __init__(self, builtin):
        self.builtin = builtin

    def print_tests(self, test):
        for desc, value in self._list_tests.items():
            print("{}: {}".format(desc, self.builtin(value)))

    def print_exception_tests(self, exception_tests, exception_message=None):
        print("Disallowed without args:")
        try:
            print(self.builtin())
        except Exception as e:
            print("caught ", repr(e))

        test_name = iter([
            " with float not iterable:",
            " with float type not iterable:"
            ])

        for value in exception_tests:
            print(str(self.builtin) + next(test_name))
            try:
                print(self.builtin(value))
            except Exception as e:
                if exception_message:
                    print(exception_message)
                else:
                    print(repr(e))

    def run_all_tests(self):
        tests = [
            self._list_tests,
            self._range_tests,
            self._set_tests,
            self._dict_tests,
            self._yeild_tests,
            self._exception_tests,
            self._other_tests
        ]

        for test in tests:
            if test == self._exception_tests:
                self.print_exception_tests(test)
            else:
                self.print_tests(test)

print("Test for any")
any_test = CommonOptimizationTest(any)
any_test.run_all_tests()

print("Test for all")
all_test = CommonOptimizationTest(all)
all_test.run_all_tests()