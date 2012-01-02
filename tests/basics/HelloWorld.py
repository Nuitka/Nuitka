# -*- coding: utf-8 -*-
#
#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python test originally created or extracted from other peoples work. The
#     parts and resulting tests are too small to be protected and therefore
#     is in the public domain.
#
#     If you submit Kay Hayen patches to this in either form, you automatically
#     grant him a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. Obviously it
#     won't affect code that comes to him indirectly or code you don't submit to
#     him.
#
#     This is to reserve my ability to re-license the official code at any time,
#     to put it into public domain or under PSF.
#
#     Please leave the whole of this copyright notice intact.
#
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