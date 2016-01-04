#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

a = 3
b = 7
c = [7, 8]
d = 15

print '+', a + b
print '-', a - b
print '*', a * b
print '/', a / b
print "//", a // b
print '%', b % a
print "& (2)", a & b
print "| (2)", a | b
print "& (3)", a & b & d
print "| (3)", a | b | d
print "^ (2)", a ^ b
print "^ (3)", a ^ b ^ d
print "**", a ** b
print "<<", a << b
print ">>", b >> a
print "in", b in c
print "not in", b not in c
print '<', a < b
print '>', a > b
print "==", a == b
print "<=", a <= b
print ">=", a >= b
print "!=", a != b
print "is", a is b
print "is not", a is not b

print '~', ~ b
print '-', - b
print '+', + b

l =  {('a', 'c') : "a,c", 'b' : 2, 'c' : 3, 'd' : 4  }
l[ 'l', ] = '6'


print "Extended slicing:"
print "Should be a,c:", l[ 'a', 'c']

print "Short form of extended slicing:"

d = {}
# d[1] = 1
d[1,] = 2
d[1,2] = 3
d[1,2,3] = 4
L = list(d)
L.sort()
print L

s = "Some information"
ss = s[-1]

print "Constant subscript of string", ss

print "Repr"
print `L`, `ss`

print `0L`

print repr(L), repr(ss)
print repr(3L)

print "Slicing on a list:"
l = [1, 3, 5, 7, 11, 13, 17]

print l[None:None]

n = None
print l[n:n]
print l[3:n]
print l[n:3]

value = None
try:
    x = value[1]
except Exception as e:
    print "Indexing None gives", repr(e)
