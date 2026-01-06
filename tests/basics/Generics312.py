def someGenericFunction[T]():
    print("hello", T)


someGenericFunction()

# Verify the name didn't leak.
try:
    print(T)
except NameError:
    print("not found")

T = 1


def someGenericFunctionShadowingGlobal[T]():
    print(T)


someGenericFunctionShadowingGlobal()
print(T)
