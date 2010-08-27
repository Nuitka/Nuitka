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