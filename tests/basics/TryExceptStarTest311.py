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
