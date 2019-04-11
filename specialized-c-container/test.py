import myModule
import timeit

result = myModule.list1()

print("time of getting the sum using python/c api implementation")
print(timeit.timeit()*1000 , " ms")
