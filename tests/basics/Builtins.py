#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
        print "Accessing z writing to locals in exec function gives Exception", e

    return r, y

    # Note: This exec is dead code, and still changes the behaviour of
    # CPython, because it detects exec during parse already.
    exec ""

print "Testing locals():"
print someFunctionWritingLocals()
print someFunctionWritingLocalsContainingExec()

print "Vars on module level", vars()

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

try:
    print "Empty range call",
    print range()
except TypeError, e:
    print "Gives exception:", e

print "List from iterable", list( "abc" ), list()
print "List from sequence", list( sequence = (0, 1, 2) )
print "Tuple from iterable", tuple( "cda" ), tuple()
print "Tuple from sequence", tuple( sequence = (0, 1, 2) )

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

print "Oct from constants", oct( 467 ), oct( 0 )
print "Found during optimization", oct( int( "3" ) )

print "Hex from constants", hex( 467 ), hex( 0 )
print "Found during optimization", hex( int( "3" ) )


print "Bin from constants", bin( 467 ), bin( 0 )
print "Found during optimization", bin( int( "3" ) )

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
    print chr()
except Exception, e:
    print "Disallowed without args", repr(e)

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

# TODO: This is calls, not really builtins.
a = 2

print "Can optimize the star list argness away", int(*(a,)),
print "Can optimize the empty star list arg away", int(*tuple()),
print "Can optimize the empty star dict arg away", long(**dict())

print "Dict building with keyword arguments", dict(), dict( a = f )
print "Dictionary entirely from constant args", dict(q='Guido', w='van', e='Rossum', r='invented', t='Python', y='')

a = 5
print "Instance check recognises", isinstance( a, int )

try:
    print "Instance check with too many arguments", isinstance( a, long, int )
except Exception, e:
    print "Too many args", repr(e)

try:
    print "Instance check with too many arguments", isinstance( a )
except Exception, e:
    print "Too few args", repr(e)
