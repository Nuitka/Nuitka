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

def someFunctionUsingLocals():
    x = 1
    r = locals()


    # This is without effect on r. It doesn't mention y at all
    y = 2

    # This adds z to the locals, but only that.
    r[ "z" ] = 3

    return r, y

print "Testing locals()"
print someFunctionUsingLocals()

module_locals = locals()

import os
module_locals[ "__file__" ] = os.path.basename( module_locals[ "__file__" ] )

print "Use on the module level", module_locals

def someFunctionUsingGlobals():
    g = globals()

    g[ "hallo" ] = "du"

    global hallo
    print "hallo", hallo


print "Testing globals():"
someFunctionUsingGlobals()

print "Testing dir():"

print "Module dir",

def someFunctionUsingDir():
    x = someFunctionUsingGlobals()

    print "Function dir", dir()

someFunctionUsingDir()

print "Making a new type, with type() and 3 args:",
new_class = type( "Name", (object, ), {} )
print new_class, new_class()

print "None has type", type(None)

print "Constant ranges", range( 2 ), range( 1, 6 ), range( 3, 0, -1 ), range( 3, 8, 2 ), range(5, -5, -3)
print "Border cases", range(0), range(-1), range( -1, 1 )

try:
    print "Range with 0 step gives:",
    print range( 3, 8, 0 )
except ValueError, e:
    print e
