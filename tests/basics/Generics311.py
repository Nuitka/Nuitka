"""Generic annotations tests, cover most important forms of them."""

# Tests are dirty on purpose.
#
# pylint: disable=not-an-iterable,unused-argument

from typing import Tuple, TypeVar, TypeVarTuple

T = TypeVar("T")
Ts = TypeVarTuple("Ts")

print("Module level T=", T)
print("Module level Ts=", Ts)

print("Unpacking a TypeVar tuple with star list arguments gives:")


def func1(*args: *Ts) -> None:
    print("Function level Ts=", Ts)
    print("Function level *Ts=", *Ts)


func1()
print(func1.__annotations__)

print("Manually defining a Tuple[int,...] gives:")


def func2(*args: *Tuple[int, ...]) -> None:
    pass


func2()
print("Annotations", func2.__annotations__)


print("Unpacking a TypeVar tuple with star list arguments gives:")


def func3(*args: Tuple[*Ts]) -> Tuple[*Ts]:
    print("Function level Ts=", Ts)
    print("Function level *Ts=", *Ts)


func3()
print("Annotations", func3.__annotations__)

print("Unpacking a TypeVar with star list arguments should raise an error:")
try:

    def func4(*args: *T) -> T:
        print(T)
        print(*T)

    func4()
    print("Annotations", func4.__annotations__)
except TypeError as e:
    print("Expected error:", e)
