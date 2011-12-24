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
class SimpleClass:
    """ The class documentation."""

    print locals()

    class_var = 1

    def __init__( self, init_parameter ):
        self.x = init_parameter

    def normal_method( self, arg1, arg2 ):
        self.arg1 = arg1
        self.arg2 = arg2

        return self.arg1, self.arg2, self.x, self

    @staticmethod
    def static_method():
        return "something"

print "Simple class:", SimpleClass
print "Lives in", SimpleClass.__module__
print "Documentation", SimpleClass.__doc__
print "Instantiate simple class:", SimpleClass( 14 )
print "Call simple class normal method:", SimpleClass( 11 ).normal_method( 1, 2 )
print "Call simple class static method:", SimpleClass( 11 ).static_method()

class MetaClass( type ):
    def __init__( cls, name, bases, dictionary ):
        print "MetaClass is called."
        cls.addedin = 5

print MetaClass

class ComplexClass:
    __metaclass__ = MetaClass

print ComplexClass, dir( ComplexClass )

print ComplexClass, hasattr( ComplexClass, "addedin" ) and ComplexClass.addedin


def function():
    x = 1

    class DynamicClass:
        y = x

    return DynamicClass

    x = 2

print function(), function().y

def strangeClassBehaviour():
    class StrangeClass(object):
        count = 0

        def __new__( cls ):
            print "__new__"

            cls.count += 1
            return object.__new__(cls)

        def __del__( self ):
            print "__del__"

            cls = self.__class__
            cls.count -= 1
            assert cls.count >= 0


    x = StrangeClass()

    return x.count

print "Strange class with __new__ and __del__ overloads", strangeClassBehaviour()

class ClosureLocalizer:
    function = function

    def deco( f ):
        return f

    @deco
    def x():
        pass

print "Class with a name from module level renamed to local", ClosureLocalizer.function

print "Class with decorator"

def classdecorator( cls ):
    print "cls decorator", cls.addedin

    return cls

@classdecorator
class MyClass:
    __metaclass__ = MetaClass

print "Class that updates its locals",

class DictUpdating:
    a = 1

    locals().update( { "b" : 2 } )

    for f in range(6):
        locals()[ "test_%s" % f ] = f

print DictUpdating.b, DictUpdating.test_4

def functionThatOffersClosureToPassThroughClass( x ):
    class Foo:
        global x
        x = 1

        def __call__(self, y):
            return x + y

    return Foo()

print functionThatOffersClosureToPassThroughClass(6)(2),
print x

class NameCollisionClosure:
    def x( self ):
        return x

print NameCollisionClosure, NameCollisionClosure().x()
