#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Call related templates.

"""

call_pos_star_dict = """\
CALL_FUNCTION_STAR_BOTH_ONLY( %(star_dict_arg)s, %(pos_args)s, %(function)s )"""

call_star_list_star_dict = """\
CALL_FUNCTION_STAR_BOTH_ONLY( %(star_dict_arg)s, %(star_list_arg)s, %(function)s )"""

call_pos_named_star_list = """\
CALL_FUNCTION_STAR_LIST( %(function)s, %(pos_args)s, %(named_args)s, %(star_list_arg)s )"""

call_pos_named_star_dict = """\
CALL_FUNCTION_STAR_DICT2( %(function)s, %(pos_args)s, %(named_args)s, %(star_dict_arg)s )"""

call_pos_star_list_star_dict = """\
CALL_FUNCTION_STAR_BOTH( %(function)s, %(pos_args)s, %(star_list_arg)s, %(star_dict_arg)s )"""

call_pos_named_list_star_star_dict = """
CALL_FUNCTION_STAR_BOTH2( %(function)s, %(pos_args)s, %(named_args)s, %(star_list_arg)s, %(star_dict_arg)s )"""

template_reverse_macros_declaration = """\
#include "nuitka/eval_order.hpp"

#if NUITKA_REVERSED_ARGS == 0
%(noreverse_macros)s
#else
%(reverse_macros)s
#endif
"""
