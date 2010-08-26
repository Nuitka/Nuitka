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

a = 3
b = 7
c = [ 7, 8 ]
d = 15

print "+", a + b
print "-", a - b
print "*", a * b
print "/", a / b
print "//", a // b
print "%", b % a
print "& (2)", a & b
print "| (2)", a | b
print "& (3)", a & b & d
print "| (3)", a | b | d
print "^ (2)", a ^ b
print "^ (3)", a ^ b ^ d
print "**", a ** b
print "<<", a << b
print ">>", b >> a
print "in", b in c
print "not in", b not in c
print "<", a < b
print ">", a > b
print "==", a == b
print "<=", a <= b
print ">=", a >= b
print "!=", a != b
print "is", a is b
print "is not", a is not b

print "~", ~ b
print "-", - b
print "+", + b

l =  { ( "a", "c" ) : "a,c", "b" : 2, "c" : 3, "d" : 4  }
l[ "l", ] = "6"


print "Extended slicing:"
print "Should be a,c:", l[ "a", "c" ]

print "Short form of extended slicing:"

d = {}
d[1] = 1
# TODO: Enable this one CPython bug is fixed.
# d[1,] = 2
d[1,2] = 3
d[1,2,3] = 4
L = list(d)
L.sort()
print L
