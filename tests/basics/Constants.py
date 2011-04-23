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
