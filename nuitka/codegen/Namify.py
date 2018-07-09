#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Namify constants.
This determines the identifier names of constants in the generated code. We
try to have readable names where possible, and resort to hash codes only when
it is really necessary.

"""


import hashlib
import math
import re
from logging import warning
from types import BuiltinFunctionType

from nuitka.__past__ import (  # pylint: disable=I0021,redefined-builtin
    long,
    unicode,
    xrange
)
from nuitka.Builtins import builtin_anon_values, builtin_named_values_list


class ExceptionCannotNamify(Exception):
    pass

def namifyConstant(constant):
    # Many branches, statements and every case has a return, this is a huge case
    # statement, that encodes the naming policy of constants, with often complex
    # conditions, pylint: disable=too-many-branches,too-many-return-statements,too-many-statements

    if type(constant) is int:
        if constant == 0:
            result = "int_0"
        elif constant > 0:
            result = "int_pos_%d" % constant
        else:
            result = "int_neg_%d" % abs(constant)

        if len(result) > 32:
            result = _digest(result)

        return result
    elif type(constant) is long:
        if constant == 0:
            result = "long_0"
        elif constant > 0:
            result = "long_pos_%d" % constant
        else:
            result = "long_neg_%d" % abs(constant)

        if len(result) > 32:
            result = _digest(result)

        return result
    elif constant is None:
        return "none"
    elif constant is True:
        return "true"
    elif constant is False:
        return "false"
    elif constant is Ellipsis:
        return "ellipsis"
    elif type(constant) is str:
        return "str_" + _namifyString(constant)
    elif type(constant) is bytes:
        return "bytes_" + _namifyString(constant)
    elif type(constant) is unicode:
        if _isAscii(constant):
            return "unicode_" + _namifyString(str(constant))
        else:
            # Others are better digested to not cause compiler trouble
            return "unicode_digest_" + _digest(repr(constant))
    elif type(constant) is float:
        if math.isnan(constant):
            return "float_%s_nan" % (
                "minus" if math.copysign(1, constant) < 0 else "plus"
            )

        return "float_%s" % repr(constant).replace('.', '_').\
          replace('-', "_minus_").replace('+', "")
    elif type(constant) is complex:
        value = "%s__%s" % (constant.real, constant.imag)

        value = value.replace('+', 'p').replace('-', 'm').\
          replace('.', '_')

        if value.startswith('(') and value.endswith(')'):
            value = value[1:-1]

        return "complex_%s" % value
    elif type(constant) is dict:
        if constant == {}:
            return "dict_empty"
        else:
            return "dict_" + _digest(repr(constant))
    elif type(constant) is set:
        if constant == set():
            return "set_empty"
        else:
            return "set_" + _digest(repr(constant))
    elif type(constant) is frozenset:
        if constant == frozenset():
            return "frozenset_empty"
        else:
            return "frozenset_" + _digest(repr(constant))
    elif type(constant) is tuple:
        if constant == ():
            return "tuple_empty"
        else:
            try:
                result = '_'.join(
                    namifyConstant(value)
                    for value in
                    constant
                )

                if len(result) > 60:
                    result = _digest(repr(constant))

                return "tuple_" + result + "_tuple"
            except ExceptionCannotNamify:
                warning("Couldn't namify '%r'" % (constant,))

                return "tuple_" + _digest(repr(constant))
    elif type(constant) is list:
        if constant == []:
            return "list_empty"
        else:
            try:
                result = '_'.join(
                    namifyConstant(value)
                    for value in
                    constant
                )

                if len(result) > 60:
                    result = _digest(repr(constant))

                return "list_" + result + "_list"
            except ExceptionCannotNamify:
                warning("Couldn't namify '%r'" % value)

                return "list_" + _digest(repr(constant))
    elif type(constant) is bytearray:
        return "bytearray_" + _digest(repr(constant))
    elif type(constant) is xrange:
        return "xrange_%s" % (
            str(constant)[7 if str is bytes else 6:-1].replace(' ', "").replace(',', '_').replace('-', "neg")
        )
    elif type(constant) is slice:
        return "slice_%s_%s_%s" % (
            namifyConstant(constant.start),
            namifyConstant(constant.stop),
            namifyConstant(constant.step)
        )
    elif constant in builtin_anon_values:
        return "anon_%s" % builtin_anon_values[constant]
    elif type(constant) is type:
        return "type_%s" % constant.__name__
    elif type(constant) is BuiltinFunctionType:
        assert constant in builtin_named_values_list

        return "builtin_%s" % constant.__name__
    elif constant is NotImplemented:
        return "type_notimplemented"
    else:
        raise ExceptionCannotNamify("%r" % constant, type(constant))

_re_str_needs_no_digest = re.compile(r"^([a-z]|[A-Z]|[0-9]|_){1,40}$", re.S)

def _namifyString(string):
    # Many branches case has a return, encodes the naming policy of strings
    # constants, with often complex decisions to make, pylint: disable=too-many-return-statements

    if string in ("", b""):
        return "empty"
    elif string == ' ':
        return "space"
    elif string == '.':
        return "dot"
    elif string == '\n':
        return "newline"
    elif type(string) is str and \
         _re_str_needs_no_digest.match(string) and \
         '\n' not in string:
        # Some strings can be left intact for source code readability.
        return "plain_" + string
    elif len(string) == 1:
        return "chr_%d" % ord(string)
    elif len(string) > 2 and string[0] == '<' and string[-1] == '>' and \
         _re_str_needs_no_digest.match(string[1:-1]) and \
         '\n' not in string:
        return "angle_" + string[1:-1]
    else:
        # Others are better digested to not cause compiler trouble
        return "digest_" + _digest(repr(string))

def _isAscii(string):
    try:
        _unused = str(string)

        return True
    except UnicodeEncodeError:
        return False

def _digest(value):
    if str is bytes:
        # Python2 is simple
        return hashlib.md5(value).hexdigest()
    else:
        # Python3 needs to encode the string is it is one.
        if type(value) is bytes:
            return hashlib.md5(value).hexdigest()
        else:
            return hashlib.md5(value.encode("utf-8")).hexdigest()
