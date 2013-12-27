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


import inspect, types, sys

def compiledFunction():
   pass

assert inspect.isfunction( compiledFunction ) is True
assert isinstance( compiledFunction, types.FunctionType )
assert isinstance( compiledFunction, ( int, types.FunctionType ) )

# Even this works.
assert type( compiledFunction ) == types.FunctionType

class compiledClass:
   def compiledMethod(self):
      pass

assert inspect.isfunction( compiledClass ) is False
assert isinstance( compiledClass, types.FunctionType ) is False

assert inspect.ismethod( compiledFunction ) is False
assert inspect.ismethod( compiledClass ) is False

assert inspect.ismethod( compiledClass.compiledMethod ) == ( sys.version_info < ( 3, ) )
assert inspect.ismethod( compiledClass().compiledMethod ) is True

assert bool( type( compiledClass.compiledMethod ) == types.MethodType ) == ( sys.version_info < ( 3, ) )

def compiledGenerator():
   yield 1

assert inspect.isfunction( compiledGenerator ) is True
assert inspect.isgeneratorfunction( compiledGenerator ) is True

assert isinstance( compiledGenerator(), types.GeneratorType ) is True
assert type( compiledGenerator() ) == types.GeneratorType
assert isinstance( compiledGenerator, types.GeneratorType ) is False

assert inspect.ismethod( compiledGenerator() ) is False
assert inspect.isfunction( compiledGenerator() ) is False

assert inspect.isgenerator( compiledFunction ) is False
assert inspect.isgenerator( compiledGenerator ) is False
assert inspect.isgenerator( compiledGenerator() ) is True

def someFunction():
   assert inspect.isframe( sys._getframe() )
   print inspect.getframeinfo( sys._getframe() )

someFunction()

import sys

class C:
    print "Class locals", str( sys._getframe().f_locals ).replace( ", '__locals__': {...}", "" ).replace( "'__qualname__': 'C', ", "" )
    print "Class flags", sys._getframe().f_code.co_flags | 64

def f():
    print "Func locals", sys._getframe().f_locals
    print "Func flags", sys._getframe().f_code.co_flags | 64

f()

def displayDict(d):
    d = dict(d)
    if "__loader__" in d:
        d[ "__loader__" ] = "<loader removed>"

    return repr( d )

print "Module frame locals", displayDict( sys._getframe().f_locals )
print "Module flags", sys._getframe().f_code.co_flags  | 64
