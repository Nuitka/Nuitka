# 
#     Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Python test that I originally created or extracted from other peoples
#     work. I put my parts of it in the public domain. It is at least Free
#     Software where it's copied from other people. In these cases, I will
#     indicate it.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the new code, or in the alternative
#     a BSD license to the new code, should your jurisdiction prevent this. This
#     is to reserve my ability to re-license the code at any time.
# 
# -*- coding: utf-8 -*-

def plain_list_dict_args_function( plain, *arg_list, **arg_dict ):
    print plain, arg_list, arg_dict

def plain_list_args_function( plain, *arg_list ):
    print plain, arg_list

def plain_dict_args_function( plain, **arg_dict ):
    print plain, arg_dict


print "Function with plain arg and varargs dict:"
plain_dict_args_function( 1, a = 2, b = 3, c = 4 )
plain_dict_args_function( 1 )

print "Function with plain arg and varargs list:"
plain_list_args_function( 1, 2, 3, 4 )
plain_list_args_function( 1 )

print "Function with plain arg, varargs list and varargs dict:"
plain_list_dict_args_function( 1, 2, z = 3 )
plain_list_dict_args_function( 1, 2, 3 )
plain_list_dict_args_function( 1, a = 2, b = 3, c = 4 )

def list_dict_args_function( *arg_list, **arg_dict ):
    print arg_list, arg_dict

def list_args_function( *arg_list ):
    print arg_list

def dict_args_function( **arg_dict ):
    print arg_dict

print "Function with plain arg and varargs dict:"
dict_args_function( a = 2, b = 3, c = 4 )
dict_args_function()

print "Function with plain arg and varargs list:"
list_args_function( 2, 3, 4 )
list_args_function()

print "Function with plain arg, varargs list and varargs dict:"
list_dict_args_function( 2, z = 3 )
list_dict_args_function( 2, 3 )
list_dict_args_function( a = 2, b = 3, c = 4 )
