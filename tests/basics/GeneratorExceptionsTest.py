#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tests for generator exception state.

These check that the handled exception is kept in the generator object and
restored when resuming, rather than using the exception that the caller
happens to handle at resume time.

This file avoids syntax newer than Python 2.6, so it can report behavior for
older Python versions too, where it may differ from current Python.
"""

from __future__ import print_function

import sys


def current_exception():
    return sys.exc_info()[1]


def exception_context(exception):
    # Python 2 has no exception chaining.
    return getattr(exception, "__context__", None)


# Thrown exception context while suspended inside an except block.
def gen_context():
    try:
        raise KeyError("a")
    except Exception:
        yield


g = gen_context()
next(g)
try:
    g.throw(ValueError("thrown"))
except ValueError as e:
    print("Generator throw context: %r" % (exception_context(e),))


# Thrown exception into a generator without own handler does not use the
# caller's handled exception as context.
def gen_throw_plain():
    yield
    yield


def caller_throw_plain():
    g = gen_throw_plain()
    next(g)
    try:
        raise KeyError("caller")
    except KeyError:
        try:
            g.throw(ValueError("thrown plain"))
        except ValueError as e:
            print("Generator throw plain context: %r" % (exception_context(e),))
        print("Caller after throw plain: %r" % (current_exception(),))


caller_throw_plain()


# Leaving an except block on a later resume must not restore caller state.
def gen_leak():
    yield
    try:
        raise KeyError("in generator")
    except KeyError:
        yield
    yield


def caller_leak():
    g = gen_leak()
    next(g)
    try:
        raise ValueError("in caller")
    except ValueError:
        next(g)
    next(g)
    print("Generator after handler: %r" % (current_exception(),))


caller_leak()


# Inside a generator without own handler the caller exception is visible on
# the first resume, but not after the caller left its handler.
def gen_sys_exc():
    print("Generator sees caller: %r" % (current_exception(),))
    yield
    print("Generator sees after caller: %r" % (current_exception(),))


def caller_sys_exc():
    g = gen_sys_exc()
    try:
        raise ValueError("caller")
    except ValueError:
        next(g)
    try:
        next(g)
    except StopIteration:
        pass
    print("Caller after generator: %r" % (current_exception(),))


caller_sys_exc()


# Nested handlers inside a generator.
def gen_nested():
    try:
        raise KeyError("outer")
    except KeyError:
        try:
            raise ValueError("inner")
        except ValueError:
            print("Generator nested inner: %r" % (current_exception(),))
            yield
        print("Generator nested outer: %r" % (current_exception(),))
        yield
    print("Generator nested after: %r" % (current_exception(),))


g = gen_nested()
next(g)
next(g)
try:
    next(g)
except StopIteration:
    pass
print("Caller after nested: %r" % (current_exception(),))


# Raised exception gets the context of the handler it is raised in.
def raise_in_handler():
    try:
        raise KeyError("handled")
    except KeyError:
        try:
            raise ValueError("raised")
        except ValueError as e:
            print("Raised in handler: %r" % (exception_context(e),))


raise_in_handler()


# Generator raised exception with no own handler, resumed from a handler.
def gen_raises_plain():
    yield
    raise ValueError("plain")


def caller_raises_plain():
    g = gen_raises_plain()
    next(g)
    try:
        raise KeyError("caller")
    except KeyError:
        try:
            next(g)
        except ValueError as e:
            print("Generator raised plain: %r" % (exception_context(e),))


caller_raises_plain()


# Bare raise inside generator with no own handler.
def gen_bare_raise():
    yield
    try:
        raise
    except BaseException as e:
        print("Generator bare raise: %r" % (e,))


def caller_bare_raise():
    g = gen_bare_raise()
    next(g)
    try:
        raise KeyError("caller bare")
    except KeyError:
        try:
            next(g)
        except StopIteration:
            pass


caller_bare_raise()

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
