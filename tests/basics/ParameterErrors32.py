#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

def kwfunc(a, *, k):
    pass

print( "Call function with mixed arguments with too wrong keyword argument." )

try:
    kwfunc( k = 3, b = 5 )
except TypeError as e:
    print( repr(e) )

print( "Call function with mixed arguments with too little positional arguments." )

try:
    kwfunc( k = 3 )
except TypeError as e:
    print( repr(e) )


print( "Call function with mixed arguments with too little positional arguments." )

try:
    kwfunc( 3 )
except TypeError as e:
    print( repr(e) )

print( "Call function with mixed arguments with too many positional arguments." )

try:
    kwfunc( 1,2,k=3 )
except TypeError as e:
    print( repr(e) )

def kwfuncdefaulted(a, b = None, *, c = None):
    pass

print( "Call function with mixed arguments and defaults but too many positional arguments." )

try:
    kwfuncdefaulted(1, 2, 3)
except TypeError as e:
    print( repr(e) )

def kwfunc2(a, *, k, l, m):
    pass

print( "Call function with mixed arguments with too little positional and keyword-only arguments." )

try:
    kwfunc2( 1, l = 2 )
except TypeError as e:
    print( repr(e) )

try:
    kwfunc2( 1 )
except TypeError as e:
    print( repr(e) )
