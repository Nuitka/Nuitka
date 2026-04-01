"""Generic annotations tests, cover most important forms of them."""

# Tests are dirty on purpose.
#
# pylint: disable=not-an-iterable,unused-argument

from typing import Tuple, TypeVar, TypeVarTuple

T = TypeVar("T")
Ts = TypeVarTuple("Ts")

print("Module level T=", T)
print("Module level Ts=", Ts)
print()


print("[Part: 1] Unpacking a TypeVar tuple with star list arguments gives:")


def func1(*args: *Ts) -> None:
    print("Function level Ts=", Ts)
    print("Function level *Ts=", *Ts)


func1()
print(func1.__annotations__, "\n")


print("[Part: 2] Manually defining a Tuple[int,...] gives:")


def func21(*args: *Tuple[int, ...]) -> None:
    pass


func21()
print("Annotations", func21.__annotations__, "\n")


def func22(*args: *tuple[int, ...]) -> None:
    pass


func22()
print("Annotations", func22.__annotations__, "\n")


print("[Part: 3] Unpacking a TypeVar tuple with star list arguments gives:")


def func31(*args: Tuple[*Ts]) -> Tuple[*Ts]:
    print("Function level Ts=", Ts)
    print("Function level *Ts=", *Ts)


func31()
print("Annotations", func31.__annotations__, "\n")


def func32(*args: tuple[*Ts]) -> tuple[*Ts]:
    print("Function level Ts=", Ts)
    print("Function level *Ts=", *Ts)


func32()
print("Annotations", func32.__annotations__, "\n")


print("[Part: 4] Unpacking a TypeVar with star list arguments should raise an error:")
try:

    def func4(*args: *T) -> T:
        print(T)
        print(*T)

    func4()
    print("Annotations", func4.__annotations__, "\n")
except TypeError as e:
    print("Expected error:", e, "\n")
