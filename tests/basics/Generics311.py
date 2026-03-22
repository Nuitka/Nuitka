from typing import Tuple, TypeVar, TypeVarTuple

T = TypeVar("T")
Ts = TypeVarTuple("Ts")


def func1(*args: *Ts) -> None:
    print(Ts)
    print(*Ts)


func1()
print(func1.__annotations__)


def func2(*args: *Tuple[int, ...]) -> None:
    print(Ts)
    print(*Ts)


func2()
print(func2.__annotations__)


def func3(*args: Tuple[*Ts]) -> Tuple[*Ts]:
    print(Ts)
    print(*Ts)


func3()
print(func3.__annotations__)


try:

    def func4(*args: *T) -> T:
        print(T)
        print(*T)

    func4()
    print(func4.__annotations__)
except TypeError as e:
    print(e)
