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

x = 2

def someFunction1():
    x = 3

    return x

def someFunction2():
    global x

    x = 4

    return x

def someFunction3():
    return x

def someNestedGlobalUser1():
    z = 1

    def setZ():
        global z

        z = 3

    setZ()

    return z

def someNestedGlobalUser2():
    z = 1

    exec """
def setZ():
    global z

    z = 3

setZ()
"""

    return z

def someNestedGlobalUser3():
    exec """
z = 1

def setZ():
    global z

    z = 3

setZ()
"""
    return z


def someNestedGlobalUser4():
    z = 1

    exec """
z = 1

def setZ():
    global z

    z = 3

setZ()
"""
    return z

def someNestedGlobalUser5():
    z = 1

    exec """
z = 3

"""
    return z

def someNestedGlobalUser6():
    exec """
z = 3

"""
    return z



print "Function that shadows a global variable with a local variable"
print someFunction1()
print "Function that accesses and changes a global variable declared with a global statement"
print someFunction2()
print "Function that uses a global variable"
print someFunction3()
print "Functions that uses a global variable in a nested function in various ways:"
print someNestedGlobalUser1, someNestedGlobalUser1()
print someNestedGlobalUser2, someNestedGlobalUser2()
print someNestedGlobalUser3, someNestedGlobalUser3()
print someNestedGlobalUser4, someNestedGlobalUser4()
print someNestedGlobalUser5, someNestedGlobalUser5()
print someNestedGlobalUser6, someNestedGlobalUser6()


x = 7
def f():
    x = 1
    def g():
        global x
        def i():
            def h():
                return x
            return h()
        return i()
    return g()


print f()
