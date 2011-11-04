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
d[1,] = 2
d[1,2] = 3
d[1,2,3] = 4
L = list(d)
L.sort()
print L

s = "Some information"
ss = s[-1]

print "Constant subscript of string", ss

print "Repr"
print `L`, `ss`

print `0L`

print repr(L), repr(ss)
print repr(3L)

print "Slicing on a list:"
l = [ 1, 3, 5, 7, 11, 13, 17 ]

print l[None:None]

n = None
print l[n:n]
print l[3:n]
print l[n:3]
