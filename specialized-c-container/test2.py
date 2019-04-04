import ctypes
import timeit

l = ctypes.CDLL('./list2.so')


result = l.list_sum()

print(result)
print(timeit.timeit()*100)
