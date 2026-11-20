#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

import inspect
import pprint
import sys


def displayDir(l):
    if "__firstlineno__" in l:
        l.remove("__firstlineno__")

    if "__static_attributes__" in l:
        l.remove("__static_attributes__")

    return pprint.pformat(l)


def displayDict(d):
    if "__loader__" in d:
        d = dict(d)
        d["__loader__"] = "<__loader__ removed>"

    if "__file__" in d:
        d = dict(d)
        d["__file__"] = "<__file__ removed>"

    if "__firstlineno__" in d:
        d = dict(d)
        del d["__firstlineno__"]

    # Avoid recursion that we don't offer for classes.
    if "__locals__" in d:
        d = dict(d)
        del d["__locals__"]

    return pprint.pformat(d)


class SimpleClass:
    "The class documentation."  # Leading space on purpose.

    # TODO: Doesn't work with Python3, because we don't yet make our own dict
    # visible.  print locals()
    print("Class locals, while building", displayDict(locals()))

    class_var = 1

    def __init__(self, init_parameter):
        self.x = init_parameter

    def normal_method(self, arg1, arg2):
        self.arg1 = arg1
        self.arg2 = arg2

        return self.arg1, self.arg2, self.x, self

    @staticmethod
    def static_method():
        return "something"


print("Simple class:", SimpleClass)
print("Lives in", SimpleClass.__module__)
print("Documentation", SimpleClass.__doc__)
print("Instantiate simple class:", SimpleClass(14))
print("Call simple class normal method:", SimpleClass(11).normal_method(1, 2))
print("Call simple class static method:", SimpleClass(11).static_method())


class MetaClass(type):
    def __init__(cls, name, bases, dictionary):
        print("MetaClass is called.")
        cls.added_in = 5


print(MetaClass)


class ComplexClass:
    __metaclass__ = MetaClass


print(ComplexClass, displayDir(dir(ComplexClass)))

print(ComplexClass, hasattr(ComplexClass, "added_in") and ComplexClass.added_in)


def function():
    x = 1

    class DynamicClass:
        y = x

    x = 2

    return DynamicClass


print(function(), function().y)


def strangeClassBehavior():
    class StrangeClass(object):
        count = 0

        def __new__(cls):
            print("__new__")

            cls.count += 1
            return object.__new__(cls)

        def __del__(self):
            print("__del__")

            cls = self.__class__
            cls.count -= 1
            assert cls.count >= 0

    x = StrangeClass()

    return x.count


print("Strange class with __new__ and __del__ overloads", strangeClassBehavior())


class ClosureLocalizer:
    function = function

    # Using what looks like a method as a decorator.
    def deco(f):
        f.decorated = True

        return f

    @deco
    def x(self):
        pass


print("Class with a name from module level renamed to local", ClosureLocalizer.function)
print("Class method decorated", ClosureLocalizer().x.decorated)


class MethodDispatcher(object):
    def __init__(self, name):
        self.name = name
        self.types = []

    def add(self, types, func):
        self.types.append(types)


def dispatch(*types):
    def _decorator(func):
        name = func.__name__
        class_locals = inspect.currentframe().f_back.f_locals
        dispatcher = class_locals.get(name, MethodDispatcher(name))
        dispatcher.add(types, func)
        return dispatcher

    return _decorator


class A(object):
    pass


class B(object):
    pass


class FrameLocalsDecoratorClass(object):
    @dispatch(A)
    def run(self, value):
        return "A"

    @dispatch(B)
    def run(self, value):
        return "B"


print(
    "Class frame locals decorators",
    [types[0].__name__ for types in FrameLocalsDecoratorClass.run.types],
)

print("Class with decorator and meta class:")


def class_decorator(cls):
    try:
        print("cls decorator", cls.added_in)
    except AttributeError:
        print("cls decorator has not added")

    return cls


@class_decorator
class MyClass:
    __metaclass__ = MetaClass


print("Class that updates its locals:")


class DictUpdating:
    a = 1

    locals().update({"b": 2})

    for f in range(6):
        locals()["test_%s" % f] = f


print("Changed values", DictUpdating.b, DictUpdating.test_4)


def makeConditionalClass(condition):
    if condition:

        class ConditionalClass:
            a = 1
            class_locals = locals()

        return ConditionalClass


conditional_class = makeConditionalClass(True)
print("Class in conditional with locals:", conditional_class.a)


def functionThatOffersClosureToPassThroughClass(x):
    class Foo:
        global x
        x = 1

        def __call__(self, y):
            return x + y

    return Foo()


print(functionThatOffersClosureToPassThroughClass(6)(2), x)


class NameCollisionClosure:
    def x(self):
        return x


print(NameCollisionClosure, NameCollisionClosure().x())


class ClassesWithNestedClass:
    class NestedClass(object):
        def getDict(self):
            return {"a": 2}


print(
    "Classes:",
    ClassesWithNestedClass,
    ClassesWithNestedClass().NestedClass,
    ClassesWithNestedClass().NestedClass().getDict(),
)

secondary = "global closure wins"


class ClassWithModuleVariableCollisionMain:
    secondary = None

    def __init__(self):
        self.secondary = self.Child()
        self.value = self.secondary.attr

    class Child:
        def __init__(self):
            self.attr = secondary


print(
    ClassWithModuleVariableCollisionMain, ClassWithModuleVariableCollisionMain().value
)

# See #4166.
print("Class body reads a function local assigned later:")

shared_name = 30


def classBodyThenLocalAssignment(use_class):
    if use_class:

        class C:
            shared_name = 5
            derived_name = shared_name * 2

        return C

    shared_name = 5

    return {"shared_name": shared_name, "derived_name": shared_name * 2}


print(classBodyThenLocalAssignment(False))
print("module shared_name:", shared_name)


def classBodyReadsLaterLocal():
    class C:
        x = 1
        y = x

    x = 2

    return C.y, x


print(classBodyReadsLaterLocal())


def recursiveFunctionUsesLocal():
    def recurse(n):
        if n < 0:

            class C:
                x = 1
                y = x

        x = n

        if n:
            recurse(n - 1)

        return x

    return recurse(2)


print("recursion result:", recursiveFunctionUsesLocal())

later_local = 100


def classBodyReadsUnboundLocal():
    class C:
        y = later_local

    later_local = 2

    return C.y


try:
    print(classBodyReadsUnboundLocal())
except NameError:
    print("NameError expected")

print("module later_local:", later_local)

shadowed_name = 100


def classBodyBindsAndReadsName():
    class C:
        y = shadowed_name
        shadowed_name = 2

    shadowed_name = 3

    return C.y, C.shadowed_name, shadowed_name


print(classBodyBindsAndReadsName())
print("module shadowed_name:", shadowed_name)

iterable_name = (100,)


def classBodyComprehensionIterable():
    class C:
        values = [i for i in iterable_name]

    iterable_name = (2, 3)

    return C.values


try:
    print(classBodyComprehensionIterable())
except NameError:
    print("NameError expected")

print("module iterable_name:", iterable_name)


def forTargetBindsLocal():
    class C:
        x = 1
        y = x

    for x in (2,):
        pass

    return C.y, x


print(forTargetBindsLocal())

exception_target = "module value"


def exceptTargetBindsLocal():
    class C:
        exception_target = 1
        y = exception_target

    try:
        1 / 0
    except ZeroDivisionError as exception_target:
        pass

    return C.y


print(exceptTargetBindsLocal())
print("module exception_target:", exception_target)


class MethodWithClassBody:
    def method(self):
        class C:
            x = 1
            y = x

        x = 3

        return C.y, x


print(MethodWithClassBody().method())


def classBodyInGenerator():
    class C:
        x = 1
        y = x

    x = 4

    yield C.y, x


print(list(classBodyInGenerator()))

print("Instances with managed dictionaries:")


class ManagedDictClass:
    class_attribute = "class"

    def method(self, value):
        return "method", value

    @property
    def prop(self):
        return "prop"


managed = ManagedDictClass()
managed.alpha = 1
managed.beta = 2

print("attribute:", managed.alpha, managed.beta)
print("dict:", sorted(managed.__dict__))
print("class:", managed.__class__.__name__)
print("hasattr:", hasattr(managed, "alpha"), hasattr(managed, "missing"))
print("getattr:", getattr(managed, "missing", "default"))

managed.method = lambda value: ("instance-method", value)
print("method:", managed.method(3))
del managed.method
print("method class:", managed.method(4))

managed.__dict__["prop"] = "shadowed"
print("property:", managed.prop)

try:
    managed.missing
except AttributeError as e:
    if sys.version_info >= (3, 10):
        print("error context:", e.name, e.obj is managed)
    else:
        print("error context: missing")


print("Instances with managed dictionaries converted to a real dict:")


class ManyAttributes:
    def method(self, value):
        return "many-method", value


many = ManyAttributes()

for i in range(50):
    setattr(many, "attr%d" % i, i)

many.direct = 99

print("attribute:", many.attr0, many.attr49, many.direct)
print("hasattr:", hasattr(many, "attr25"), hasattr(many, "missing"))
print("class:", many.__class__.__name__)
print("dict:", len(many.__dict__))

many.method = lambda value: ("many-instance-method", value)
print("method:", many.method(5))
del many.method
print("method class:", many.method(6))

del many.attr0
print("deleted:", hasattr(many, "attr0"))


print("Slots only and slots with dictionary:")


class SlotsOnly:
    __slots__ = ("slot",)


slots_only = SlotsOnly()
slots_only.slot = 1
print("slots only:", slots_only.slot, hasattr(slots_only, "missing"))

try:
    slots_only.missing = 2
except AttributeError:
    print("slots only set: AttributeError")


class SlotsWithDict:
    __slots__ = ("slot", "__dict__")


slots_with_dict = SlotsWithDict()
slots_with_dict.slot = 1
slots_with_dict.extra = 2
print(
    "slots dict:",
    slots_with_dict.slot,
    slots_with_dict.extra,
    sorted(slots_with_dict.__dict__),
)


class ClassBodyDeletion:
    __iop__ = "iop"
    __iadd__ = __iop__
    del __iop__

    def method(self):
        return 1


print(
    "Class body deletion:",
    ClassBodyDeletion.__iadd__,
    "__iop__" in ClassBodyDeletion.__dict__,
    ClassBodyDeletion().method(),
)


print("Attribute assignment KeyError handling:")


class BadAttrKey(str):
    def __hash__(self):
        return hash("x")

    def __eq__(self, other):
        raise KeyError("boom")


class NonDataDescr(object):
    def __get__(self, instance, owner=None):
        return 42


class CustomDataDescr(object):
    def __get__(self, instance, owner=None):
        return 1

    def __set__(self, instance, value):
        raise KeyError("from_descr_set")


class DescriptorKeyErrorHolder(object):
    @property
    def prop(self):
        return 1

    @prop.setter
    def prop(self, value):
        raise KeyError("from_property_setter")

    data_descr = CustomDataDescr()


class ManagedKeyErrorObj(object):
    x = NonDataDescr()


class DictSubclassKeyErrorObj(dict):
    x = NonDataDescr()


def reportAttributeException(label, func, target):
    try:
        func()
    except Exception as e:
        print(
            label,
            type(e).__name__,
            e.args,
            getattr(e, "name", None),
            getattr(e, "obj", None) is target,
        )
    else:
        print(label, "no exception")


descr_holder = DescriptorKeyErrorHolder()


def assignProperty():
    descr_holder.prop = 2


def assignDataDescriptor():
    descr_holder.data_descr = 2


reportAttributeException(
    "property setattr:", lambda: setattr(descr_holder, "prop", 2), descr_holder
)
reportAttributeException("property direct:", assignProperty, descr_holder)
reportAttributeException("data descr direct:", assignDataDescriptor, descr_holder)

managed_key_error_obj = ManagedKeyErrorObj()
managed_key_error_obj.__dict__[BadAttrKey("x")] = 1


def assignManagedDict():
    managed_key_error_obj.x = 2


reportAttributeException("managed dict set:", assignManagedDict, managed_key_error_obj)

dict_subclass_key_error_obj = DictSubclassKeyErrorObj()
dict_subclass_key_error_obj.__dict__[BadAttrKey("x")] = 1


def assignGenericDict():
    dict_subclass_key_error_obj.x = 2


reportAttributeException(
    "generic dict set:", assignGenericDict, dict_subclass_key_error_obj
)

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
