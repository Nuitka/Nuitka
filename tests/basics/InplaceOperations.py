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
