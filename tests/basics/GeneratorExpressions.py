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

print "Generator expression that demonstrates the timing:"
def iteratorCreationTiming():
    def getIterable( x ):
        print "Getting iterable", x
        return Iterable( x )

    class Iterable:
        def __init__( self, x ):
            self.x = x
        def __iter__( self ):
            print "Giving iter now", self.x

            return iter(range(self.x))

    gen = ( (y,z) for y in getIterable( 3 ) for z in getIterable( 2 ) )
    print gen
    gen.next()
    res = tuple( gen )
    print res
    try:
        gen.next()
    except StopIteration:
        print "Use past end gave StopIteration as expected"

iteratorCreationTiming()

print "Generator expressions that demonstrate the use of conditions:"

print tuple( x for x in range(8) if x % 2 == 1 )
print tuple( x for x in range(8) if x % 2 == 1 for z in range(8) if z == x  )

# print tuple( x for (x,y) in zip(range(2),range(4)))
