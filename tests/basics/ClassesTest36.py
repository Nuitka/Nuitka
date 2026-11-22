#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Covers Python 3.6+ class '__init_subclass__' support with 'super()'."""

import functools
import sys

print("Testing class __init_subclass__ with class decorator requiring __classcell__:")


def makeClassDecorator(cls):
    def __init__(self):
        cls.__self_init__(self)

    cls.__init__ = __init__
    return cls


class ClassWithInitSubclassSuperParent:
    def __init__(self):
        print("ClassWithInitSubclassSuper Parent Initialized")

    def __init_subclass__(cls, decorator):
        decorator(cls)()


class ClassWithInitSubclassSuperChild(
    ClassWithInitSubclassSuperParent,
    decorator=makeClassDecorator,
):
    def __self_init__(self):
        super().__init__()


def identityDecorator(func):
    func.marked = True
    return func


def wrappingDecorator(func):
    def wrapper(*args, **kwargs):
        return ("wrapped", func(*args, **kwargs))

    return wrapper


class CustomDescriptor(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, owner=None):
        def bound(*args, **kwargs):
            return ("descriptor", owner, args, kwargs)

        return bound


print("Testing __init_subclass__ decorator and async handling:")


class InitSubclassStatic:
    calls = []

    @staticmethod
    def __init_subclass__(tag="default"):
        InitSubclassStatic.calls.append(("static", tag))


class InitSubclassStaticChild(InitSubclassStatic, tag="ok"):
    pass


class InitSubclassExplicitClassmethod:
    calls = []

    @classmethod
    def __init_subclass__(cls, tag="default"):
        cls.calls.append(("explicit", cls.__name__, tag))


class InitSubclassExplicitClassmethodChild(InitSubclassExplicitClassmethod, tag="ok"):
    pass


class InitSubclassDescriptor:
    @CustomDescriptor
    def __init_subclass__(cls, **kwargs):
        pass


class InitSubclassDescriptorChild(InitSubclassDescriptor):
    pass


class InitSubclassIdentity:
    calls = []

    @identityDecorator
    def __init_subclass__(cls, tag="default"):
        cls.calls.append(("identity", cls.__name__, tag))


class InitSubclassIdentityChild(InitSubclassIdentity, tag="ok"):
    pass


class InitSubclassWrapped:
    calls = []

    @wrappingDecorator
    def __init_subclass__(cls, tag="default"):
        cls.calls.append(("wrapped", cls.__name__, tag))


class InitSubclassWrappedChild(InitSubclassWrapped, tag="ok"):
    pass


class InitSubclassAsync:
    async def __init_subclass__(cls, **kwargs):
        return cls


class InitSubclassAsyncStatic:
    @staticmethod
    async def __init_subclass__(**kwargs):
        return kwargs


class InitSubclassAsyncIdentity:
    @identityDecorator
    async def __init_subclass__(cls, **kwargs):
        return cls


print(
    "InitSubclassStatic:",
    type(InitSubclassStatic.__dict__["__init_subclass__"]),
    InitSubclassStatic.calls,
)
print(
    "InitSubclassExplicitClassmethod:",
    type(InitSubclassExplicitClassmethod.__dict__["__init_subclass__"]),
    InitSubclassExplicitClassmethod.calls,
)
print(
    "InitSubclassDescriptor:",
    type(InitSubclassDescriptor.__dict__["__init_subclass__"]),
)
print(
    "InitSubclassIdentity:",
    type(InitSubclassIdentity.__dict__["__init_subclass__"]),
    InitSubclassIdentity.__dict__["__init_subclass__"].__func__.marked,
    InitSubclassIdentity.calls,
)
print(
    "InitSubclassWrapped:",
    type(InitSubclassWrapped.__dict__["__init_subclass__"]),
    InitSubclassWrapped.calls,
)
print(
    "InitSubclassAsync:",
    type(InitSubclassAsync.__dict__["__init_subclass__"]),
)
print(
    "InitSubclassAsyncStatic:",
    type(InitSubclassAsyncStatic.__dict__["__init_subclass__"]),
)
print(
    "InitSubclassAsyncIdentity:",
    type(InitSubclassAsyncIdentity.__dict__["__init_subclass__"]),
    InitSubclassAsyncIdentity.__dict__["__init_subclass__"].__func__.marked,
)


if sys.version_info >= (3, 7):
    print("Testing __class_getitem__ decorator and async handling:")

    class ClassGetItemPlain:
        def __class_getitem__(cls, item):
            return ("plain", cls.__name__, item)

    class ClassGetItemStatic:
        @staticmethod
        def __class_getitem__(item):
            return ("static", item)

    class ClassGetItemExplicitClassmethod:
        @classmethod
        def __class_getitem__(cls, item):
            return ("explicit", cls.__name__, item)

    class ClassGetItemDescriptor:
        @CustomDescriptor
        def __class_getitem__(cls, item):
            return ("unused", cls, item)

    class ClassGetItemIdentity:
        @identityDecorator
        def __class_getitem__(cls, item):
            return ("identity", cls.__name__, item)

    class ClassGetItemWrapped:
        @wrappingDecorator
        def __class_getitem__(cls, item):
            return (cls.__name__, item)

    class ClassGetItemLruCache:
        @functools.lru_cache(maxsize=None)
        def __class_getitem__(item):
            return ("lru", item)

    class ClassGetItemAsync:
        async def __class_getitem__(cls, item):
            return ("async", cls.__name__, item)

    class ClassGetItemAsyncStatic:
        @staticmethod
        async def __class_getitem__(item):
            return ("async_static", item)

    class ClassGetItemAsyncIdentity:
        @identityDecorator
        async def __class_getitem__(cls, item):
            return ("async_identity", cls.__name__, item)

    print(
        "ClassGetItemPlain:",
        type(ClassGetItemPlain.__dict__["__class_getitem__"]),
        ClassGetItemPlain[int],
    )
    print(
        "ClassGetItemStatic:",
        type(ClassGetItemStatic.__dict__["__class_getitem__"]),
        ClassGetItemStatic[int],
    )
    print(
        "ClassGetItemExplicitClassmethod:",
        type(ClassGetItemExplicitClassmethod.__dict__["__class_getitem__"]),
        ClassGetItemExplicitClassmethod[int],
    )
    print(
        "ClassGetItemDescriptor:",
        type(ClassGetItemDescriptor.__dict__["__class_getitem__"]),
        ClassGetItemDescriptor[int],
    )
    print(
        "ClassGetItemIdentity:",
        type(ClassGetItemIdentity.__dict__["__class_getitem__"]),
        ClassGetItemIdentity.__dict__["__class_getitem__"].__func__.marked,
        ClassGetItemIdentity[int],
    )
    print(
        "ClassGetItemWrapped:",
        type(ClassGetItemWrapped.__dict__["__class_getitem__"]),
        ClassGetItemWrapped[int],
    )
    print(
        "ClassGetItemLruCache:",
        type(ClassGetItemLruCache.__dict__["__class_getitem__"]),
        ClassGetItemLruCache[int],
    )
    coro1 = ClassGetItemAsync[int]
    coro1.close()
    coro2 = ClassGetItemAsyncStatic[int]
    coro2.close()
    coro3 = ClassGetItemAsyncIdentity[int]
    coro3.close()
    print(
        "ClassGetItemAsync:",
        type(ClassGetItemAsync.__dict__["__class_getitem__"]),
    )
    print(
        "ClassGetItemAsyncStatic:",
        type(ClassGetItemAsyncStatic.__dict__["__class_getitem__"]),
    )
    print(
        "ClassGetItemAsyncIdentity:",
        type(ClassGetItemAsyncIdentity.__dict__["__class_getitem__"]),
        ClassGetItemAsyncIdentity.__dict__["__class_getitem__"].__func__.marked,
    )

    print("Testing __class_getitem__ error handling and edge cases:")

    class MetaClassGetItemRuntimeError(type):
        def __getattribute__(cls, name):
            if name == "__class_getitem__":
                raise RuntimeError("meta class_getitem error")
            return super().__getattribute__(name)

    class MetaClassGetItemAttributeError(type):
        def __getattribute__(cls, name):
            if name == "__class_getitem__":
                raise AttributeError("meta class_getitem missing")
            return super().__getattribute__(name)

    class DescrClassGetItemError:
        def __get__(self, instance, owner=None):
            raise RuntimeError("descriptor class_getitem error")

    class ClassGetItemMetaRuntimeError(metaclass=MetaClassGetItemRuntimeError):
        pass

    class ClassGetItemMetaAttributeError(metaclass=MetaClassGetItemAttributeError):
        pass

    class ClassGetItemDescrError:
        __class_getitem__ = DescrClassGetItemError()

    class ClassGetItemNone:
        __class_getitem__ = None

    class ClassGetItemNonCallable:
        __class_getitem__ = 42

    class ClassGetItemPlainMissing:
        pass

    class ClassGetItemKeyType:
        def __class_getitem__(cls, item):
            return (type(item).__name__, item)

    def reportClassSubscript(label, fn):
        try:
            res = fn()
        except Exception as e:
            print(label, "raised", type(e).__name__, str(e))
        else:
            print(label, "returned", res)

    reportClassSubscript("meta runtime [0]:", lambda: ClassGetItemMetaRuntimeError[0])
    reportClassSubscript(
        "meta runtime [int]:", lambda: ClassGetItemMetaRuntimeError[int]
    )
    reportClassSubscript("meta attr [0]:", lambda: ClassGetItemMetaAttributeError[0])
    reportClassSubscript(
        "meta attr [int]:", lambda: ClassGetItemMetaAttributeError[int]
    )
    reportClassSubscript("descr error [0]:", lambda: ClassGetItemDescrError[0])
    reportClassSubscript("descr error [int]:", lambda: ClassGetItemDescrError[int])
    reportClassSubscript("none [0]:", lambda: ClassGetItemNone[0])
    reportClassSubscript("none [int]:", lambda: ClassGetItemNone[int])
    reportClassSubscript("non-callable [0]:", lambda: ClassGetItemNonCallable[0])
    reportClassSubscript("non-callable [int]:", lambda: ClassGetItemNonCallable[int])
    reportClassSubscript("missing [0]:", lambda: ClassGetItemPlainMissing[0])
    reportClassSubscript("missing [int]:", lambda: ClassGetItemPlainMissing[int])
    reportClassSubscript("key type [0]:", lambda: ClassGetItemKeyType[0])
    reportClassSubscript("key type [True]:", lambda: ClassGetItemKeyType[True])

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
