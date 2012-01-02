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
x = 1
x += 2

print "Plain inplace:", x

z = [ 1, 2, 3 ]
z[1] += 5

print "List inplace:", z[1]

h = { "a" : 3 }
h["a"] += 2

print "Dict inplace:", h["a"]

class B:
    a = 1

B.a += 2

print "Class attribute inplace:", B.a

h = [ 1, 2, 3, 4 ]
h[1:2] += (2,3)

print "List sclice inplace", h
