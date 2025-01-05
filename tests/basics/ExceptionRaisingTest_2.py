#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

import sys

print("Raising an exception type in a function:")


def raiseExceptionClass():
    raise ValueError


try:
    raiseExceptionClass()
except Exception as e:
    print("Caught exception type", e, repr(e), type(e))
    print("Inside handler, sys.exc_info is this", sys.exc_info())

print("After catching, sys.exc_info is this", sys.exc_info())
print("*" * 20)

print("Raising an exception instance in a function:")


def raiseExceptionInstance():
    raise ValueError("hallo")


try:
    raiseExceptionInstance()
except Exception as f:
    print("Caught exception instance", f, repr(f), type(f))
    print("Inside handler, sys.exc_info is this", sys.exc_info())

print("After catching, sys.exc_info is this", sys.exc_info())
print("*" * 20)

print("Raising an exception, then catch it to re-raise it:")


def raiseExceptionAndReraise(arg):
    try:
        return arg / arg
    except:
        raise


try:
    raiseExceptionAndReraise(0)
except:
    print("Caught reraised", sys.exc_info())

print("After catching, sys.exc_info is this", sys.exc_info())
print("*" * 20)

print("Access an undefined global variable in a function:")


def raiseNonGlobalError():
    return undefined_value


try:
    raiseNonGlobalError()
except:
    print("NameError caught", sys.exc_info())

print("After catching, sys.exc_info is this", sys.exc_info())
print("*" * 20)

print("Raise a new style class as an exception, should be rejected:")


def raiseIllegalError():
    class X(object):
        pass

    raise X()


try:
    raiseIllegalError()
except TypeError as E:
    print("New style class exception correctly rejected:", E)
except:
    print(sys.exc_info())
    assert False, "Error, new style class exception was not rejected"

print("After catching, sys.exc_info is this", sys.exc_info())
print("*" * 20)

print("Raise an old-style class, version dependent outcome:")


class ClassicClassException:
    pass


def raiseCustomError():
    raise ClassicClassException()


try:
    try:
        raiseCustomError()
    except ClassicClassException:
        print("Caught classic class exception")
    except:
        print("Default catch", sys.exc_info())

        assert False, "Error, old style class exception was not caught"
except TypeError as e:
    print("Python3 hates to even try and catch classic classes", e)
else:
    print("Classic exception catching was considered fine.")

print("After catching, sys.exc_info is this", sys.exc_info())
print("*" * 20)

print("Check lazy exception creation:")


def checkExceptionConversion():
    try:
        raise Exception("some string")
    except Exception as err:
        print("Caught raised object", err, type(err))

    try:
        raise Exception, "some string"
    except Exception as err:
        print("Caught raised type, value pair", err, type(err))


checkExceptionConversion()
print("*" * 20)

print("Check exc_info scope:")


def checkExcInfoScope():
    try:
        raise ValueError
    except:
        assert sys.exc_info()[0] is not None
        assert sys.exc_info()[1] is not None
        assert sys.exc_info()[2] is not None

    if sys.version_info[0] < 3:
        print("Exc_info remains visible after exception handler for Python2")

        assert sys.exc_info()[0] is not None
        assert sys.exc_info()[1] is not None
        assert sys.exc_info()[2] is not None
    else:
        print("Exc_info is clear after exception handler for Python3")

        assert sys.exc_info()[0] is None
        assert sys.exc_info()[1] is None
        assert sys.exc_info()[2] is None

    def subFunction():
        print("Entering with exception info", sys.exc_info())

        assert sys.exc_info()[0] is not None
        assert sys.exc_info()[1] is not None
        assert sys.exc_info()[2] is not None

        try:
            print("Trying")
        except:
            pass

        print(
            "After trying something and didn't have an exception, info is",
            sys.exc_info(),
        )

    print("Call a function inside the exception handler and check there too.")

    try:
        raise KeyError
    except:
        assert sys.exc_info()[0] is not None
        assert sys.exc_info()[1] is not None
        assert sys.exc_info()[2] is not None

        subFunction()

    print("Call it twice and see.")

    try:
        raise "me"
    except:
        assert sys.exc_info()[0] is not None
        assert sys.exc_info()[1] is not None
        assert sys.exc_info()[2] is not None

        subFunction()
        subFunction()


if sys.version_info[0] < 3:
    sys.exc_clear()

checkExcInfoScope()

print("*" * 20)

# Check that the sys.exc_info is cleared again, after being set inside the
# function checkExcInfoScope, it should now be clear again.
assert sys.exc_info()[0] is None, sys.exc_info()[0]
assert sys.exc_info()[1] is None
assert sys.exc_info()[2] is None

print("Check catching subclasses")


def checkDerivedCatch():
    class A(BaseException):
        pass

    class B(A):
        def __init__(self):
            pass

    a = A()
    b = B()

    try:
        raise A, b
    except B, v:
        print("Caught B", v)
    except A, v:
        print("Didn't catch as B, but as A, Python3 does that", v)
    else:
        print("Not caught A class, not allowed to happen.")

    try:
        raise B, a
    except TypeError, e:
        print("TypeError with pair form for class not taking args:", e)


checkDerivedCatch()

print("*" * 20)


def checkNonCatch1():
    print("Testing if the else branch is executed in the optimizable case:")

    try:
        0
    except TypeError:
        print("Should not catch")
    else:
        print("Executed else branch correctly")


checkNonCatch1()
print("*" * 20)


def checkNonCatch2():
    try:
        print("Testing if the else branch is executed in the non-optimizable case:")
    except TypeError:
        print("Should not catch")
    else:
        print("Executed else branch correctly")


checkNonCatch2()
print("*" * 20)

print("Checking raise that with exception arguments that raise error themselves.")


def checkRaisingRaise():
    def geterror():
        return 1 / 0

    try:
        geterror()
    except Exception as e:
        print("Had exception", e)

    try:
        raise TypeError, geterror()

    except Exception as e:
        print("Had exception", e)

    try:
        raise TypeError, 7, geterror()

    except Exception as e:
        print("Had exception", e)


checkRaisingRaise()
print("*" * 20)

print("Checking a re-raise that isn't one:")


def checkMisRaise():
    raise


try:
    checkMisRaise()
except Exception as e:
    print("Without existing exception, re-raise gives:", e)

print("*" * 20)

print("Raising an exception in an exception handler gives:")


def nestedExceptions(a, b):
    try:
        a / b
    except ZeroDivisionError:
        a / b


try:
    nestedExceptions(1, 0)
except Exception as e:
    print("Nested exception gives", e)

print("*" * 20)

print("Checking unpacking from an exception as a sequence:")


def unpackingCatcher():
    try:
        raise ValueError(1, 2)
    except ValueError as (a, b):
        print("Unpacking caught exception and unpacked", a, b)


unpackingCatcher()
print("Afterwards, exception info is", sys.exc_info())

print("*" * 20)

print("Testing exception that escapes __del__ and therefore cannot be raised")


def divide(a, b):
    return a / b


def raiseExceptionInDel():
    class C:
        def __del__(self):
            c = divide(1, 0)
            print(c)

    def f():
        C()

    f()


raiseExceptionInDel()
print("*" * 20)

print("Testing exception changes between generator switches:")


def yieldExceptionInteraction():
    def yield_raise():
        print("Yield finds at generator entry", sys.exc_info()[0])
        try:
            raise KeyError("caught")
        except KeyError:
            yield sys.exc_info()[0]
            yield sys.exc_info()[0]
        yield sys.exc_info()[0]

    g = yield_raise()
    print("Initial yield from catch in generator", next(g))
    print("Checking from outside of generator", sys.exc_info()[0])
    print("Second yield from the catch reentered", next(g))
    print("Checking from outside of generator", sys.exc_info()[0])
    print("After leaving the catch generator yielded", next(g))


yieldExceptionInteraction()
print("*" * 20)

print(
    "Testing exception change between generator switches while handling an own exception"
)


def yieldExceptionInteraction2():
    def yield_raise():
        print("Yield finds at generator entry", sys.exc_info()[0])
        try:
            raise ValueError("caught")
        except ValueError:
            yield sys.exc_info()[0]
            yield sys.exc_info()[0]
        yield sys.exc_info()[0]

    try:
        undefined_global
    except Exception:
        print("Checking from outside of generator with", sys.exc_info()[0])
        g = yield_raise()
        v = next(g)
        print("Initial yield from catch in generator:", v)
        print("Checking from outside the generator:", sys.exc_info()[0])
        print("Second yield from the catch reentered:", next(g))
        print("Checking from outside the generation again:", sys.exc_info()[0])
        print("After leaving the catch generator yielded:", next(g))

    print("After exiting the trying branch:", sys.exc_info()[0])


yieldExceptionInteraction2()
print("After function exit, no exception", sys.exc_info())
print("*" * 20)

print("Check what happens if a function attempts to clear the exception in a handler")


def clearingException():
    def clearit():
        try:
            if sys.version_info[0] < 3:
                sys.exc_clear()
        except KeyError:
            pass

    try:
        raise KeyError
    except:
        print("Before clearing, it's", sys.exc_info())
        clearit()

        print("After clearing, it's", sys.exc_info())


clearingException()
print("*" * 20)

print("Check that multiple exceptions can be caught in a handler through a variable:")


def multiCatchViaTupleVariable():
    some_exceptions = (KeyError, ValueError)

    try:
        raise KeyError
    except some_exceptions:
        print("Yes, indeed.")


multiCatchViaTupleVariable()


def raiseValueWithValue():
    try:
        raise ValueError(1, 2, 3), (ValueError(1, 2, 3))
    except Exception as e:
        print("Gives", e)


print("Check exception given when value is raised with value", raiseValueWithValue())

# Make sure the "repr" of exceptions is fine

a = IOError
print("IOError is represented correctly:", repr(a))


def raising():
    raise ValueError


def not_raising():
    pass


def raiseWithFinallyNotCorruptingLineNumber():
    try:
        try:
            raising()
        finally:
            not_raising()
    except ValueError:
        print("Traceback is in tried block line", sys.exc_info()[2].tb_lineno)


raiseWithFinallyNotCorruptingLineNumber()


def wideCatchMustPublishException():
    print("At entry, no exception", sys.exc_info())

    try:
        undefined_global
    except:
        print("Inside handler:", sys.exc_info())

        pass

    print("Outside handler:", sys.exc_info())


print("Check that a unqualified catch properly preserves exception")
wideCatchMustPublishException()

print("Check if a nested exception handler does overwrite re-raised")


def checkReraiseAfterNestedTryExcept():
    def reraise():
        try:
            raise TypeError("outer")
        except Exception:
            try:
                raise KeyError("nested")
            except KeyError:
                print("Current exception inside nested handler", sys.exc_info())

                pass

            print("Current exception after nested handler exited", sys.exc_info())

            # Which one does this pick
            raise

    try:
        reraise()
    except Exception as e:
        print("Caught", repr(e))


checkReraiseAfterNestedTryExcept()


def checkReraiseByFunction():
    def reraise():
        raise

    try:
        try:
            raise TypeError("outer")
        except Exception:
            reraise()
    except Exception as e:
        import traceback

        print("Exception traceback of re-raise:")
        print("-" * 40)
        traceback.print_exc()
        print("-" * 40)
        print("OK.")


# TODO: Enable this, once the actual traceback of a function
# re-raise isn't wrong (contains itself) anymore.
if False:
    checkReraiseByFunction()


def checkNoRaiseExceptionDictBuilding(arg):
    a = {(): arg}

    b = {None: arg}

    c = {Ellipsis: arg}

    d = {1.0j: arg}

    e = {1.0: arg}

    f = {long(0): arg}

    g = {0: arg}

    h = {type: arg}

    return a, b, c, d, e, f, g, h


checkNoRaiseExceptionDictBuilding(1)


def checkRaiseExceptionDictBuildingRange(arg):
    try:
        i = {range(10): arg}
    except Exception as e:
        print("Raised", repr(e))
    else:
        print("No exception, OK for Python2")

        return i


print("Check if range as dict key raises:")
checkRaiseExceptionDictBuildingRange(2)


def checkRaiseExceptionDictBuildingTuple(arg):
    try:
        i = {(2, []): arg}
    except Exception as e:
        print("Raised", repr(e))
    else:
        return i


print("Check if mutable tuple as dict key raises:")
checkRaiseExceptionDictBuildingTuple(3)


def checkRaiseExceptionDictBuildingList(arg):
    try:
        i = {[2, ()]: arg}
    except Exception as e:
        print("Raised", repr(e))
    else:
        return i


print("Check if list as dict key raises:")
checkRaiseExceptionDictBuildingList(4)

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
