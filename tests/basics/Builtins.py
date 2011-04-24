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

def someFunctionWritingLocals():
    x = 1
    r = locals()

    # This is without effect on r. It doesn't mention y at all
    y = 2

    # This adds z to the locals, but only that.
    r[ "z" ] = 3
    del x

    try:
        z
    except Exception, e:
        print "Accessing z writing to locals gives Exception", e

    return r, y

def someFunctionWritingLocalsContainingExec():
    x = 1
    r = locals()

    # This is without effect on r. It doesn't mention y at all
    y = 2

    # This adds z to the locals, but only that.
    r[ "z" ] = 3

    try:
        z
    except Exception, e:
        print "Accessing z writing to locals gives Exception", e

    return r, y

    exec ""

print "Testing locals():"
print someFunctionWritingLocals()
print someFunctionWritingLocalsContainingExec()

module_locals = locals()

import os
module_locals[ "__file__" ] = os.path.basename( module_locals[ "__file__" ] )

print "Use of locals on the module level", module_locals

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

print "Corner case large negative value", range(-2**100)
print "Corner case with large start/end values in small range", range(2**100,2**100+2)

try:
    print "Range with 0 step gives:",
    print range( 3, 8, 0 )
except ValueError, e:
    print e

try:
    print "Range with float:",
    print range(1.0)
except TypeError, e:
    print "Gives exception:", e

print "List from iterable", list( "abc" ), list()
print "Tuple from iterable", tuple( "cda" ), tuple()
print "Dictionary from iterable and keywords", dict( ( "ab", ( 1, 2 ) ), f = 1, g = 1 )
print "More constant dictionaries", {'two': 2, 'one': 1}, {}, dict()
g = {'two': 2, 'one': 1}
print "Variable dictionary", dict( g )
print "Found during optimization", dict( dict( {'le': 2, 'la': 1} ), fu = 3 ), dict( named = dict( {'le': 2, 'la': 1} ) )

print "Floats from constants", float( "3.0" ), float( x = 9.0 ), float()
print "Found during optimization", float( float( "3.2" ) ), float( x = float( 11.0 ) )

print "Strs from constants", str( "3.3" ), str( object = 9.1 ), str()
print "Found during optimization", str( float( "3.3" ) ), str( object = float( 12.0 ) )

print "Bools from constants", bool( "3.3" ), bool( x = 9.1 ), bool(0), bool()
print "Found during optimization", bool( float( "3.3" ) ), bool( x = float( 0.0 ) )

print "Ints from constants", int( "3" ), int( x = "9" ), int( "f", 16 ), int( x = "e", base = 16 ), int( base = 2 ), int( "0101", base = 2 ), int(0), int()
print "Found during optimization", int( int( "3" ) ), int( x = int( 0.0 ) )

try:
    int( 1,2,3 )
except Exception, e:
    print "Too many args gave", repr(e)

try:
    int( y = 1 )
except Exception, e:
    print "Wrong arg", repr(e)

f = 3
print "Unoptimized call of int", int( "0" * f, base = 16 )

d = { "x" : "12", "base" : 8 }
print "Dict call of int", int( **d )

try:
    print ord()
except Exception, e:
    print "Disallowed without args", repr(e)

try:
    print ord( s = 1 )
except Exception, e:
    print "Disallowed keyword args", repr(e)

try:
    print ord( 1, 2 )
except Exception, e:
    print "Too many plain args", repr(e)

try:
    print ord( 1, s = 2 )
except Exception, e:
    print "Too many args, some keywords", repr(e)

try:
    print str( "1", offer = 2 )
except Exception, e:
    print "Too many args, some keywords", repr(e)
