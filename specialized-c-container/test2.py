import NuitkaListModule
import timeit

result = NuitkaListModule.list2()
print(result)
print ("time of getting the sum using our NuitkaList implementation")
print(timeit.timeit()*1000 , " ms")
