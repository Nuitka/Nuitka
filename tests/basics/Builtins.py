# 
#     Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Python test that I originally created or extracted from other peoples
#     work. I put my parts of it in the public domain. It is at least Free
#     Software where it's copied from other people. In these cases, I will
#     indicate it.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the new code, or in the alternative
#     a BSD license to the new code, should your jurisdiction prevent this. This
#     is to reserve my ability to re-license the code at any time.
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
