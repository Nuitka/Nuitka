#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Common helper functions for specializing code."""

from nuitka.Constants import the_empty_unicode
from nuitka.tools.quality.auto_format.AutoFormat import (  # For import from here, pylint: disable=unused-import
    withFileOpenedAndAutoFormatted,
)


def writeLine(output, *args):
    if not args:
        output.write("\n")
    elif len(args) == 1:
        output.write(args[0] + "\n")
    else:
        assert False, args


# Python2 dict methods:
python2_dict_methods = (  # we have full coverage for all methods
    "clear",
    "copy",
    "fromkeys",
    "get",
    "has_key",
    "items",
    "iteritems",
    "iterkeys",
    "itervalues",
    "keys",
    "pop",
    "popitem",
    "setdefault",
    "update",
    "values",
    "viewitems",
    "viewkeys",
    "viewvalues",
)

python3_dict_methods = (
    # see Python2 methods, these are only less
    "clear",
    "copy",
    "fromkeys",
    "get",
    "items",
    "keys",
    "pop",
    "popitem",
    "setdefault",
    "update",
    "values",
)

python2_str_methods = (  # we have full coverage for all methods
    "capitalize",
    "center",
    "count",
    "decode",
    "encode",
    "endswith",
    "expandtabs",
    "find",
    "format",
    "index",
    "isalnum",
    "isalpha",
    "isdigit",
    "islower",
    "isspace",
    "istitle",
    "isupper",
    "join",
    "ljust",
    "lower",
    "lstrip",
    "partition",
    "replace",
    "rfind",
    "rindex",
    "rjust",
    "rpartition",
    "rsplit",
    "rstrip",
    "split",
    "splitlines",
    "startswith",
    "strip",
    "swapcase",
    "title",
    "translate",
    "upper",
    "zfill",
)

python3_str_methods = (  # we have full coverage for all methods
    "capitalize",
    "casefold",
    "center",
    "count",
    "encode",
    "endswith",
    "expandtabs",
    "find",
    "format",
    "format_map",
    "index",
    "isalnum",
    "isalpha",
    "isascii",
    "isdecimal",
    "isdigit",
    "isidentifier",
    "islower",
    "isnumeric",
    "isprintable",
    "isspace",
    "istitle",
    "isupper",
    "join",
    "ljust",
    "lower",
    "lstrip",
    "maketrans",
    "partition",
    # TODO: Python3.9 or higher:
    # "removeprefix",
    # "removesuffix",
    "replace",
    "rfind",
    "rindex",
    "rjust",
    "rpartition",
    "rsplit",
    "rstrip",
    "split",
    "splitlines",
    "startswith",
    "strip",
    "swapcase",
    "title",
    "translate",
    "upper",
    "zfill",
)

python2_unicode_methods = (
    "capitalize",
    "center",
    "count",
    "decode",
    "encode",
    "endswith",
    "expandtabs",
    "find",
    "format",
    "index",
    "isalnum",
    "isalpha",
    "isdecimal",
    "isdigit",
    "islower",
    "isnumeric",
    "isspace",
    "istitle",
    "isupper",
    "join",
    "ljust",
    "lower",
    "lstrip",
    "partition",
    "replace",
    "rfind",
    "rindex",
    "rjust",
    "rpartition",
    "rsplit",
    "rstrip",
    "split",
    "splitlines",
    "startswith",
    "strip",
    "swapcase",
    "title",
    "translate",
    "upper",
    "zfill",
)

python3_bytes_methods = (
    "capitalize",
    "center",
    "count",
    "decode",
    "endswith",
    "expandtabs",
    "find",
    # static method
    # "fromhex",
    # TODO: Python3.5 or higher:
    # "hex",
    "index",
    "isalnum",
    "isalpha",
    "isdigit",
    "islower",
    "isspace",
    "istitle",
    "isupper",
    # TODO: Python3.7 or higher:
    # "ishex",
    # "isascii",
    "join",
    "ljust",
    "lower",
    "lstrip",
    # static method
    # "maketrans",
    "partition",
    # TODO: Python3.9 or higher:
    # "removeprefix",
    # "removesuffix",
    "replace",
    "rfind",
    "rindex",
    "rjust",
    "rpartition",
    "rsplit",
    "rstrip",
    "split",
    "splitlines",
    "startswith",
    "strip",
    "swapcase",
    "title",
    "translate",
    "upper",
    "zfill",
)

python2_list_methods = (
    "append",
    "count",
    "extend",
    "index",
    "insert",
    "pop",
    "remove",
    "reverse",
    "sort",
)

python3_list_methods = (
    "append",
    "clear",
    "copy",
    "count",
    "extend",
    "index",
    "insert",
    "pop",
    "remove",
    "reverse",
    "sort",
)

python2_type_methods = (
    # TODO: Totally incomplete
)

python3_type_methods = (
    # TODO: Totally incomplete
    "__prepare__",
)


def getMethodVariations(spec_module, shape_name, method_name, must_exist=False):
    spec_name = shape_name.split("_")[-1] + "_" + method_name + "_spec"
    spec = getattr(spec_module, spec_name, None)

    present = spec is not None

    if not present and must_exist:
        assert False, spec_name

    if present:
        if spec.isStarListSingleArg():
            required = 1

            arg_counts = tuple(range(required, required + 2))

            arg_names = (
                spec.getStarListArgumentName(),
                spec.getStarDictArgumentName(),
            )

            arg_name_mapping = {
                "list_args": spec.getStarListArgumentName(),
            }
        else:
            required = spec.getArgumentCount() - spec.getDefaultCount()

            arg_counts = tuple(range(required, spec.getArgumentCount() + 1))

            arg_names = spec.getParameterNames()
            arg_name_mapping = {}

        arg_tests = [
            (
                ""
                if arg_name
                in (spec.getStarListArgumentName(), spec.getStarDictArgumentName())
                else "is not None"
            )
            for arg_name in arg_names
        ]

        result_shape = spec.getTypeShape()

    else:
        arg_names = arg_name_mapping = arg_counts = arg_tests = result_shape = None

    return present, arg_names, arg_tests, arg_name_mapping, arg_counts, result_shape


def getSpecs(spec_module):
    for name in sorted(dir(spec_module)):
        if name.endswith("_spec"):
            yield name, getattr(spec_module, name)


def formatArgs(args, starting=True, finishing=True, quoted=False):
    result = []
    if args:
        if not starting:
            result.append(",")

        for arg in args:
            result.append('"%s"' % arg if quoted else arg)

            if arg is not args[-1] or not finishing:
                result.append(",")

    return "".join(result)


def check():
    if str is bytes:
        for method_name in python2_str_methods:
            assert hasattr("", method_name), method_name
        for method_name in python2_unicode_methods:
            assert hasattr(the_empty_unicode, method_name), method_name
        for method_name in python2_dict_methods:
            assert hasattr({}, method_name), method_name
    else:
        for method_name in python3_str_methods:
            assert hasattr("", method_name), method_name
        for method_name in python3_dict_methods:
            assert hasattr({}, method_name), method_name


check()

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
