import NuitkaListModule
import timeit

result = NuitkaListModule.list2()

print("the sum of elements in the list" + result)
print(timeit.timeit()*1000 + " ms")
