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


import inspect

def compiledFunction():
   pass

assert inspect.isfunction( compiledFunction ) is True

class compiledClass:
   def compiledMethod( self ):
      pass

assert inspect.isfunction( compiledClass ) is False

assert inspect.ismethod( compiledFunction ) is False
assert inspect.ismethod( compiledClass ) is False
assert inspect.ismethod( compiledClass.compiledMethod ) is True
assert inspect.ismethod( compiledClass().compiledMethod ) is True

def compiledGenerator():
   yield 1

assert inspect.isfunction( compiledGenerator ) is True
assert inspect.isgeneratorfunction( compiledGenerator ) is True


assert inspect.ismethod( compiledGenerator() ) is False
assert inspect.isfunction( compiledGenerator() ) is False

assert inspect.isgenerator( compiledFunction ) is False
assert inspect.isgenerator( compiledGenerator ) is False
assert inspect.isgenerator( compiledGenerator() ) is True
