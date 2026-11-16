#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tests for exception state with "yield from" delegation."""

import sys


def current_exception():
    return sys.exc_info()[1]


# Thrown exception through yield from, using the delegating handler state.
def inner_plain():
    yield "inner"
    yield "inner-end"


def outer_handled():
    try:
        raise KeyError("outer handled")
    except KeyError:
        yield from inner_plain()


g = outer_handled()
next(g)
try:
    g.throw(ValueError("through"))
except ValueError as e:
    print("Yield from throw context: %r" % (e.__context__,))


# Nested generators see the exception state of the delegating generator.
def inner_state():
    print("Inner sees: %r" % (current_exception(),))
    yield
    print("Inner resumed sees: %r" % (current_exception(),))


def outer_state():
    try:
        raise KeyError("outer")
    except KeyError:
        print("Outer sees: %r" % (current_exception(),))
        yield from inner_state()
        print("Outer after inner sees: %r" % (current_exception(),))


g = outer_state()
next(g)
try:
    next(g)
except StopIteration:
    pass
print("Module after: %r" % (current_exception(),))


# A yield from after leaving an except block must not leak its state.
def inner_after_handler():
    yield 1


def outer_after_handler():
    try:
        raise KeyError("handled")
    except KeyError:
        pass
    yield from inner_after_handler()
    print("Outer after yield from: %r" % (current_exception(),))


g = outer_after_handler()
print("First: %r" % (next(g),))
try:
    next(g)
except StopIteration:
    pass
print("Caller after yield from: %r" % (current_exception(),))


# GeneratorExit thrown through yield from must not chain the close error.
def gen_finally():
    try:
        yield "first"
    finally:
        yield "second"


def gen_yield_from_finally():
    yield from gen_finally()


g = gen_yield_from_finally()
next(g)
try:
    g.throw(GeneratorExit())
except RuntimeError as e:
    print("Yield from close context: %r" % (e.__context__,))

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
