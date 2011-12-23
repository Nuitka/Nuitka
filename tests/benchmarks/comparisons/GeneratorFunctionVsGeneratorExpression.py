#!/usr/bin/env python
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

b = range(10000)

def getGeneratorFunction():
   def f():
      for i in b:
         yield i

   return f

def getGeneratorExpression():
   return ( i for i in b )


import time

start = time.time()

f = getGeneratorFunction()

for x in range( 1000 ):
   r = list( f() )

end = time.time()

func_time = end - start

start = time.time()

for x in range( 1000 ):
   r = list( getGeneratorExpression() )

end = time.time()

genexpr_time = end - start

print "Generator Function took", func_time
print "Generator Expression took", genexpr_time
