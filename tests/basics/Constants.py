#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Playing around with constants only. """

for value in (0, 0L, 3L, -4L, 17, "hey", (0, ),(0L, ), 0.0, -0.0 ):
   print value, repr(value)

print 1 == 0

print repr(0L), repr(0L) == "0L"

print {} is {}

a = ( {}, [] )

a[0][1] = 2
a[1].append( 3 )

print a

print ( {}, [] )

def argChanger(a):
   a[0][1] = 2
   a[1].append( 3 )

   return a

print argChanger( ( {}, [] ) )

print ( {}, [] )

print set(['foo'])


def mutableConstantChanger():
    a = ( [ 1, 2 ], [ 3 ] )
    print a

    a[ 1 ].append( 5 )
    print a

    d = { "l": [], "m" : [] }
    d["l"].append( 7 )
    print d

    declspec = None
    spec = dict(qual=[], storage=set(), type=[], function=set(), q = 1)
    spec[ "type" ].insert( 0, 2 )
    spec[ "storage" ].add(3)
    print sorted( spec )

mutableConstantChanger()
mutableConstantChanger()

def defaultKeepsIdentity(arg = "str_value"):
   print arg is "str_value"

defaultKeepsIdentity()


# Dictionary creation from call args
def dd(**d):
    return d
def f():
    def one():
        print "one"

    def two():
        print "two"

    a = dd(qual=one(), storage=two(), type=[], function=[])
    print "f mutable", a
    a = dd(qual=1, storage=2, type=3, function=4)
    print "f immutable", a

    # TODO: This exposes a bug in how the star dict argument should populate the
    # dictionary first instead of last, and the called arguments might have to
    # come from pairs so hashing does not reorder.
    # x = { "p" : 7 }
    # a = dd(qual=[], storage=[], type=[], function=[],**x)
    # print "f ext mutable", a
    # x = { "p" : 8 }
    # a = dd(qual=1, storage=2, type=3, function=4,**x)
    # print "f ext immutable", a
f()

# Dictionary creation one after another
x={}
x["function"] = []
x["type"] = []
x["storage"] = []
x["qual"] = []
print "m", x
x={}
x["function"] = 1
x["type"] = 2
x["storage"] = 3
x["qual"] = 4
print "m", x

# Constants in the code must be created differently.
d = { "qual" :  [], "storage" : [], "type2" : [], "function" : [] }
print "c", d
d = { "qual" :  1, "storage" : 2, "type2" : 3, "function" : 4 }
print "c", d

# Constants that might be difficult
min_signed_int = int( -(2**(8*8-1)-1)-1 )
print "small int", min_signed_int, type(min_signed_int)
min_signed_int = int( -(2**(8*4-1)-1)-1 )
print "small int", min_signed_int, type(min_signed_int)

# Constants that might be difficult
min_signed_long = long( -(2**(8*8-1)-1)-1 )
print "small long", min_signed_long, type(min_signed_long)
min_signed_long = long( -(2**(8*4-1)-1)-1 )
print "small long", min_signed_long, type(min_signed_long)
