import ctypes

print(ctypes.CDLL("msvproc.dll"))
print(ctypes.c_int(5))
