#
#     Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are in the public domain. It is at least Free Software
#     where it's copied from other people. In these cases, it will normally be
#     indicated.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     Please leave the whole of this copyright notice intact.
#
def dictOrderCheck():
    def key1():
        print "key1 called"

        return 1
    def key2():
        print "key2 called"

        return 2
    def value1():
        print "value1 called"

        return 11
    def value2():
        print "value2 called"

        return 22

    print "Checking order of calls in dictionary creation from callables:"

    print { key1() : value1(), key2() : value2() }

def listOrderCheck():
    def value1():
        print "value1 called"

        return 11
    def value2():
        print "value2 called"

        return 22

    print [ value1(), value2() ]

def sliceOrderCheck():
    d = range(10)

    def lvalue():
        print "lvalue",

        return d

    def rvalue():
        print "rvalue",

        return range(2)

    def rvalue4():
        print "rvalue",

        return range(4)

    def low():
        print "low",

        return 0

    def high():
        print "high",

        return 4

    def step():
        print "step",

        return 2

    print "Complex slice lookup", lvalue()[ low() : high() : step() ]

    print "Complex slice assignment",
    lvalue()[ low() : high() : step() ] = rvalue()
    print d

    print "Complex slice del",
    del lvalue()[ low() : high() : step() ]
    print d

    print "Complex inplace slice operation",
    # TODO: This gives an error in CPython, but not in Nuitka.
    # lvalue()[ low() : high() : step() ] += rvalue()
    print d

    d = range(10)

    print "Simple slice lookup", lvalue()[ low() : high() ]

    print "Simple slice assignment",
    lvalue()[ 3 + low() : 3 + high() ] = rvalue()
    print d

    print "Simple slice del",
    del lvalue()[ 3 + low() : 3 + high() ]
    print d

    print "Simple inplace slice operation",
    lvalue()[ low() : high() ] += rvalue4()
    print d


def subscriptOrderCheck():
    d={}

    def lvalue():
        print "lvalue",

        return d

    def rvalue():
        print "rvalue",

        return 2

    def subscript():
        print "subscript",

        return 1

    lvalue()[ subscript() ] = rvalue()
    print d

    print lvalue()[ subscript() ]

    del lvalue()[ subscript() ]
    print d

def compareOrderCheck():
    def lvalue():
        print "lvalue",

        return 1

    def rvalue():
        print "rvalue",

        return 2

    print "==", lvalue() == rvalue()
    print "<=", lvalue() <= rvalue()
    print ">=", lvalue() >= rvalue()
    print "!=", lvalue() != rvalue()
    print ">", lvalue() > rvalue()
    print "<", lvalue() < rvalue()

def generatorOrderCheck():
    def default1():
        print "default1",

        return 1

    def default2():
        print "default2",

        return 2

    def default3():
        print "default3",

        return 3

    def generator( a = default1(), b = default2(), c = default3() ):
        yield a
        yield b
        yield c

    print list( generator() )

def classOrderCheck():
    print "Checking order of class constructions:"

    class B1:
        pass

    class B2:
        pass

    def base1():
        print "base1",

        return B1

    def base2():
        print "base2",

        return B2

    def deco1( cls ):
        print "deco1",

        return cls

    def deco2( cls ):
        print "deco2",

        return B2


    @deco2
    @deco1
    class X( base1(), base2() ):
        print "class body",

    print

def inOrderCheck():
    print "Checking order of in operator:"

    def container():
        print "container",

        return [ 3 ]

    def searched():
        print "searched",

        return 3

    print searched() in container()

dictOrderCheck()
listOrderCheck()
subscriptOrderCheck()
compareOrderCheck()
sliceOrderCheck()
generatorOrderCheck()
classOrderCheck()
inOrderCheck()
