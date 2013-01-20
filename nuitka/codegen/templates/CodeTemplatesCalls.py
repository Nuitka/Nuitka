#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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
""" Call related templates.

"""

# Bad to read, but we wan't the helper name to say it all and the call on same line
# pylint: disable=C0301

template_call_star_dict = """\
CALL_FUNCTION_WITH_STAR_DICT( %(function)s, %(star_dict_arg)s )"""

template_call_star_list_star_dict = """\
CALL_FUNCTION_WITH_STAR_LIST_STAR_DICT( %(function)s, %(star_list_arg)s, %(star_dict_arg)s )"""

template_call_pos_star_dict = """\
CALL_FUNCTION_WITH_POSARGS_STAR_DICT( %(function)s, %(pos_args)s, %(star_dict_arg)s )"""

template_call_pos_star_list = """\
CALL_FUNCTION_WITH_POSARGS_STAR_LIST( %(function)s, %(pos_args)s, %(star_list_arg)s )"""

template_call_pos_star_list_star_dict = """\
CALL_FUNCTION_WITH_POSARGS_STAR_LIST_STAR_DICT( %(function)s, %(pos_args)s, %(star_list_arg)s, %(star_dict_arg)s )"""

template_call_pos_named_star_list = """\
CALL_FUNCTION_WITH_POSARGS_KEYARGS_STAR_LIST( %(function)s, %(pos_args)s, %(named_args)s, %(star_list_arg)s )"""

template_call_pos_named_star_dict = """\
CALL_FUNCTION_WITH_POSARGS_KEYARGS_STAR_DICT( %(function)s, %(pos_args)s, %(named_args)s, %(star_dict_arg)s )"""

template_call_pos_named_star_list_star_dict = """\
CALL_FUNCTION_WITH_POSARGS_KEYARGS_STAR_LIST_STAR_DICT( %(function)s, %(pos_args)s, %(named_args)s, %(star_list_arg)s, %(star_dict_arg)s )"""

template_call_named_star_list = """\
CALL_FUNCTION_WITH_KEYARGS_STAR_LIST( %(function)s, %(named_args)s, %(star_list_arg)s )"""

template_call_named_star_dict = """\
CALL_FUNCTION_WITH_KEYARGS_STAR_DICT( %(function)s, %(named_args)s, %(star_dict_arg)s )"""

template_call_named_star_list_star_dict = """\
CALL_FUNCTION_WITH_KEYARGS_STAR_LIST_STAR_DICT( %(function)s, %(named_args)s, %(star_list_arg)s, %(star_dict_arg)s )"""

template_reverse_macros_declaration = """\
#include "nuitka/eval_order.hpp"

#if NUITKA_REVERSED_ARGS == 0
%(noreverse_macros)s
#else
%(reverse_macros)s
#endif
"""
