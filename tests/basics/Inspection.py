#
#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python test originally created or extracted from other peoples work. The
#     parts and resulting tests are too small to be protected and therefore
#     is in the public domain.
#
#     If you submit Kay Hayen patches to this in either form, you automatically
#     grant him a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. Obviously it
#     won't affect code that comes to him indirectly or code you don't submit to
#     him.
#
#     This is to reserve my ability to re-license the official code at any time,
#     to put it into public domain or under PSF.
#
#     Please leave the whole of this copyright notice intact.
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
