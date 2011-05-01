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
import sys, gc

gc.disable()

def simpleFunction1():
   return 1

def simpleFunction2():
    y = 3 * x
    y = 3
    y = 2

    return x*2

def simpleFunction3():
    def contained():
        return x

    return contained

def simpleFunction4():
    y = 1

    def contained():
        return y

    return contained

def simpleFunction5( a = 1*2 ):
    c = 1
    f = [ a, a + c ]

def simpleFunction6():
    for b in range(6):
        pass

    for c in (1, 2, 3, 4, 5, 6):
        pass


def simpleFunction7( b = 1 ):
    for b in range(6):
        pass

def simpleFunction8():
    c = []
    c.append( x )

def simpleFunction9( a = 1*2 ):
    if a == a:
        pass

u = None

def simpleFunction10( a = 1*2 ):
    x = [u for u in range(8)]

def simpleFunction11():
    f = 1

    while f < 8:
        f += 1

v = None

def simpleFunction12():
    a = [ (u,v) for (u,v) in zip(range(8),range(8)) ]

def cond():
    return 1

def simpleFunction13( a = 1*2 ):
    pass

def simpleFunction14p(x):
    try:
        simpleFunction14p(1,1)
    except TypeError, e:
        pass

    try:
        simpleFunction14p(1,1)
    except TypeError:
        pass

def simpleFunction14():
    simpleFunction14p( 3 )

def simpleFunction15p(x):
    try:
        try:
            x += 1
        finally:
            try:
                x *= 1
            finally:
                z = 1
    except:
        pass

def simpleFunction15():
    simpleFunction15p( [ 1 ] )

def simpleFunction16():
    class EmptyClass:
        pass

    return EmptyClass

def simpleFunction17():
    class EmptyObjectClass:
        pass

    return EmptyObjectClass()

def simpleFunction18():
    closured = 1

    class NonEmptyClass:
        def __init__( self, a, b ):
            self.a = a
            self.b = b

        inside = closured

    return NonEmptyClass( 133, 135 )

def simpleFunction19():
    lam = lambda l : l+1

    return lam( 9 ), lam


def simpleFunction20():
    try:
        a = []
        a[1]
    except IndexError, e:
        pass


def simpleFunction21():
    class EmptyBaseClass:
        def base( self ):
            return 3

    class EmptyObjectClass( EmptyBaseClass ):
        pass

    result = EmptyObjectClass()

    c = result.base()

    return result

def simpleFunction22():
    return True is False and False is not None

def simpleFunction23():
    not 2

def simpleFunction24p( x ):
    pass

def simpleFunction24():
    simpleFunction24p( x = 3 )


def simpleFunction25():
    class X:
        f = 1

    def inplace_adder( b ):
        X.f += b

    return inplace_adder( 6**8 )


def simpleFunction26():
    class X:
        f = [ 5 ]

    def inplace_adder( b ):
        X.f += b

    return inplace_adder( [ 1, 2 ] )

def simpleFunction27():
    a = { "g": 8 }

    def inplace_adder( b ):
        a[ "g" ] += b

    return inplace_adder( 3 )

def simpleFunction28():
    a = { "g": [ 8 ], "h": 2 }

    def inplace_adder( b ):
        a[ "g" ] += b

    return inplace_adder( [ 3, 5 ] )


def simpleFunction29():
    return "3" in "7"

def simpleFunction30():
    def generatorFunction():
        yield 1
        yield 2
        yield 3

def simpleFunction31():
   def generatorFunction():
      yield 1
      yield 2
      yield 3

   a = []

   for y in generatorFunction():
      a.append( y )

   for z in generatorFunction():
      a.append( z )


def simpleFunction32():
   def generatorFunction():
      yield 1

   gen = generatorFunction()
   gen.next()

def simpleFunction33():
   def generatorFunction():
      a = 1

      yield a

   a = []

   for y in generatorFunction():
      a.append( y )


def simpleFunction34():
   try:
      raise ValueError
   except:
      pass

def simpleFunction35():
   try:
      raise ValueError(1,2,3)
   except:
      pass


def simpleFunction36():
   try:
      raise TypeError, (3,x,x,x)
   except TypeError:
      pass

def simpleFunction37():
   l = [ 1, 2, 3 ]

   try:
      a, b = l
   except ValueError:
      pass


def simpleFunction38():
   class Base:
      pass

   class Parent( Base ):
      pass

def simpleFunction39():
   class Parent( object ):
      pass


def simpleFunction40():
   def myGenerator():
      yield 1

   myGenerator()

def simpleFunction41():
   a = b = 2


def simpleFunction42():
   a = b = 2 * x


def simpleFunction43():
   class D:
      pass

   a = D()

   a.b = 1

def simpleFunction44():
   def nested_args_function( (a,b), c ):
      return a, b, c

   nested_args_function( ( 1, 2 ), 3 )

def simpleFunction45():
   def nested_args_function( (a,b), c ):
      return a, b, c

   try:
      nested_args_function( ( 1, ), 3 )
   except ValueError:
      pass

def simpleFunction46():
   def nested_args_function( (a,b), c ):
      return a, b, c

   try:
      nested_args_function( ( 1, 2, 3 ), 3 )
   except ValueError:
      pass

def simpleFunction47():
   def reraisy():
      def raisingFunction():
         raise ValueError(3)

      def reraiser():
         raise

      try:
         raisingFunction()
      except:
         reraiser()


   try:
      reraisy()
   except:
      pass

def simpleFunction48():
   class BlockExceptions:
      def __enter__( self ):
         pass
      def __exit__( self, exc, val, tb):
         return True

   with BlockExceptions():
      raise ValueError()

template = "lala %s lala"

def simpleFunction49():
   c = 3
   d = 4

   a = x, y = b,e = (c,d)

x = 17

def checkReferenceCount( checked_function, warmup = False ):
   sys.exc_clear()
   print checked_function,

   ref_count1 = 17
   ref_count2 = 17

   gc.collect()
   ref_count1 = sys.gettotalrefcount()

   if warmup:
      checked_function()

   sys.exc_clear()
   gc.collect()

   ref_count2 = sys.gettotalrefcount()

   if ref_count1 == ref_count2 and warmup and False:
      print "WARMUP not needed",

   gc.collect()
   ref_count1 = sys.gettotalrefcount()

   checked_function()

   sys.exc_clear()
   gc.collect()

   ref_count2 = sys.gettotalrefcount()

   if ref_count1 != ref_count2:
      print "FAILED", ref_count1, ref_count2
   else:
      print "PASSED"

checkReferenceCount( simpleFunction1 )
checkReferenceCount( simpleFunction2 )
checkReferenceCount( simpleFunction3 )
checkReferenceCount( simpleFunction4 )
checkReferenceCount( simpleFunction5 )
checkReferenceCount( simpleFunction6 )
checkReferenceCount( simpleFunction7 )
checkReferenceCount( simpleFunction8 )
checkReferenceCount( simpleFunction9 )
checkReferenceCount( simpleFunction10 )
checkReferenceCount( simpleFunction11 )
checkReferenceCount( simpleFunction12 )
checkReferenceCount( simpleFunction13 )
checkReferenceCount( simpleFunction14, warmup = True )
checkReferenceCount( simpleFunction15, warmup = True )
checkReferenceCount( simpleFunction16 )
checkReferenceCount( simpleFunction17 )
checkReferenceCount( simpleFunction18 )
checkReferenceCount( simpleFunction19 )
checkReferenceCount( simpleFunction20, warmup = True )
checkReferenceCount( simpleFunction21 )
checkReferenceCount( simpleFunction22 )
checkReferenceCount( simpleFunction23 )
checkReferenceCount( simpleFunction24 )
checkReferenceCount( simpleFunction25 )
checkReferenceCount( simpleFunction26 )
checkReferenceCount( simpleFunction27 )
checkReferenceCount( simpleFunction28 )
checkReferenceCount( simpleFunction29 )
checkReferenceCount( simpleFunction30 )
checkReferenceCount( simpleFunction31 )
# checkReferenceCount( simpleFunction32, warmup = True )
checkReferenceCount( simpleFunction33 )
checkReferenceCount( simpleFunction34, warmup = True )
checkReferenceCount( simpleFunction35, warmup = True )
checkReferenceCount( simpleFunction36, warmup = True )
checkReferenceCount( simpleFunction37, warmup = True )
checkReferenceCount( simpleFunction38 )
checkReferenceCount( simpleFunction39, warmup = True )
checkReferenceCount( simpleFunction40 )
checkReferenceCount( simpleFunction41 )
checkReferenceCount( simpleFunction42 )
checkReferenceCount( simpleFunction43 )
checkReferenceCount( simpleFunction44 )
checkReferenceCount( simpleFunction45, warmup = True )
checkReferenceCount( simpleFunction46, warmup = True )
checkReferenceCount( simpleFunction47, warmup = True )
checkReferenceCount( simpleFunction48, warmup = True )
checkReferenceCount( simpleFunction49 )
