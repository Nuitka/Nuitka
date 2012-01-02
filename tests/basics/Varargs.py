# -*- coding: utf-8 -*-
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
