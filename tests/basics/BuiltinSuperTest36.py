try:

    class Meta(type):
        def __new__(mcs, name, bases, namespace):
            cls = type.__new__(mcs, name, bases, namespace)
            cls.test()

    class WithClassRef(metaclass=Meta):
        def test():
            return __class__

except BaseException:
    raise
else:
    print("Success")


def makeClassDecorator(cls):
    def __init__(self):
        cls.__self_init__(self)

    cls.__init__ = __init__
    return cls


class Parent:
    def __init__(self):
        print("Initialized")

    def __init_subclass__(cls, *, decorator):
        decorator(cls)()


class Child(
    Parent,
    decorator=makeClassDecorator,
):
    def __self_init__(self):
        super().__init__()
