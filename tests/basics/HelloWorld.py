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
# -*- coding: utf-8 -*-
print "Hello World from Module main Code"

def printHelloWorld():
    print "Hello World from Function main Code"

print printHelloWorld

printHelloWorld()

def printHelloWorld2( arg ):
    print arg

print printHelloWorld2

printHelloWorld2( "Hello World from Function positional argument" )
printHelloWorld2( arg = "Hello World from Function keyword argument" )

def printHelloWorld3( arg = "Hello World from Function default argument" ):
    print arg

print printHelloWorld3

printHelloWorld3()