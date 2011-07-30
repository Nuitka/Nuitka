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

print "List contraction on the module level:"
x = [(u if u%2==0 else 0) for u in range(10)]
print x

print "List contraction on the function level:"
def someFunction():
   x = [(u if u%2==0 else 0) for u in range(10)]
   print x

someFunction()

print "List contractions with no, 1 one 2 conditions:"
def otherFunction():
    print [ x for x in range(8) ]
    print [ x for x in range(8) if x % 2 == 1 ]
    print [ x for x in range(8) if x % 2 == 1 if x > 4 ]

otherFunction()

print "Complex list contractions with more than one for:"
def complexContractions():
   print [ (x,y) for x in range(3) for y in range(5) ]

   seq = range(3)
   res = [(i, j, k) for i in iter(seq) for j in iter(seq) for k in iter(seq)]

   print res

complexContractions()

print "Contraction for 2 fors and one final if refering to first for:"

def trickyContraction():
   class Range:
      def __init__( self, value ):
         self.value = value

      def __iter__( self ):
         print "Giving range iter to", self.value

         return iter( range( self.value ))

   def Cond( y ):
      print "Checking against", y

      return y == 1

   r = [ (x,z,y) for x in Range(3) for z in Range(2) for y in Range(4) if Cond(y) ]
   print "result", r

trickyContraction()

def lambdaWithcontraction( x ):
   l = lambda x : [ z for z in range(x) ]
   r = l(x)
   print locals()

lambdaWithcontraction( 3 )
