#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


print("Basic assignment forms from various iterables:")
a, b = 1, 2  # simple sequence assignment
print(a, b)
a, b = ["green", "blue"]  # list assignment
print(a, b)
a, b = "XY"  # string assignment
print(a, b)
a, b = range(1, 5, 2)  # any iterable will do
print(a, b)

print("Using braces on unpacking side:")
(a, b), c = "XY", "Z"  # a = 'X', b = 'Y', c = 'Z'
print(a, b, c)

print("Too many values:")
try:
    (a, b), c = "XYZ"  # ERROR -- too many values to unpack
except Exception as e:
    print(repr(e))
print(a, b, c)

print("Too few values:")
try:
    (a, b), c = "XY"  # ERROR -- need more than 1 value to unpack
except Exception as e:
    print(repr(e))
print(a, b, c)

print("More complex right hand side, consisting of multiple values:")
(
    (a, b),
    c,
) = [
    1,
    2,
], "this"  # a = '1', b = '2', c = 'this'
print(a, b, c)

print("More complex right hand side, too many values:")
try:
    (a, b), (c,) = [1, 2], "this"  # ERROR -- too many values to unpack
except Exception as e:
    print(repr(e))
print(a, b, c)

print("Extended sequence * unpacking:")
a, *b = 1, 2, 3, 4, 5  # a = 1, b = [2,3,4,5]
print(a, b)
*a, b = 1, 2, 3, 4, 5  # a = [1,2,3,4], b = 5
print(a, b)
a, *b, c = 1, 2, 3, 4, 5  # a = 1, b = [2,3,4], c = 5
print(a, b)

a, *b = "X"  # a = 'X', b = []
print(a, b)
*a, b = "X"  # a = [], b = 'X'
print(a, b)
a, *b, c = "XY"  # a = 'X', b = [], c = 'Y'
print(a, b)
a, *b, c = "X...Y"  # a = 'X', b = ['.','.','.'], c = 'Y'
print(a, b, c)

a, b, *c = 1, 2, 3  # a = 1, b = 2, c = [3]
print(a, b, c)
a, b, c, *d = 1, 2, 3  # a = 1, b = 2, c = 3, d = []
print(a, b, c, d)

(a, b), c = [1, 2], "this"  # a = '1', b = '2', c = 'this'
print(a, b, c)
(a, b), *c = [1, 2], "this"  # a = '1', b = '2', c = ['this']
print(a, b, c)
(a, b), c, *d = [1, 2], "this"  # a = '1', b = '2', c = 'this', d = []
print(a, b, c, d)
(a, b), *c, d = [1, 2], "this"  # a = '1', b = '2', c = [], d = 'this'
print(a, b, c, d)

(a, b), (c, *d) = [1, 2], "this"  # a = '1', b = '2', c = 't', d = ['h', 'i', 's']
print(a, b, c, d)

(*a,) = (1, 2)  # a = [1,2]


print("Extended sequence * unpacking with non-iterable:")
try:
    (*a,) = 1  # ERROR -- 'int' object is not iterable
except Exception as e:
    print(repr(e))
print(a)

print("Extended sequence * unpacking with list:")
(*a,) = [1]  # a = [1]
print(a)

print("Extended sequence * unpacking with tuple:")
(*a,) = (1,)  # a = [1]
print(a)

print("Extended sequence * unpacking with fixed right side:")
*a, b = [1]  # a = [], b = 1
print(a, b)
*a, b = (1,)  # a = [], b = 1
print(a, b)

print("Unpacking too many values:")
try:
    (a, b), c = 1, 2, 3  # ERROR -- too many values to unpack
except Exception as e:
    print(repr(e))
print(a, b, c)
print("Unpacking with star argument changes error:")
try:
    (a, b), *c = 1, 2, 3  # ERROR - 'int' object is not iterable
except Exception as e:
    print(repr(e))
print(a, b, c)

print("Unpacking with star argument after tuple unpack:")
(a, b), *c = "XY", 2, 3  # a = 'X', b = 'Y', c = [2,3]
print(a, b, c)

print("Extended sequence unpacking, nested:")

try:
    (a, b), c = 1, 2, 3  # ERROR -- too many values to unpack
except Exception as e:
    print(repr(e))
print(a, b, c)
*(a, b), c = 1, 2, 3  # a = 1, b = 2, c = 3
print(a, b, c)

(*(a, b),) = 1, 2  # a = 1, b = 2
print(a, b)

(*(a, b),) = "XY"  # a = 'X', b = 'Y'
print(a, b)

try:
    (*(a, b),) = "this"  # ERROR -- too many values to unpack
except Exception as e:
    print(repr(e))
print(a, b)

(*(a, *b),) = "this"  # a = 't', b = ['h', 'i', 's']
print(a, b)

*(a, *b), c = "this"  # a = 't', b = ['h', 'i'], c = 's'
print(a, b, c)

(*(a, *b),) = 1, 2, 3, 3, 4, 5, 6, 7  # a = 1, b = [2, 3, 3, 4, 5, 6, 7]
print(a, b)

try:
    *(a, *b), (*c,) = 1, 2, 3, 3, 4, 5, 6, 7  # ERROR -- 'int' object is not iterable
except Exception as e:
    print(repr(e))
print("unchanged", a, b, c)

print("Unpacking with nested stars:")
*(a, *b), c = 1, 2, 3, 3, 4, 5, 6, 7  # a = 1, b = [2, 3, 3, 4, 5, 6], c = 7
print(a, b, c)

print("Unpacking with even more nested stars:")
*(a, *b), (*c,) = 1, 2, 3, 4, 5, "XY"  # a = 1, b = [2, 3, 4, 5], c = ['X', 'Y']
print(a, b, c)

*(a, *b), c, d = 1, 2, 3, 3, 4, 5, 6, 7  # a = 1, b = [2, 3, 3, 4, 5], c = 6, d = 7
print("starting", a, b, c, d)
try:
    *(a, *b), (c, d) = 1, 2, 3, 3, 4, 5, 6, 7  # ERROR -- 'int' object is not iterable
except Exception as e:
    print(repr(e))
print("unchanged", a, b, c, d)

try:
    *(a, *b), (*c, d) = 1, 2, 3, 3, 4, 5, 6, 7  # ERROR -- 'int' object is not iterable
except Exception as e:
    print(repr(e))
print(a, b, c, d)


try:
    *(a, b), c = "XY", 3  # ERROR -- need more than 1 value to unpack
except Exception as e:
    print(repr(e))
print("unchanged", a, b, c)

*(*a, b), c = "XY", 3  # a = [], b = 'XY', c = 3
print(a, b, c)
(a, b), c = "XY", 3  # a = 'X', b = 'Y', c = 3
print(a, b, c)

*(a, b), c = "XY", 3, 4  # a = 'XY', b = 3, c = 4
print(a, b, c)
*(*a, b), c = "XY", 3, 4  # a = ['XY'], b = 3, c = 4
print(a, b, c)
try:
    (a, b), c = "XY", 3, 4  # ERROR -- too many values to unpack
except Exception as e:
    print(repr(e))
print(a, b, c)

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
