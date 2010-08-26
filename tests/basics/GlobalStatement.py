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

print "Function that shadows a global variable with a local variable"
print someFunction1()
print "Function that accesses and changes a global variable declared with a global statement"
print someFunction2()
print "Function that uses a global variable"
print someFunction3()
