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
""" Optimizations of built-ins to built-in calls.

"""
from __future__ import print_function

import math
import sys

from nuitka.__past__ import builtins
from nuitka.PythonVersions import python_version

from .ParameterSpecs import ParameterSpec, TooManyArguments, matchCall


class BuiltinParameterSpec(ParameterSpec):
    __slots__ = ("builtin",)

    def __init__(self, name, arg_names, default_count, list_star_arg = None,
                  dict_star_arg = None):
        ParameterSpec.__init__(
            self,
            ps_name          = name,
            ps_normal_args   = arg_names,
            ps_list_star_arg = list_star_arg,
            ps_dict_star_arg = dict_star_arg,
            ps_default_count = default_count,
            ps_kw_only_args  = ()
        )

        self.builtin = getattr(builtins, name)

        assert default_count <= len(arg_names)

    def __repr__(self):
        return "<BuiltinParameterSpec %s>" % self.name

    def getName(self):
        return self.name

    def isCompileTimeComputable(self, values):
        # By default, we make this dependent on the ability to compute the
        # arguments, which is of course a good start for most cases, so this
        # is for overloads, pylint: disable=no-self-use

        for value in values:
            if value is not None and not value.isCompileTimeConstant():
                return False

        return True

    def simulateCall(self, given_values):
        # Using star dict call for simulation and catch any exception as really
        # fatal, pylint: disable=broad-except,too-many-branches

        try:
            given_normal_args = given_values[:len(self.normal_args)]

            if self.list_star_arg:
                given_list_star_args = given_values[len(self.normal_args)]
            else:
                given_list_star_args = None

            if self.dict_star_arg:
                given_dict_star_args = given_values[ -1 ]
            else:
                given_dict_star_args = None

            arg_dict = {}

            for arg_name, given_value in zip(self.normal_args, given_normal_args):
                assert type(given_value) not in (tuple, list), \
                  ("do not like a tuple %s" % (given_value,))

                if given_value is not None:
                    arg_dict[ arg_name ] = given_value.getCompileTimeConstant()

            if given_dict_star_args:
                for given_dict_star_arg in reversed(given_dict_star_args):
                    arg_name = given_dict_star_arg.getKey().getCompileTimeConstant()
                    arg_value = given_dict_star_arg.getValue().getCompileTimeConstant()

                    arg_dict[arg_name] = arg_value

            arg_list = []

            for arg_name in self.normal_args[:self.getPositionalOnlyCount()]:
                if arg_name in arg_dict:
                    arg_list.append(arg_dict[arg_name])
                    del arg_dict[arg_name]

        except Exception as e:
            sys.exit("Fatal problem: %r" % e)


        if given_list_star_args:
            return self.builtin(
                *(arg_list + list(value.getCompileTimeConstant() for value in given_list_star_args)),
                **arg_dict
            )
        else:
            return self.builtin(
                *arg_list,
                **arg_dict
            )


class BuiltinParameterSpecNoKeywords(BuiltinParameterSpec):
    __slots__ = ()

    def allowsKeywords(self):
        return False

    def simulateCall(self, given_values):
        # Using star dict call for simulation and catch any exception as really fatal,
        # pylint: disable=broad-except

        try:
            if self.list_star_arg:
                given_list_star_arg = given_values[ len(self.normal_args) ]
            else:
                given_list_star_arg = None

            arg_list = []
            refuse_more = False

            for _arg_name, given_value in zip(self.normal_args, given_values):
                assert type(given_value) not in (tuple, list), ("do not like tuple %s" % (given_value,))

                if given_value is not None:
                    if not refuse_more:
                        arg_list.append(given_value.getCompileTimeConstant())
                    else:
                        assert False
                else:
                    refuse_more = True

            if given_list_star_arg is not None:
                arg_list += [ value.getCompileTimeConstant() for value in given_list_star_arg ]
        except Exception as e:
            print("Fatal error: ", end = ' ', file = sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(repr(e))

        return self.builtin(*arg_list)


class BuiltinParameterSpecExceptions(BuiltinParameterSpec):
    def __init__(self, exception_name):
        # TODO: Parameter default_count makes no sense for exceptions probably.
        BuiltinParameterSpec.__init__(
            self,
            name          = exception_name,
            arg_names     = (),
            default_count = 0,
            list_star_arg = "args"
        )

    def allowsKeywords(self):
        return False

    def getKeywordRefusalText(self):
        return "exceptions.%s does not take keyword arguments" % self.name

    def getCallableName(self):
        return "exceptions." + self.getName()


class BuiltinParameterSpecPosArgs(BuiltinParameterSpec):
    __slots__ = ("positional_only",)

    def __init__(self, name, arg_names, default_count, positional_only,
                 list_star_arg = None, dict_star_arg = None, ):
        BuiltinParameterSpec.__init__(
            self,
            name          = name,
            arg_names     = arg_names,
            default_count = default_count,
            list_star_arg = list_star_arg,
            dict_star_arg = dict_star_arg
        )

        # Kind of the point of this class.
        assert positional_only
        self.positional_only = positional_only

    def getPositionalOnlyCount(self):
        return self.positional_only


def makeBuiltinExceptionParameterSpec(exception_name):
    if exception_name == "ImportError" and python_version >= 300:
        # TODO: Create this beast, needs keyword only arguments to be supported,
        # currently user of this function must take care to not have them.
        pass

    return BuiltinParameterSpecExceptions(
        exception_name = exception_name
    )

if python_version < 370:
    builtin_int_spec = BuiltinParameterSpec("int", ('x', "base"), 2)
else:
    builtin_int_spec = BuiltinParameterSpecPosArgs("int", ('x', "base"), 2, 1)


# These builtins are only available for Python2
if python_version < 300:
    builtin_long_spec = BuiltinParameterSpec(
        "long",
        ('x', "base"),
        2
    )
    builtin_execfile_spec = BuiltinParameterSpecNoKeywords(
        "execfile",
        ("filename", "globals", "locals"),
        2
    )
    builtin_unicode_spec = BuiltinParameterSpec(
        "unicode",
        ("string", "encoding", "errors"),
        3
    )

builtin_xrange_spec = BuiltinParameterSpecNoKeywords(
    "xrange" if python_version < 300 else "range",
    ("start", "stop", "step"),
    2
)


if python_version < 370:
    builtin_bool_spec = BuiltinParameterSpec("bool", ('x',), 1)
else:
    builtin_bool_spec = BuiltinParameterSpecNoKeywords("bool", ('x',), 1)

if python_version < 370:
    builtin_float_spec = BuiltinParameterSpec("float", ('x',), 1)
else:
    builtin_float_spec = BuiltinParameterSpecNoKeywords("float", ('x',), 1)

builtin_complex_spec = BuiltinParameterSpec("complex", ("real", "imag"), 2)

# This built-in have variable parameters for Python2/3
if python_version < 300:
    builtin_str_spec = BuiltinParameterSpec("str", ("object",), 1)
else:
    builtin_str_spec = BuiltinParameterSpec("str", ("object", "encoding", "errors"), 3)

builtin_len_spec = BuiltinParameterSpecNoKeywords("len", ("object",), 0)
builtin_dict_spec = BuiltinParameterSpec("dict", (), 0, "list_args", "dict_args")
builtin_len_spec = BuiltinParameterSpecNoKeywords("len", ("object",), 0)

if python_version < 370:
    builtin_tuple_spec = BuiltinParameterSpec("tuple", ("sequence",), 1)
    builtin_list_spec = BuiltinParameterSpec("list", ("sequence",), 1)
else:
    builtin_tuple_spec = BuiltinParameterSpecNoKeywords("tuple", ("sequence",), 1)
    builtin_list_spec = BuiltinParameterSpecNoKeywords("list", ("sequence",), 1)

builtin_set_spec = BuiltinParameterSpecNoKeywords("set", ("iterable",), 1)
builtin_frozenset_spec = BuiltinParameterSpecNoKeywords("frozenset", ("iterable",), 1)

builtin_import_spec = BuiltinParameterSpec("__import__", ("name", "globals", "locals", "fromlist", "level"), 4)

if python_version < 300:
    builtin_open_spec = BuiltinParameterSpec("open", ("name", "mode", "buffering"), 3)
else:
    builtin_open_spec = BuiltinParameterSpec("open", ("name", "mode", "buffering",
                                                      "encoding", "errors", "newline",
                                                      "closefd", "opener"), 7)

builtin_chr_spec = BuiltinParameterSpecNoKeywords("chr", ('i',), 0)
builtin_ord_spec = BuiltinParameterSpecNoKeywords("ord", ('c',), 0)
builtin_bin_spec = BuiltinParameterSpecNoKeywords("bin", ("number",), 0)
builtin_oct_spec = BuiltinParameterSpecNoKeywords("oct", ("number",), 0)
builtin_hex_spec = BuiltinParameterSpecNoKeywords("hex", ("number",), 0)
builtin_id_spec = BuiltinParameterSpecNoKeywords("id", ("object",), 0)
builtin_repr_spec = BuiltinParameterSpecNoKeywords("repr", ("object",), 0)

builtin_dir_spec = BuiltinParameterSpecNoKeywords("dir", ("object",), 1)
builtin_vars_spec = BuiltinParameterSpecNoKeywords("vars", ("object",), 1)

builtin_locals_spec = BuiltinParameterSpecNoKeywords("locals", (), 0)
builtin_globals_spec = BuiltinParameterSpecNoKeywords("globals", (), 0)
builtin_eval_spec = BuiltinParameterSpecNoKeywords("eval", ("source", "globals", "locals"), 2)
if python_version < 300:
    builtin_compile_spec = BuiltinParameterSpec(
        "compile",
        ("source", "filename", "mode", "flags", "dont_inherit"),
        2
    )
else:
    builtin_compile_spec = BuiltinParameterSpec(
        "compile",
        ("source", "filename", "mode", "flags", "dont_inherit", "optimize"),
        3
    )
if python_version >= 300:
    builtin_exec_spec = BuiltinParameterSpecNoKeywords(
        "exec",
        ("source", "globals", "locals"),
        2
    )

# Note: Iter in fact names its first argument if the default applies
# "collection", fixed up in a wrapper.
builtin_iter_spec = BuiltinParameterSpecNoKeywords("iter", ("callable", "sentinel"), 1)
builtin_next_spec = BuiltinParameterSpecNoKeywords("next", ("iterator", "default"), 1)

# Note: type with 1 and type with 3 arguments are too different.
builtin_type1_spec = BuiltinParameterSpecNoKeywords("type", ("object",), 0)
builtin_type3_spec = BuiltinParameterSpecNoKeywords("type", ("name", "bases", "dict"), 0)

builtin_super_spec = BuiltinParameterSpecNoKeywords("super", ("type", "object"), 1 if python_version < 300 else 2)

builtin_hasattr_spec = BuiltinParameterSpecNoKeywords("hasattr", ("object", "name"), 0)
builtin_getattr_spec = BuiltinParameterSpecNoKeywords("getattr", ("object", "name", "default"), 1)
builtin_setattr_spec = BuiltinParameterSpecNoKeywords("setattr", ("object", "name", "value"), 0)

builtin_isinstance_spec = BuiltinParameterSpecNoKeywords("isinstance", ("instance", "classes"), 0)

class BuiltinBytearraySpec(BuiltinParameterSpecNoKeywords):
    def isCompileTimeComputable(self, values):
        # For bytearrays, we need to avoid the case of large bytearray
        # construction from an integer at compile time.

        result = BuiltinParameterSpecNoKeywords.isCompileTimeComputable(
            self,
            values = values
        )

        if result and len(values) == 1:
            index_value = values[0].getIndexValue()

            if index_value is None:
                return result

            return index_value < 256
        else:
            return result

builtin_bytearray_spec = BuiltinBytearraySpec("bytearray", ("string", "encoding", "errors"), 2)

if python_version >= 300:
    builtin_bytes_spec = BuiltinBytearraySpec("bytes", ("string", "encoding", "errors"), 3)


# Beware: One argument version defines "stop", not "start".
builtin_slice_spec = BuiltinParameterSpecNoKeywords("slice", ("start", "stop", "step"), 2)

builtin_hash_spec = BuiltinParameterSpecNoKeywords("hash", ("object",), 0)

builtin_format_spec = BuiltinParameterSpecNoKeywords("format", ("value", "format_spec"), 1)

builtin_sum_spec = BuiltinParameterSpecNoKeywords("sum", ("sequence", "start"), 1)

builtin_staticmethod_spec = BuiltinParameterSpecNoKeywords("staticmethod", ("function",), 0)
builtin_classmethod_spec = BuiltinParameterSpecNoKeywords("classmethod", ("function",), 0)

if python_version < 300:
    builtin_sorted_spec = BuiltinParameterSpecNoKeywords("sorted", ("iterable", "cmp", "key", "reverse"), 2)
else:
    builtin_sorted_spec = BuiltinParameterSpecNoKeywords("sorted", ("iterable", "key", "reverse"), 2)

builtin_reversed_spec = BuiltinParameterSpecNoKeywords("reversed", ("object",), 0)

builtin_reversed_spec = BuiltinParameterSpecNoKeywords("reversed", ("object",), 0)

if python_version < 300:
    builtin_enumerate_spec = BuiltinParameterSpec("enumerate", ("sequence",), 0)
else:
    builtin_enumerate_spec = BuiltinParameterSpec("enumerate", ("iterable",), 0)


class BuiltinRangeSpec(BuiltinParameterSpecNoKeywords):
    def isCompileTimeComputable(self, values):
        # For ranges, we need have many cases that can prevent the ability
        # to pre-compute, pylint: disable=too-many-branches,too-many-return-statements

        result = BuiltinParameterSpecNoKeywords.isCompileTimeComputable(
            self,
            values = values
        )

        if result:
            arg_count = len(values)

            if arg_count == 1:
                low = values[0]

                # If it's not a number constant, we can compute the exception
                # that will be raised.
                if not low.isNumberConstant():
                    return True

                return low.getConstant() < 256
            elif arg_count == 2:
                low, high = values

                # If it's not a number constant, we can compute the exception
                # that will be raised.
                if not low.isNumberConstant() or not high.isNumberConstant():
                    return True

                return high.getConstant() - low.getConstant() < 256
            elif arg_count == 3:
                low, high, step = values

                if not low.isNumberConstant() or \
                   not high.isNumberConstant() or \
                   not step.isNumberConstant():
                    return True

                low = low.getConstant()
                high = high.getConstant()
                step = step.getConstant()

                # It's going to give a ZeroDivisionError in this case.
                if step == 0:
                    return True

                if low < high:
                    if step < 0:
                        return True
                    else:
                        return math.ceil(float(high - low) / step) < 256
                else:
                    if step > 0:
                        return True
                    else:
                        return math.ceil(float(high - low) / step) < 256
            else:
                assert False
        else:
            return False


builtin_range_spec = BuiltinRangeSpec("range", ("start", "stop", "step"), 2)

if python_version >= 300:
    builtin_ascii_spec = BuiltinParameterSpecNoKeywords("ascii", ("object",), 0)


builtin_divmod_spec = BuiltinParameterSpecNoKeywords("divmod", ("left", "right"), 0)


def extractBuiltinArgs(node, builtin_spec, builtin_class,
                       empty_special_class = None):
    try:
        kw = node.getCallKw()

        # TODO: Could check for too many / too few, even if they are unknown, we
        # might raise that error, but that need not be optimized immediately.
        if kw is not None:
            if not kw.isMappingWithConstantStringKeys():
                return None

            pairs = kw.getMappingStringKeyPairs()

            if pairs and not builtin_spec.allowsKeywords():
                raise TooManyArguments(
                    TypeError(builtin_spec.getKeywordRefusalText())
                )
        else:
            pairs = ()

        args = node.getCallArgs()

        if args:
            if not args.canPredictIterationValues():
                return None

            positional = args.getIterationValues()
        else:
            positional = ()

        if not positional and not pairs and empty_special_class is not None:
            return empty_special_class(source_ref = node.getSourceReference())

        args_dict = matchCall(
            func_name     = builtin_spec.getName(),
            args          = builtin_spec.getArgumentNames(),
            star_list_arg = builtin_spec.getStarListArgumentName(),
            star_dict_arg = builtin_spec.getStarDictArgumentName(),
            num_defaults  = builtin_spec.getDefaultCount(),
            num_posonly   = builtin_spec.getPositionalOnlyCount(),
            positional    = positional,
            pairs         = pairs
        )
    except TooManyArguments as e:
        from nuitka.nodes.NodeMakingHelpers import (
            makeRaiseExceptionReplacementExpressionFromInstance,
            wrapExpressionWithSideEffects
        )

        return wrapExpressionWithSideEffects(
            new_node     = makeRaiseExceptionReplacementExpressionFromInstance(
                expression = node,
                exception  = e.getRealException()
            ),
            old_node     = node,
            side_effects = node.extractSideEffectsPreCall()
        )

    args_list = []

    for argument_name in builtin_spec.getArgumentNames():
        args_list.append(args_dict[argument_name])

    if builtin_spec.getStarListArgumentName() is not None:
        args_list.append(args_dict[builtin_spec.getStarListArgumentName()])

    if builtin_spec.getStarDictArgumentName() is not None:
        args_list.append(args_dict[builtin_spec.getStarDictArgumentName()])

    # Using list reference for passing the arguments without names,
    result = builtin_class(
        *args_list,
        source_ref = node.getSourceReference()
    )
    result.setCompatibleSourceReference(node.getCompatibleSourceReference())

    return result
