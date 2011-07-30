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

print "Generator expression that demonstrates the timing:"
def iteratorCreationTiming():
    def getIterable( x ):
        print "Getting iterable", x
        return Iterable( x )

    class Iterable:
        def __init__( self, x ):
            self.x = x
            self.values = range( x )
            self.count = 0

        def __iter__( self ):
            print "Giving iter now", self.x

            return self

        def next( self ):
            print "Next of", self.x, self.count

            if len( self.values ) > self.count:
                self.count += 1

                return self.values[ self.count - 1 ]
            else:
                raise StopIteration

        def __del__( self ):
            print "Deleting", self.x


    gen = ( (y,z) for y in getIterable( 3 ) for z in getIterable( 2 ) )

    print "Using generator", gen
    gen.next()
    res = tuple( gen )
    print res

    try:
        gen.next()
    except StopIteration:
        print "Use past end gave StopIteration as expected"

    print "Early aborting generator"

    gen2 = ( (y,z) for y in getIterable( 3 ) for z in getIterable( 2 ) )
    del gen2

iteratorCreationTiming()

print "Generator expressions that demonstrate the use of conditions:"

print tuple( x for x in range(8) if x % 2 == 1 )
print tuple( x for x in range(8) if x % 2 == 1 for z in range(8) if z == x  )

print tuple( x for (x,y) in zip(range(2),range(4)))

print "Directory of generator expressions:"
for_dir = ( x for x in [1] )

gen_dir = dir( for_dir )

print sorted( g for g in gen_dir if not g.startswith( "gi_" ) )


def genexprSend():
    x = ( x for x in range(9) )

    print "Sending too early:"
    try:
        x.send(3)
    except TypeError, e:
        print "Gave expected TypeError with text:", e

    z = x.next()

    y = x.send(3)

    print "Send return value", y
    print "And then next gave", x.next()

    print "Throwing an exception from it."
    try:
        x.throw( ValueError, 2, None )
    except ValueError, e:
        print "Gave expected ValueError with text:", e

    try:
        x.next()
        print "Next worked even after thrown error"
    except StopIteration, e:
        print "Gave expected stop iteration after throwing exception in it:", e


    print "Throwing another exception from it."
    try:
        x.throw( ValueError, 5, None )
    except ValueError, e:
        print "Gave expected ValueError with text:", e


print "Generator expressions have send too:"

genexprSend()

def genexprClose():
    x = ( x for x in range(9) )

    print "Immediate close:"

    x.close()
    print "Closed once"

    x.close()
    print "Closed again without any trouble"

genexprClose()

def genexprThrown():

    def checked( z ):
        if z == 3:
            raise ValueError

        return z

    x = ( checked( x ) for x in range(9) )

    try:
        for count, value in enumerate( x ):
            print count, value
    except ValueError:
        print count+1, ValueError

    try:
        x.next()

        print "Allowed to do next() after raised exception from the generator expression"
    except StopIteration:
        print "Exception in generator, disallowed next() afterwards."

genexprThrown()

def nestedExpressions():
    a = [x for x in range(10)]
    b = (x for x in (y for y in a))

    print "nested generator expression", list(b)

nestedExpressions()

def lambdaGenerators():
    a = 1

    x = lambda : (yield a)

    print "Simple lambda generator", x, x(), list( x() )

    y = lambda : ((yield 1),(yield 2))

    print "Complex lambda generator", y, y(), list( y() )

lambdaGenerators()

def functionGenerators():
    # Like lambdaGenerators, to show how functions behave differently if at all.

    a = 1

    def x():
        yield a

    print "Simple function generator", x, x(), list( x() )

    def y():
        yield((yield 1),(yield 2))

    print "Complex function generator", y, y(), list( y() )

functionGenerators()
