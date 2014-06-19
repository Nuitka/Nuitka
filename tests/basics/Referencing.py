#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
import sys, gc

if not hasattr(sys, "gettotalrefcount"):
    print("Warning, using non-debug Python makes this test ineffective.")
    sys.gettotalrefcount = lambda : 0

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

def simpleFunction5(a = 1*2):
    c = 1
    f = [ a, a + c ]

def simpleFunction6():
    for b in range(6):
        pass

    for c in (1, 2, 3, 4, 5, 6):
        pass


def simpleFunction7(b = 1):
    for b in range(6):
        pass

def simpleFunction8():
    c = []
    c.append(x)

def simpleFunction9(a = 1*2):
    if a == a:
        pass

u = None

def simpleFunction10(a = 1*2):
    x = [u for u in range(8)]

def simpleFunction11():
    f = 1

    while f < 8:
        f += 1

v = None

def simpleFunction12():
    a = [(u,v) for (u,v) in zip(range(8),range(8))]

def cond():
    return 1

def simpleFunction13(a = 1*2):
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
        def __init__(self, a, b):
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
        def base(self):
            return 3

    class EmptyObjectClass(EmptyBaseClass):
        pass

    result = EmptyObjectClass()

    c = result.base()

    return result

def simpleFunction22():
    return True is False and False is not None

def simpleFunction23():
    not 2

def simpleFunction24p(x):
    pass

def simpleFunction24():
    simpleFunction24p( x = 3 )


def simpleFunction25():
    class X:
        f = 1

    def inplace_adder(b):
        X.f += b

    return inplace_adder( 6**8 )


def simpleFunction26():
    class X:
        f = [ 5 ]

    def inplace_adder(b):
        X.f += b

    return inplace_adder( [ 1, 2 ] )

def simpleFunction27():
    a = { "g": 8 }

    def inplace_adder(b):
        a[ "g" ] += b

    return inplace_adder( 3 )

def simpleFunction28():
    a = { "g": [ 8 ], "h": 2 }

    def inplace_adder(b):
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

   class Parent(Base):
      pass

def simpleFunction39():
    class Parent(object):
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
    def nested_args_function((a,b), c):
        return a, b, c

    nested_args_function( ( 1, 2 ), 3 )

def simpleFunction45():
    def nested_args_function((a,b), c):
        return a, b, c

    try:
        nested_args_function( ( 1, ), 3 )
    except ValueError:
        pass

def simpleFunction46():
    def nested_args_function((a,b), c):
        return a, b, c

    try:
        nested_args_function(( 1, 2, 3 ), 3)
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
      def __enter__(self):
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

b = range(10)

def simpleFunction50():
   def getF():
      def f():
         for i in b:
            yield i

      return f

   f = getF()

   for x in range( 2 ):
      r = list( f() )

def simpleFunction51():
   g = ( x for x in range(9) )

   try:
      g.throw( ValueError, 9 )
   except ValueError, e:
      pass

def simpleFunction52():
   g = ( x for x in range(9) )

   try:
      g.throw( ValueError( 9 ) )
   except ValueError, e:
      pass

def simpleFunction53():
    g = ( x for x in range(9) )

    try:
        g.send( 9 )
    except TypeError, e:
        pass

def simpleFunction54():
    g = ( x for x in range(9) )
    g.next()

    try:
       g.send( 9 )
    except TypeError, e:
        pass


def simpleFunction55():
   g = ( x for x in range(9) )

   try:
      g.close()
   except ValueError, e:
      pass

def simpleFunction56():
    def f():
        f()

    try:
        f()
    except RuntimeError:
        pass

def simpleFunction57():
    x = 1
    y = 2

    def f( a = x, b = y):
        return a, b

    f()
    f(2)
    f(3,4)

def simpleFunction58():
    a = 3
    b = 5

    try:
        a = a * 2

        return a
    finally:
        a / b


def simpleFunction59():
    a = 3
    b = 5

    try:
        a = a * 2

        return a
    finally:
        return a / b


def simpleFunction60():
    try:
        raise ValueError(1,2,3), ValueError(1,2,3)
    except Exception:
        pass

def simpleFunction61():
    try:
        raise ValueError, 2, None
    except Exception:
        pass

def simpleFunction62():
    try:
        raise ValueError, 2, 3
    except Exception:
        pass

class X:
    def __del__(self):
        # Super used to reference leak.
        x = super()

        raise ValueError, ValueError(1)

def simpleFunction63():
    def superUser():
        X()

    try:
        superUser()
    except Exception:
        pass

def simpleFunction64():
    x = 2
    y = 3
    z = eval( "x * y" )

def simpleFunction65():
    import array

    a = array.array("b", b"")
    assert a == eval(repr(a), {"array": array.array})

    d = {
        "x" : 2,
        "y" : 3
    }
    z = eval(repr(d), d)


def simpleFunction66():
    import types
    return type(simpleFunction65) == types.FunctionType

def simpleFunction67():
    length = 100000
    pattern = "1234567890\00\01\02\03\04\05\06"

    q, r = divmod(length, len(pattern))
    teststring = pattern * q + pattern[:r]

def simpleFunction68():
    from random import randrange
    x = randrange(18)

def simpleFunction69():
    pools = [ tuple() ]
    g = ((len(pool) == 0,) for pool in pools)
    g.next()

def simpleFunction70():
    def gen():
        try:
            yyyy
        except Exception:
            pass

        yield sys.exc_info()

    try:
        xxxx
    except Exception:
        return list(gen())

def simpleFunction71():
    try:
        undefined
    except Exception:
        try:
            try:
                raise
            finally:
                undefined
        except Exception:
            pass

def simpleFunction71():
    for i in range(10):
        try:
            undefined
        finally:
            break

def simpleFunction72():
    for i in range(10):
        try:
            undefined
        finally:
            return 7


def simpleFunction73():
    import os

    return os

def simpleFunction74():
    def raising_gen():
        try:
            raise TypeError
        except TypeError:
            yield

    g = raising_gen()
    g.next()

    try:
        g.throw(RuntimeError())
    except RuntimeError:
        pass

def simpleFunction75():
    class MyException(Exception):
        def __init__(self, obj):
            self.obj = obj
    class MyObj:
        pass

    def inner_raising_func():
        raise MyException(MyObj())

    try:
        inner_raising_func()
    except MyException:
        try:
            try:
                raise
            finally:
                raise
        except MyException:
            pass

def simpleFunction76():
    class weirdstr(str):
        def __getitem__(self, index):
            return weirdstr(str.__getitem__(self, index))

    (weirdstr("1234"))
    # filter(lambda x: x>="33", weirdstr("1234"))


def simpleFunction77():
    a = "x = 2"
    exec(a)


x = 17

m1 = {}
m2 = {}

def snapObjRefCntMap(before):
   if before:
      global m1
      m = m1
   else:
      global m2
      m = m2

   for x in gc.get_objects():
      if x is m1:
         continue

      if x is m2:
         continue

      m[ str( x ) ] = sys.getrefcount( x )


def checkReferenceCount(checked_function, max_rounds = 10):
   assert sys.exc_info() == ( None, None, None ), sys.exc_info()

   print checked_function.func_name + ":",

   ref_count1 = 17
   ref_count2 = 17

   explain = False

   for count in range( max_rounds ):
      x1 = 0
      x2 = 0

      gc.collect()
      ref_count1 = sys.gettotalrefcount()

      if explain and count == max_rounds - 1:
         snapObjRefCntMap( True )

      checked_function()

      assert sys.exc_info() == ( None, None, None ), sys.exc_info()

      gc.collect()

      if explain and count == max_rounds - 1:
         snapObjRefCntMap( False )

      ref_count2 = sys.gettotalrefcount()

      if ref_count1 == ref_count2:
         print "PASSED"
         break

      # print count, ref_count1, ref_count2
   else:
      print "FAILED", ref_count1, ref_count2, "leaked", ref_count2 - ref_count1

      if explain:
         assert m1
         assert m2

         for key in m1.keys():
            if key not in m2:
               print "*" * 80
               print key
            elif m1[key] != m2[key]:
               print "*" * 80
               print key
            else:
               pass
               # print m1[key]

   assert sys.exc_info() == ( None, None, None ), sys.exc_info()

   gc.collect()


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
checkReferenceCount( simpleFunction14 )
checkReferenceCount( simpleFunction15 )
checkReferenceCount( simpleFunction16 )
checkReferenceCount( simpleFunction17 )
checkReferenceCount( simpleFunction18 )
checkReferenceCount( simpleFunction19 )
checkReferenceCount( simpleFunction20 )
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
checkReferenceCount( simpleFunction32 )
checkReferenceCount( simpleFunction33 )
checkReferenceCount( simpleFunction34 )
checkReferenceCount( simpleFunction35 )
checkReferenceCount( simpleFunction36 )
checkReferenceCount( simpleFunction37 )
checkReferenceCount( simpleFunction38 )
checkReferenceCount( simpleFunction39 )
checkReferenceCount( simpleFunction40 )
checkReferenceCount( simpleFunction41 )
checkReferenceCount( simpleFunction42 )
checkReferenceCount( simpleFunction43 )
checkReferenceCount( simpleFunction44 )
checkReferenceCount( simpleFunction45 )
checkReferenceCount( simpleFunction46 )
checkReferenceCount( simpleFunction47 )
checkReferenceCount( simpleFunction48 )
checkReferenceCount( simpleFunction49 )
checkReferenceCount( simpleFunction50 )
checkReferenceCount( simpleFunction51 )
checkReferenceCount( simpleFunction52 )
checkReferenceCount( simpleFunction53 )
checkReferenceCount( simpleFunction54 )
checkReferenceCount( simpleFunction55 )
# TODO: The function taking a closure of itself, causes a reference leak, that
# we accept for now.
# checkReferenceCount( simpleFunction56 )
checkReferenceCount( simpleFunction57 )
checkReferenceCount( simpleFunction58 )
checkReferenceCount( simpleFunction59 )
checkReferenceCount( simpleFunction60 )
checkReferenceCount( simpleFunction61 )
checkReferenceCount( simpleFunction62 )

# Avoid unraisable output.
old_stderr = sys.stderr
try:
   sys.stderr = open( "/dev/null", "wb" )
except Exception: # Windows
    checkReferenceCount(simpleFunction63)
else:
    checkReferenceCount(simpleFunction63)

    new_stderr = sys.stderr
    sys.stderr = old_stderr
    new_stderr.close()

checkReferenceCount(simpleFunction64)
checkReferenceCount(simpleFunction65)
checkReferenceCount(simpleFunction66)
checkReferenceCount(simpleFunction67)
checkReferenceCount(simpleFunction68)
checkReferenceCount(simpleFunction69)
checkReferenceCount(simpleFunction70)
checkReferenceCount(simpleFunction71)
checkReferenceCount(simpleFunction72)
checkReferenceCount(simpleFunction73)
checkReferenceCount(simpleFunction74)
checkReferenceCount(simpleFunction75)
# TODO: The class taking a closure of itself, causes a reference leak, that
# we accept for now.
# checkReferenceCount( simpleFunction76 )
checkReferenceCount(simpleFunction77)
