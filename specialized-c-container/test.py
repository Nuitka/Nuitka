import myModule
import timeit

result = myModule.list1()

print("the sum of the list " + result)
print(timeit.timeit()*1000 + " ms")
