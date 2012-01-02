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

""" Playing around with constants only. """

for value in (0, 0L, 3L, -4L, 17, "hey", (0, ),(0L, ), 0.0, -0.0 ):
   print value, repr(value)

print 1 == 0

print repr(0L), repr(0L) == "0L"

print {} is {}

a = ( {}, [] )

a[0][1] = 2
a[1].append( 3 )

print a

print ( {}, [] )

def argChanger( a ):
   a[0][1] = 2
   a[1].append( 3 )

   return a

print argChanger( ( {}, [] ) )

print ( {}, [] )

print set(['foo'])


def mutableConstantChanger():
   a = ( [ 1, 2 ], [ 3 ] )
   print a

   a[ 1 ].append( 5 )
   print a

mutableConstantChanger()
mutableConstantChanger()
