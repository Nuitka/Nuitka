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



def decorator1( f ):
    print "Executing decorator 1"

    def deco_f():
        return f() + 2

    return deco_f

def decorator2( f ):
    print "Executing decorator 2"

    def deco_f():
        return f() * 2

    return deco_f

# Result of function now depends on correct order of applying the decorators
@decorator1
@decorator2
def function1():
    return 3

print function1()

def deco_returner1():
    print "Executing decorator returner D1"
    return decorator1

def deco_returner2():
    print "Executing decorator returner D2"
    return decorator2

@deco_returner1()
@deco_returner2()
def function2():
    return 3

print function2()
