#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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

def kwonlysimple( *, a ):
    return a

print( "Most simple case", kwonlysimple( a = 3 ) )

def kwonlysimpledefaulted( *, a = 5 ):
    return a

print( "Default simple case", kwonlysimpledefaulted() )


def default1():
    print( "Called", default1 )
    return 1

def default2():
    print( "Called", default2 )

    return 2


def default3():
    print( "Called", default3 )
    return 3

def default4():
    print( "Called", default4 )

    return 4




def kwonlyfunc( x, y = default1(), z = default2(), *, a, b = default3(), c = default4(), d ):
    print( x, y, z, a, b, c, d )

print( kwonlyfunc.__kwdefaults__ )

print( "Keyword only function" )
kwonlyfunc( 7, a = 8, d = 12 )
