#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function


def lambdaContainer(x):
    f = lambda c: c
    g = lambda c: c if x else c * c
    # h = lambda c: 'a' <= c <= 'z'

    y = f(x)
    z = g(4)

    print("Lambda with conditional expression gives", z)

    if "a" <= x <= y <= "z":
        print("Four")

    if "a" <= x <= "z":
        print("Yes")

    if "a" <= x > "z":
        print("Yes1")

    if "a" <= ("1" if x else "2") > "z":
        print("Yes2")

    if "a" <= ("1" if x else "2") > "z" > undefined_global:
        print("Yes3")

    z = lambda foo=y: foo

    print("Lambda defaulted gives", z())


lambdaContainer("b")


def lambdaGenerator():
    x = lambda: (yield 3)

    gen = x()
    print("Lambda generator gives", next(gen))


lambdaGenerator()


def lambdaDirectCall():
    args = range(7)

    x = (lambda *args: args)(*args)

    print("Lambda direct call gave", x)


lambdaDirectCall()


def lambdaDirectCallDefaults(xs, ys):
    log = []

    def trace(label, value):
        log.append(label)
        return value

    res = (lambda x, y=trace("default", 42): x + y)(trace("arg1", 1), trace("arg2", 2))
    print("Lambda direct call with default side effect:", res, log)

    log = []
    try:
        (lambda x, y=trace("default_err", 42): x + y)(trace("arg1_err", 1), 2, 3)
    except TypeError:
        print("Lambda direct call too many args:", log)

    log = []

    def gen(items):
        for item in items:
            log.append(item)
            yield item

    res = (lambda x, y=[a for a in gen(xs) if any(a == b for b in ys)]: x + len(y))(
        1, [10, 20]
    )
    print("Lambda direct call with comprehension default:", res, log)


lambdaDirectCallDefaults([1, 2, 3], [2, 3, 4])

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
