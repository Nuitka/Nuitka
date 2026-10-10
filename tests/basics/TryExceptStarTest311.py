#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


def test_raise_and_catch_no_assign():
    try:
        raise ExceptionGroup("test", [ValueError("1")])
    except* ValueError:
        print("caught")


test_raise_and_catch_no_assign()


def test_raise_and_catch():
    try:
        raise ExceptionGroup("test", [ValueError("1")])
    except* ValueError as error:
        print(repr(error))
        print(error.exceptions)


test_raise_and_catch()


def test_raise_and_catch_non_exception_group():
    try:
        raise ValueError("Nobody expects the Spanish Inquisition")
    except* ValueError as error:
        print(repr(error))
        print(error.exceptions)


test_raise_and_catch_non_exception_group()


def test_raise_and_dont_catch():
    try:
        try:
            raise TypeError("123")
        except* ValueError:
            print("bad!")
    except Exception as outer:
        print(repr(outer))


test_raise_and_dont_catch()


def test_remaining_exceptions():
    try:
        try:
            raise ExceptionGroup("test", [ValueError("1"), TypeError("2")])
        except* ValueError as error:
            print(repr(error))
            print(error.exceptions)
    except Exception as outer:
        print(outer)


test_remaining_exceptions()


def test_multiple_handlers():
    try:
        raise ExceptionGroup("test", [ValueError("1"), TypeError("2")])
    except* ValueError as error:
        print(type(error))
        print(repr(error))
        print(error.exceptions)
    except* TypeError as error:
        print(type(error))
        print(repr(error))
        print(error.exceptions)


test_multiple_handlers()


def test_multiple_handlers_with_remaining():
    try:
        try:
            raise ExceptionGroup(
                "test", [ValueError("1"), TypeError("2"), RuntimeError("3")]
            )
        except* ValueError as error:
            print(type(error))
            print(repr(error))
            print(error.exceptions)
        except* TypeError as error:
            print(type(error))
            print(repr(error))
            print(error.exceptions)
    except Exception as outer:
        print(outer)


test_multiple_handlers_with_remaining()


def test_catch_multiple_types():
    try:
        raise ExceptionGroup("test", [ValueError("1"), TypeError("2")])
    except* (ValueError, TypeError) as error:
        print(repr(error))
        print(error.exceptions)


test_catch_multiple_types()


def test_catch_multiple_types_with_remaining():
    try:
        try:
            raise ExceptionGroup(
                "test", [ValueError("1"), TypeError("2"), RuntimeError("3")]
            )
        except* (ValueError, TypeError) as error:
            print(repr(error))
            print(error.exceptions)
    except Exception as outer:
        print(outer)


test_catch_multiple_types_with_remaining()

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
