# -*- coding: utf-8 -*-
#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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


def plain_list_dict_args_function(plain, *arg_list, **arg_dict):
    print("plain", plain, "arg_list", arg_list, "arg_dict", arg_dict)


def plain_list_args_function(plain, *arg_list):
    print(plain, arg_list)


def plain_dict_args_function(plain, **arg_dict):
    print(plain, arg_dict)


print("Function with plain arg and varargs dict:")
plain_dict_args_function(1, a=2, b=3, c=4)
plain_dict_args_function(1)

print("Function with plain arg and varargs list:")
plain_list_args_function(1, 2, 3, 4)
plain_list_args_function(1)

print("Function with plain arg, varargs list and varargs dict:")
plain_list_dict_args_function(1, 2, z=3)
plain_list_dict_args_function(1, 2, 3)
plain_list_dict_args_function(1, a=2, b=3, c=4)


def list_dict_args_function(*arg_list, **arg_dict):
    print(arg_list, arg_dict)


def list_args_function(*arg_list):
    print(arg_list)


def dict_args_function(**arg_dict):
    print(arg_dict)


print("Function with plain arg and varargs dict:")
dict_args_function(a=2, b=3, c=4)
dict_args_function()

print("Function with plain arg and varargs list:")
list_args_function(2, 3, 4)
list_args_function()

print("Function with plain arg, varargs list and varargs dict:")
list_dict_args_function(2, z=3)
list_dict_args_function(2, 3)
list_dict_args_function(a=2, b=3, c=4)
