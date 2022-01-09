#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Common helper functions for specializing code."""

from nuitka.tools.quality.autoformat.Autoformat import (  # For import from here, pylint: disable=unused-import
    withFileOpenedAndAutoformatted,
)


def writeline(output, *args):
    if not args:
        output.write("\n")
    elif len(args) == 1:
        output.write(args[0] + "\n")
    else:
        assert False, args


# Python2 dict methods:
python2_dict_methods = (
    "clear",  # has full dict coverage
    "copy",  # has full dict coverage
    "fromkeys",
    "get",  # has full dict coverage
    "has_key",  # has full dict coverage
    "items",  # has full dict coverage
    "iteritems",  # has full dict coverage
    "iterkeys",  # has full dict coverage
    "itervalues",  # has full dict coverage
    "keys",  # has full dict coverage
    "pop",  # has full dict coverage
    "popitem",  # has full dict coverage
    "setdefault",  # has full dict coverage
    "update",  # has full dict coverage
    "values",  # has full dict coverage
    "viewitems",  # has full dict coverage
    "viewkeys",  # has full dict coverage
    "viewvalues",  # has full dict coverage
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

python2_str_methods = (
    "capitalize",  # has full str coverage
    "center",
    "count",
    "decode",
    "encode",
    "endswith",  # has full str coverage
    "expandtabs",
    "find",  # has full str coverage
    "format",
    "index",  # has full str coverage
    "isalnum",  # has full str coverage
    "isalpha",  # has full str coverage
    "isdigit",  # has full str coverage
    "islower",  # has full str coverage
    "isspace",  # has full str coverage
    "istitle",  # has full str coverage
    "isupper",  # has full str coverage
    "join",  # has full str coverage
    "ljust",
    "lower",  # has full str coverage
    "lstrip",  # has full str coverage
    "partition",  # has full str coverage
    "replace",
    "rfind",  # has full str coverage
    "rindex",  # has full str coverage
    "rjust",
    "rpartition",  # has full str coverage
    "rsplit",  # has full str coverage
    "rstrip",  # has full str coverage
    "split",  # has full str coverage
    "splitlines",
    "startswith",  # has full str coverage
    "strip",  # has full str coverage
    "swapcase",  # has full str coverage
    "title",  # has full str coverage
    "translate",
    "upper",  # has full str coverage
    "zfill",
)

python3_str_methods = (
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
                "list_args": "iterable",
                "kw_args": "pairs",
            }
        else:
            required = spec.getArgumentCount() - spec.getDefaultCount()

            arg_counts = tuple(range(required, spec.getArgumentCount() + 1))

            arg_names = spec.getArgumentNames()
            arg_name_mapping = {}
    else:
        arg_names = arg_name_mapping = arg_counts = None

    return present, arg_names, arg_name_mapping, arg_counts


def formatArgs(args, starting=True, finishing=True):
    result = []
    if args:
        if not starting:
            result.append(",")

        for arg in args:
            result.append(arg)

            if arg is not args[-1] or not finishing:
                result.append(",")

    return "".join(result)


def check():
    if str is bytes:
        for method_name in python2_str_methods:
            assert hasattr("", method_name), method_name
        for method_name in python2_unicode_methods:
            assert hasattr(u"", method_name), method_name
        for method_name in python2_dict_methods:
            assert hasattr({}, method_name), method_name
    else:
        for method_name in python3_str_methods:
            assert hasattr("", method_name), method_name
        for method_name in python3_dict_methods:
            assert hasattr({}, method_name), method_name


check()
