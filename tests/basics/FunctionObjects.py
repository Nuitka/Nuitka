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
def func( arg1, arg2, arg3, **star ):
   """ Some documentation. """

   pass

print "Starting out: func, func_name:", func, func.func_name

print "Changing its name:"
func.func_name = "renamed"

print "With new name: func, func_name:", func, func.func_name

print "Documentation initially:",  func.__doc__

print "Changing its doc:"
func.__doc__ = "changed doc" + chr(0) + " with 0 character"

print "Documentation updated:",  repr( func.__doc__ )

print "Setting its dict"
func.my_value = "attached value"
print "Reading its dict", func.my_value

print "func_code", func.func_code, func.func_code.co_argcount
print dir( func.func_code )

def func2( arg1, arg2 = "default_arg2", arg3 = "default_arg3" ):
   pass

print "func_defaults", func2.__defaults__, func2.func_defaults
