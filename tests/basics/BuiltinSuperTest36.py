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
