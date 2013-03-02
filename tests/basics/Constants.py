#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

def argChanger( a ):
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

mutableConstantChanger()
mutableConstantChanger()

def defaultKeepsIdentity( arg = "str_value" ):
   print arg is "str_value"

defaultKeepsIdentity()
