#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
import sys, os

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            ".."
        )
    )
)
from nuitka.tools.testing.Common import (
    executeReferenceChecked,
    checkDebugPython
)

checkDebugPython()


x = 17

# Just a function return a constant. Functions don't become any smaller. Let's
# get that right.
def simpleFunction1():
    return 1

# Do a bit of math with a local variable, assigning to its value and then doing
# an overwrite of that, trying that math again. This should cover local access
# a bit.
def simpleFunction2():
    y = 3 * x  # @UnusedVariable
    y = 3

    return x*2*y

# A local function is being returned. This covers creation of local functions
# and their release. No closure variables involved yet.
def simpleFunction3():
    def contained():
        return x

    return contained

# Again, local function being return, but this time with local variable taken
# as a closure. We use value from defaulted argument, so it cannot be replaced.
def simpleFunction4(a = 1):
    y = a

    def contained():
        return y

    return contained

# Default argument and building a list as local variables. Also return them,
# so they are not optimized away.
def simpleFunction5(a = 2):
    c = 1
    f = [a, a + c]

    return c, f

def simpleFunction6():
    for _b in range(6):
        pass

    for _c in (1, 2, 3, 4, 5, 6):
        pass


def simpleFunction7(b = 1):
    for _b in range(6):
        pass

def simpleFunction8():
    c = []
    c.append(x)

def simpleFunction9(a = 1*2):
    if a == a:
        pass

u = None

def simpleFunction10(a = 1*2):
    x = [u for u in range(8)]

def simpleFunction11():
    f = 1

    while f < 8:
        f += 1

v = None

def simpleFunction12():
    a = [(u,v) for (u,v) in zip(range(8),range(8))]

    return a

def cond():
    return 1

def simpleFunction13(a = 1*2):
    pass

def simpleFunction14p(x):
    try:
        simpleFunction14p(1,1)
    except TypeError as _e:
        pass

    try:
        simpleFunction14p(1,1)
    except TypeError:
        pass

def simpleFunction14():
    simpleFunction14p(3)

def simpleFunction15p(x):
    try:
        try:
            x += 1
        finally:
            try:
                x *= 1
            finally:
                _z = 1
    except:
        pass

def simpleFunction15():
    simpleFunction15p([1])

def simpleFunction16():
    class EmptyClass:
        pass

    return EmptyClass

def simpleFunction17():
    class EmptyObjectClass:
        pass

    return EmptyObjectClass()

def simpleFunction18():
    closured = 1

    class NonEmptyClass:
        def __init__(self, a, b):
            self.a = a
            self.b = b

        inside = closured

    return NonEmptyClass(133, 135)

def simpleFunction19():
    lam = lambda l : l+1

    return lam(9), lam


def simpleFunction20():
    try:
        a = []
        a[1]
    except IndexError as _e:
        pass


def simpleFunction21():
    class EmptyBaseClass:
        def base(self):
            return 3

    class EmptyObjectClass(EmptyBaseClass):
        pass

    result = EmptyObjectClass()

    c = result.base()

    return result, c

def simpleFunction22():
    return True is False and False is not None

def simpleFunction23():
    not 2

def simpleFunction24p(x):
    pass

def simpleFunction24():
    simpleFunction24p(x = 3)


def simpleFunction25():
    class X:
        f = 1

    def inplace_adder(b):
        X.f += b

    return inplace_adder(6**8)


def simpleFunction26():
    class X:
        f = [5]

    def inplace_adder(b):
        X.f += b

    return inplace_adder([1, 2])

def simpleFunction27():
    a = { 'g': 8 }

    def inplace_adder(b):
        a[ 'g' ] += b

    return inplace_adder(3)

def simpleFunction28():
    a = { 'g': [8], 'h': 2 }

    def inplace_adder(b):
        a[ 'g' ] += b

    return inplace_adder([3, 5])


def simpleFunction29():
    return '3' in '7'

def simpleFunction30():
    def generatorFunction():
        yield 1
        yield 2
        yield 3

def simpleFunction31():
    def generatorFunction():
        yield 1
        yield 2
        yield 3

    a = []

    for y in generatorFunction():
        a.append(y)

    for z in generatorFunction():
        a.append(z)


def simpleFunction32():
    def generatorFunction():
        yield 1

    gen = generatorFunction()
    next(gen)

def simpleFunction33():
    def generatorFunction():
        a = 1

        yield a

    a = []

    for y in generatorFunction():
        a.append(y)


def simpleFunction34():
    try:
        raise ValueError
    except:
        pass

def simpleFunction35():
    try:
        raise ValueError(1,2,3)
    except:
        pass


def simpleFunction36():
    try:
        raise (TypeError, (3,x,x,x))
    except TypeError:
        pass

def simpleFunction37():
    l = [1, 2, 3]

    try:
        _a, _b = l
    except ValueError:
        pass


def simpleFunction38():
    class Base:
        pass

    class Parent(Base):
        pass

def simpleFunction39():
    class Parent(object):
        pass


def simpleFunction40():
    def myGenerator():
        yield 1

    myGenerator()

def simpleFunction41():
    a = b = 2

    return a, b


def simpleFunction42():
    a = b = 2 * x

    return a, b

def simpleFunction43():
    class D:
        pass

    a = D()

    a.b = 1

def simpleFunction47():
    def reraisy():
        def raisingFunction():
            raise ValueError(3)

        def reraiser():
            raise

        try:
            raisingFunction()
        except:
            reraiser()

    try:
        reraisy()
    except:
        pass

def simpleFunction48():
    class BlockExceptions:
        def __enter__(self):
            pass
        def __exit__(self, exc, val, tb):
            return True

    with BlockExceptions():
        raise ValueError()

template = "lala %s lala"

def simpleFunction49():
    c = 3
    d = 4

    a = x, y = b, e = (c,d)

    return a, y, b, e

b = range(10)

def simpleFunction50():
    def getF():
        def f():
            for i in b:
                yield i

        return f

    f = getF()

    for x in range(2):
        _r = list(f())

def simpleFunction51():
    g = ( x for x in range(9) )

    try:
        g.throw(ValueError, 9)
    except ValueError as _e:
        pass

def simpleFunction52():
    g = ( x for x in range(9) )

    try:
        g.throw(ValueError(9))
    except ValueError as _e:
        pass

def simpleFunction53():
    g = ( x for x in range(9) )

    try:
        g.send(9)
    except TypeError as _e:
        pass

def simpleFunction54():
    g = ( x for x in range(9) )
    next(g)

    try:
        g.send(9)
    except TypeError as _e:
        pass


def simpleFunction55():
    g = ( x for x in range(9) )

    try:
        g.close()
    except ValueError as _e:
        pass

def simpleFunction56():
    def f():
        f()

    try:
        f()
    except RuntimeError:
        pass

def simpleFunction57():
    x = 1
    y = 2

    def f(a = x, b = y):
        return a, b

    f()
    f(2)
    f(3,4)

def simpleFunction58():
    a = 3
    b = 5

    try:
        a = a * 2

        return a
    finally:
        a / b


def simpleFunction59():
    a = 3
    b = 5

    try:
        a = a * 2

        return a
    finally:
        return a / b


class X:
    def __del__(self):
        # Super used to reference leak.
        x = super()

        raise ValueError(1)

def simpleFunction63():
    def superUser():
        X()

    try:
        superUser()
    except Exception:
        pass

def simpleFunction64():
    x = 2
    y = 3  # @UnusedVariable
    z = eval("x * y")

    return z

def simpleFunction65():
    import array

    a = array.array('b', b"")
    assert a == eval(repr(a), {"array": array.array})

    d = {
        'x' : 2,
        'y' : 3
    }

    z = eval(repr(d), d)

    return z


def simpleFunction66():
    import types
    return type(simpleFunction65) == types.FunctionType

def simpleFunction67():
    length = 100000
    pattern = "1234567890\00\01\02\03\04\05\06"

    q, r = divmod(length, len(pattern))
    teststring = pattern * q + pattern[:r]

    return teststring

def simpleFunction68():
    from random import randrange
    x = randrange(18)

def simpleFunction69():
    pools = [tuple() ]
    g = ((len(pool) == 0,) for pool in pools)
    next(g)

def simpleFunction70():
    def gen():
        try:
            undefined_yyy  # @UndefinedVariable
        except Exception:
            pass

        yield sys.exc_info()

    try:
        undefined_xxx  # @UndefinedVariable
    except Exception:
        return list(gen())

def simpleFunction71():
    try:
        undefined_global  # @UndefinedVariable
    except Exception:
        try:
            try:
                raise
            finally:
                undefined_global  # @UndefinedVariable
        except Exception:
            pass

def simpleFunction72():
    try:
        for _i in range(10):
            try:
                undefined_global  # @UndefinedVariable
            finally:
                break
    except Exception:
        pass

def simpleFunction73():
    for _i in range(10):
        try:
            undefined_global  # @UndefinedVariable
        finally:
            return 7


def simpleFunction74():
    import os  # @Reimport

    return os

def simpleFunction75():
    def raising_gen():
        try:
            raise TypeError
        except TypeError:
            yield

    g = raising_gen()
    next(g)

    try:
        g.throw(RuntimeError())
    except RuntimeError:
        pass

def simpleFunction76():
    class MyException(Exception):
        def __init__(self, obj):
            self.obj = obj
    class MyObj:
        pass

    def inner_raising_func():
        raise MyException(MyObj())

    try:
        inner_raising_func()
    except MyException:
        try:
            try:
                raise
            finally:
                raise
        except MyException:
            pass

def simpleFunction77():
    class weirdstr(str):
        def __getitem__(self, index):
            return weirdstr(str.__getitem__(self, index))

    (weirdstr("1234"))
    # filter(lambda x: x>="33", weirdstr("1234"))


def simpleFunction78():
    a = "x = 2"
    exec(a)

def simpleFunction79():
    "some doc"

    simpleFunction79.__doc__ = simpleFunction79.__doc__.replace("doc", "dok")
    simpleFunction79.__doc__ += " and more" + simpleFunction79.__name__


def simpleFunction80():
    "some doc"

    del simpleFunction80.__doc__

def simpleFunction81():
    def f():
        yield 1
        j

    j = 1
    x = list(f())

def simpleFunction82():
    def f():
        yield 1
        j

    j = 1
    x = f.__doc__

def simpleFunction83():
    x = list(range(7))
    x[2] = 5

    j = 3
    x += [h*2 for h in range(j)]

def simpleFunction84():
    x = tuple(range(7))

    j = 3
    x += tuple([h*2 for h in range(j)])

def simpleFunction85():
    x = list(range(7))
    x[2] = 3
    x *= 2

def simpleFunction86():
    x = "something"
    x += ""

def simpleFunction87():
    x = 7
    x += 2000

def simpleFunction88():
    class C:
        def __iadd__(self, other):
            return self

    x = C()
    x += C()

def simpleFunction89():
    x = [1,2]
    x += [3,4]

def anyArgs(*args, **kw):
    pass

def simpleFunction90():
    some_tuple = (
        simpleFunction89,
        simpleFunction89,
        simpleFunction89,
    )

    anyArgs(*some_tuple)

def simpleFunction91():
    some_dict = {
        'a' : simpleFunction90,
    }

    anyArgs(**some_dict)

def simpleFunction92():
    some_tuple = (
        simpleFunction89,
    )

    some_dict = {
        'a' : simpleFunction90,
    }

    anyArgs(*some_tuple, **some_dict)

def simpleFunction93():
    some_tuple = (
        simpleFunction89,
    )

    some_dict = {
        'a' : simpleFunction90,
    }

    anyArgs(some_tuple, *some_tuple, **some_dict)

def simpleFunction94():
    some_tuple = (
        simpleFunction89,
    )

    some_dict = {
        'a' : simpleFunction90,
    }

    anyArgs(*some_tuple, b = some_dict, **some_dict)

def simpleFunction95():
    some_tuple = (
        simpleFunction89,
    )

    some_dict = {
        'a' : simpleFunction90,
    }

    anyArgs(some_tuple, *some_tuple, b = some_dict, **some_dict)

def simpleFunction96():
    some_tuple = (
        simpleFunction89,
    )

    anyArgs(some_tuple, *some_tuple)

# Complex call with dictionary and key arguments only.
def simpleFunction97():
    some_dict = {
        'a' : simpleFunction90,
        'd' : simpleFunction91
    }

    anyArgs(b = some_dict, c = 1, **some_dict)

def simpleFunction98():
    some_tuple = (
        simpleFunction89,
    )

    anyArgs(*some_tuple, b = some_tuple)

def simpleFunction99():
    some_dict = {
        'a' : simpleFunction90,
    }

    anyArgs(some_dict, **some_dict)

def simpleFunction100():
    def h(f):
        def g():
            return f

        return g

    def f():
        pass

    h(f)

def simpleFunction101():
    def orMaking(a, b):
        x = "axa"
        x += a or b


    orMaking('x', "")

####################################

class SomeClassWithAttributeAccess(object):
    READING = 1

    def use(self):
        return self.READING

def simpleFunction102():
    SomeClassWithAttributeAccess().use()
    SomeClassWithAttributeAccess().use()

####################################

def getInt():
    return 3

def simpleFunction103():
    try:
        raise getInt()
    except TypeError:
        pass

####################################

class ClassWithGeneratorMethod:
    def generator_method(self):
        yield self


def simpleFunction104():
    return list(ClassWithGeneratorMethod().generator_method())


def simpleFunction105():
    """ Delete a started generator, not properly closing it before releasing.
    """
    def generator():
        yield 1
        yield 2

    g = generator()
    next(g)

    del g

def simpleFunction106():
    # Call a PyCFunction with a single argument.
    return sys.getsizeof(type)

def simpleFunction107():
    # Call a PyCFunction with a single argument.
    return sum(i for i in range(x))

def simpleFunction108():
    # Call a PyCFunction with a single argument.
    return sum((i for i in range(x)), 17)

def simpleFunction109():
    # Call a PyCFunction that looks like a method call.
    sys.exc_info()

def simpleFunction110():
    def my_open(*args, **kwargs):
        return(args, kwargs)

    orig_open = __builtins__.open
    __builtins__.open = my_open

    open("me", buffering = True)
    __builtins__.open = orig_open

####################################

u = u'__name__'

def simpleFunction111():
    return getattr(simpleFunction111, u)

####################################

def simpleFunction112():
    TESTFN = "tmp.txt"
    import codecs

    try:
        with open(TESTFN, 'wb') as out_file:
            out_file.write(b'\xa1')
        f = codecs.open(TESTFN, encoding='cp949')
        f.read(2)
    except UnicodeDecodeError:
        pass
    finally:
        try:
            f.close()
        except Exception:
            pass
        try:
            os.unlink(TESTFN)
        except Exception:
            pass


####################################

def simpleFunction113():
    class A(object):
        pass
    a = A()
    a.a = a

    return a

l = []

def simpleFunction114():
    global l
    l += ["something"]

    # Erase it to avoid reference change.
    del l[:]


i = 2**16+1

def simpleFunction115():
    global i
    i += 1

t = tuple(range(259))

def simpleFunction116():
    global t
    t += (2, 3)

    t = tuple(range(259))

def simpleFunction117():
    # Operation tuple+object, error case.
    try:
        return tuple(t) + i
    except TypeError:
        pass


def simpleFunction118():
    # Operation tuple+object, error case.
    try:
        return i + tuple(t)
    except TypeError:
        pass

t2 = tuple(range(9))

def simpleFunction119():
    # Operation tuple+object no error case.
    return tuple(t) + t2

def simpleFunction120():
    # Operation object+tuple no error case.
    return t2 + tuple(t)

def simpleFunction121():
    # Operation tuple+tuple
    return tuple(t2) + tuple(t)


def simpleFunction122():
    # Operation list+object, error case.
    try:
        return list(t) + i
    except TypeError:
        pass


def simpleFunction123():
    # Operation list+object, error case.
    try:
        return i + list(t)
    except TypeError:
        pass

l2 = list(range(9))

def simpleFunction124():
    # Operation list+object no error case.
    return list(t) + l2

def simpleFunction125():
    # Operation object+list no error case.
    return l2 + list(t)

def simpleFunction126():
    # Operation tuple+tuple
    return list(l2) + list(t)


class TupleWithSlots(tuple):
    def __add__(self, other):
        return 42

    def __radd__(self, other):
        return 42

def simpleFunction127():
    # Operation tuple+object with add slot.
    return tuple(t) + TupleWithSlots()

def simpleFunction128():
    # Operation object+tuple with add slot.
    return TupleWithSlots() + tuple(t)

class ListWithSlots(list):
    def __add__(self, other):
        return 42

    def __radd__(self, other):
        return 42

def simpleFunction129():
    # Operation list+object with add slot.
    return list(t) + ListWithSlots()

def simpleFunction130():
    # Operation list+object with add slot.
    return ListWithSlots() + list(t)



####################################

# These need stderr to be wrapped.
tests_stderr = (63,)

# Disabled tests
tests_skipped = {}

result = executeReferenceChecked(
    prefix        = "simpleFunction",
    names         = globals(),
    tests_skipped = tests_skipped,
    tests_stderr  = tests_stderr
)

sys.exit(0 if result else 1)
