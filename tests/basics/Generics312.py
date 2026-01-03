def has_generic[T]():
    print("hello", T)


has_generic()

try:
    print(T)
except NameError:
    print("not found")

T = 1


def overwrites_generic[T]():
    print(T)


overwrites_generic()
print(T)
