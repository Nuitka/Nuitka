#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
from __future__ import print_function

var_on_module_level = 1

def closureTest1(some_arg):
    x = 3

    def enclosed(f = "default_value"):
        return x

    return enclosed

print("Call closured function returning function:", closureTest1(some_arg = "ignored")())

def closureTest2(some_arg):
    def enclosed(f = "default_value"):
        return x

    x = 4

    return enclosed

print("Call closured function returning function:", closureTest2(some_arg = "ignored")())


def defaultValueTest1(no_default, some_default_constant = 1):
    return some_default_constant

print("Call function with 2 parameters, one defaulted, and check that the default value is used:", defaultValueTest1("ignored"))

def defaultValueTest1a(no_default, some_default_constant_1 = 1, some_default_constant_2 = 2):
    return some_default_constant_2 - some_default_constant_1

print("Call function with 3 parameters, 2 defaulted, check they are used correctly:", defaultValueTest1a("ignored"))

def defaultValueTest2(no_default, some_default_variable = var_on_module_level*2):
    return some_default_variable

print("Call function with 2 parameters, 1 defaulted with an expression, check its result", defaultValueTest2("ignored"))

var_on_module_level = 2
print("Call function with 2 parameters, 1 defaulted with an expression, values have changed since, check its result", defaultValueTest2("ignored"))

def contractionTest():
    j = 2

    return [ j + i for i in range(8) ]

print("Call function that returns a list contraction:", contractionTest())

def defaultValueTest3a(no_default, funced_defaulted = defaultValueTest2(var_on_module_level)):
    return [ i + funced_defaulted for i in range(8) ]

print("Call function that has a default value coming from a function call:", defaultValueTest3a("ignored"))

def defaultValueTest3b(no_default, funced_defaulted = defaultValueTest2(var_on_module_level)):
    local_var = [ funced_defaulted + i for i in range(8) ]

    return local_var

print("Call function that returns a list contraction result via a local variable:", defaultValueTest3b("ignored"))

def defaultValueTest3c(no_default, funced_defaulted = defaultValueTest2(var_on_module_level)):
    local_var = [ [ j+funced_defaulted+1 for j in range(i) ] for i in range(8) ]

    return local_var

print("Call function that returns a nested list contraction with input from default parameter", defaultValueTest3c("ignored"))

def defaultValueTest4(no_default, funced_defaulted = lambda x: x**2):
    return funced_defaulted(4)

print("Call function that returns value calculated by a lambda function as default parameter", defaultValueTest4("ignored"))

def defaultValueTest4a(no_default, funced_defaulted = lambda x: x**2):
    c = 1
    d = funced_defaulted(1)

    r = ( i+j+c+d for i, j in zip(range(8), range(9)) )

    l = []
    for x in r:
        l.append(x)

    return l

print("Call function that has a lambda calculated default parameter and a generator expression", defaultValueTest4a("ignored"))

def defaultValueTest4b(no_default, funced_defaulted = lambda x: x**3):
    d = funced_defaulted(1)

    # Nested generators
    l = []

    for x in ( (d+j for j in range(4)) for i in range(8) ):
        for y in x:
            l.append(y)

    return l

print("Call function that has a lambda calculated default parameter and a nested generator expression", defaultValueTest4b("ignored"))

def defaultValueTest5(no_default, tuple_defaulted = (1,2,3)):
    return tuple_defaulted

print("Call function with default value that is a tuple", defaultValueTest5("ignored"))

def defaultValueTest6(no_default, list_defaulted = [1,2,3]):
    return list_defaulted

print("Call function with default value that is a list", defaultValueTest6("ignored"))

def lookup(unused, something):
    something.very.namelookup.chaining()
    something.very.namelookup.chaining()


x = len("hey")

def in_test(a):
    # if 7 in a:
    #   print "hey"

    8 in a  # @NoEffect
    9 not in a  # @NoEffect

def printing():
    print("Hallo")
    print("du")
    print("da")

def my_deco(function):
    def new_function(c, d):
        return function(d, c)

    return new_function

@my_deco
def decoriert(a,b):
    def subby(a):
        return 2 + a

    return 1+subby(b)

print("Function with decoration", decoriert(3, 9))

#def var_test(a):
#   b = len(a)
#   c = len(a)

def user():
    global a

    return a

a = "oh common"

some_constant_tuple = (2,5,7)
some_semiconstant_tuple = (2,5,a)

f = a * 2

print(defaultValueTest1("ignored"))

# The change of the default variable doesn't influence the default
# parameter of defaultValueTest2, that means it's also calculated
# at the time the function is defined.
module_level = 7
print(defaultValueTest2("also ignored"))

def starArgTest(a, b, c):
    return a, b, c

print("Function called with star arg from tuple:")

star_list_arg = (11, 44, 77)
print(starArgTest(*star_list_arg))

print("Function called with star arg from list:")

star_list_arg = [7, 8, 9]
print(starArgTest(*star_list_arg))

star_dict_arg = {
    'a' : 9, 'b' : 3, 'c': 8
}

print("Function called with star arg from dict")

print(starArgTest(**star_dict_arg))

lambda_func = lambda a, b : a < b
lambda_args = (8, 9)

print("Lambda function called with star args from tuple:")
print(lambda_func(*lambda_args))

print("Lambda function called with star args from list:")
lambda_args = [8, 7]
print(lambda_func(*lambda_args))


print("Generator function without context:")
def generator_without_context_function():
    gen = ( x for x in range(9) )

    return tuple(gen)

print(generator_without_context_function())

print("Generator function with 2 iterateds:")

def generator_with_2_fors():
    return tuple( (x, y) for x in range(2) for y in range(3) )

print(generator_with_2_fors())

def someYielder():
    yield 1
    yield 2

def someYieldFunctionUser():
    print("someYielder", someYielder())

    result = []

    for a in someYielder():
        result.append(a)

    return result

print("Function that uses some yielding function coroutine:")
print(someYieldFunctionUser())

def someLoopYielder():
    for i in (0, 1, 2):
        yield i


def someLoopYieldFunctionUser():
    result = []

    for a in someLoopYielder():
        result.append(a)

    return result

print("Function that uses some yielding function coroutine that loops:")
print(someLoopYieldFunctionUser())

def someGeneratorClosureUser():
    def someGenerator():
        def userOfGeneratorLocalVar():
            return x+1

        x = 2

        yield userOfGeneratorLocalVar()
        yield 6

    gen = someGenerator()

    return [next(gen), next(gen) ]

print("Function generator that uses a local function accessing its local variables to yield:")
print(someGeneratorClosureUser())

def someClosureUsingGeneratorUser():
    offered = 7

    def someGenerator():
        yield offered

    return next(someGenerator())

print("Function generator that yield from its closure:")
print(someClosureUsingGeneratorUser())


print("Function call with both star args and named args:")
def someFunction(a, b, c, d):
    print(a, b, c, d)

someFunction(a = 1, b = 2, **{ 'c' : 3, 'd' : 4 })

print("Order of evaluation of function and args:")

def getFunction():
    print("getFunction", end = "")

    def x(y, u, a, k):
        return y, u, k, a

    return x

def getPlainArg1():
    print("getPlainArg1", end = "")
    return 9

def getPlainArg2():
    print("getPlainArg2", end = "")
    return 13

def getKeywordArg1():
    print("getKeywordArg1", end = "")
    return 'a'

def getKeywordArg2():
    print("getKeywordArg2", end = "")
    return 'b'

getFunction()(getPlainArg1(), getPlainArg2(), k = getKeywordArg1(), a = getKeywordArg2())
print()

def getListStarArg():
    print("getListStarArg", end = "")
    return [1]

def getDictStarArg():
    print("getDictStarArg", end = "")
    return { 'k' : 9 }

print("Same with star args:")

getFunction()(getPlainArg1(), a = getKeywordArg1(), *getListStarArg(), **getDictStarArg())
print()

print("Dictionary creation order:")

d = {
    getKeywordArg1() : getPlainArg1(),
    getKeywordArg2() : getPlainArg2()
}
print()

print("Throwing an exception to a generator function:")

def someGeneratorFunction():
    try:
        yield 1
        yield 2
    except:
        yield 3

    yield 4

gen1 = someGeneratorFunction()

print("Fresh Generator Function throwing gives", end = "")

try:
    print(gen1.throw(ValueError)),
except ValueError:
    print("exception indeed")

gen2 = someGeneratorFunction()

print("Used Generator Function throwing gives", end = "")
next(gen2)
print(gen2.throw(ValueError), "indeed")

gen3 = someGeneratorFunction()

print("Fresh Generator Function close gives", end = "")
print(gen3.close())

gen4 = someGeneratorFunction()

print("Used Generator Function that mis-catches close gives", end = "")
next(gen4)
try:
    print(gen4.close(), end = "")
except RuntimeError:
    print("runtime exception indeed")


gen5 = someGeneratorFunction()

print("Used Generator Function close gives", end = "")
next(gen5)
next(gen5)
next(gen5)

print(gen5.close(), end = "")

def receivingGenerator():
    while True:
        a = yield 4
        yield a

print("Generator function that receives", end = "")

gen6 = receivingGenerator()

print(next(gen6), end = "")
print(gen6.send(5), end = "")
print(gen6.send(6), end = "")
print(gen6.send(7), end = "")
print(gen6.send(8))

print("Generator function whose generator is copied", end = "")

def generatorFunction():
    yield 1
    yield 2

gen7 = generatorFunction()
next(gen7)

gen8 = iter(gen7)
print(next(gen8))

def doubleStarArgs(*a, **d):
    return a, d

try:
    from UserDict import UserDict
except ImportError:
    print("Using Python3, making own non-dict dict:")

    class UserDict(dict):
        pass

print("Function that has keyword argument matching the list star arg name", end = "")
print(doubleStarArgs(1, **UserDict(a = 2)))

def generatorFunctionUnusedArg(a):
    yield 1

generatorFunctionUnusedArg(3)

def closureHavingGenerator(arg):
    def gen(x = 1):
        yield arg

    return gen()

print("Function generator that has a closure and default argument", end = "")
print(list(closureHavingGenerator(3)))


def functionWithDualStarArgsAndKeywordsOnly(a1, a2, a3, a4, b):
    return a1, a2, a3, a4, b

l = [1, 2, 3]
d = {'b': 8}

print("Dual star args, but not positional call", functionWithDualStarArgsAndKeywordsOnly(a4 = 1, *l, **d))

def posDoubleStarArgsFunction(a, b, c, *l, **d):
    return a, b, c, l, d

l = [2]
d = { "other" : 7, 'c' : 3 }

print("Dual star args consuming function", posDoubleStarArgsFunction(1,  *l, **d))

import inspect, sys

for value in sorted(dir()):
    main_value = getattr(sys.modules[ "__main__" ], value)

    if inspect.isfunction(main_value):
        print(main_value, main_value.__code__.co_varnames[:main_value.__code__.co_argcount]) # inspect.getargs( main_value.func_code )

        # TODO: Make this work as well, currently disabled, because of nested arguments not
        # being compatible yet.
        # print main_value, main_value.func_code.co_varnames, inspect.getargspec( main_value )
        pass
