class Parent[T]:
    value: T
    print(T)


class Child[T](Parent[T]):
    another_value: int
    print(T)


try:
    print(T)
except NameError:
    print("!!!")
