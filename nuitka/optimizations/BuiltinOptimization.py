#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
import math
import sys

from nuitka.nodes.ParameterSpecs import (
    ParameterSpec,
    TooManyArguments,
    matchCall
)
from nuitka.Utils import python_version


class BuiltinParameterSpec(ParameterSpec):
    def __init__(self, name, arg_names, default_count, list_star_arg = None,
                  dict_star_arg = None):
        ParameterSpec.__init__(
            self,
            name          = name,
            normal_args   = arg_names,
            list_star_arg = list_star_arg,
            dict_star_arg = dict_star_arg,
            default_count = default_count,
            kw_only_args  = ()
        )

        self.builtin = __builtins__[name]

    def __repr__(self):
        return "<BuiltinParameterSpec %s>" % self.name

    def getName(self):
        return self.name

    def isCompileTimeComputable(self, values):
        # By default, we make this dependent on the ability to compute the
        # arguments, which is of course a good start for most cases, so this
        # is for overloads, pylint: disable=R0201

        for value in values:
            if value is not None and not value.isCompileTimeConstant():
                return False
        return True

    def simulateCall(self, given_values):
        # Using star dict call for simulation and catch any exception as really
        # fatal, pylint: disable=W0142,W0703

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

        except Exception as e:
            sys.exit("Fatal problem: %r" % e)

        if given_list_star_args:
            return self.builtin(
                *(value.getCompileTimeConstant() for value in given_list_star_args),
                **arg_dict
            )
        else:
            return self.builtin(**arg_dict)


class BuiltinParameterSpecNoKeywords(BuiltinParameterSpec):

    def allowsKeywords(self):
        return False

    def simulateCall(self, given_values):
        # Using star dict call for simulation and catch any exception as really fatal,
        # pylint: disable=W0142,W0703

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
            print >> sys.stderr, "Fatal error: ",
            import traceback
            traceback.print_exc()
            sys.exit(repr(e))

        return self.builtin(*arg_list)


class BuiltinParameterSpecExceptions(BuiltinParameterSpec):
    def __init__(self, exception_name, default_count):
        # TODO: Parameter default_count makes no sense for exceptions probably.
        BuiltinParameterSpec.__init__(
            self,
            name          = exception_name,
            arg_names     = (),
            default_count = default_count,
            list_star_arg = "args"
        )

    def allowsKeywords(self):
        return False

    def getKeywordRefusalText(self):
        return "exceptions.%s does not take keyword arguments" % self.name

    def getCallableName(self):
        return "exceptions." + self.getName()


def makeBuiltinParameterSpec(exception_name):
    if exception_name == "ImportError" and python_version >= 330:
        # TODO: Create this beast, needs keyword only arguments to be supported,
        # currently user of this function must take care to not have them.
        pass

    return BuiltinParameterSpecExceptions(
        exception_name = exception_name,
        default_count  = 0
    )

builtin_int_spec = BuiltinParameterSpec("int", ('x', "base"), 2)

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
    builtin_xrange_spec = BuiltinParameterSpec(
        "xrange",
        ("start", "stop", "step"),
        2
    )


builtin_bool_spec = BuiltinParameterSpec("bool", ('x',), 1)
builtin_float_spec = BuiltinParameterSpec("float", ('x',), 1)

# This built-in have variable parameters for Python2/3
if python_version < 300:
    builtin_str_spec = BuiltinParameterSpec("str", ("object",), 1)
else:
    builtin_str_spec = BuiltinParameterSpec("str", ("object", "encoding", "errors"), 3)

builtin_len_spec = BuiltinParameterSpecNoKeywords("len", ("object",), 0)
builtin_dict_spec = BuiltinParameterSpec("dict", (), 0, "list_args", "dict_args")
builtin_len_spec = BuiltinParameterSpecNoKeywords("len", ("object",), 0)
builtin_tuple_spec = BuiltinParameterSpec("tuple", ("sequence",), 1)
builtin_list_spec = BuiltinParameterSpec("list", ("sequence",), 1)
builtin_set_spec = BuiltinParameterSpecNoKeywords("set", ("iterable",), 1)

builtin_import_spec = BuiltinParameterSpec("__import__", ("name", "globals", "locals", "fromlist", "level"), 4)
builtin_open_spec = BuiltinParameterSpec("open", ("name", "mode", "buffering"), 3)
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

builtin_bytearray_spec = BuiltinParameterSpecNoKeywords("bytearray", ("iterable_of_ints",), 1)

# Beware: One argument defines stop, not start.
builtin_slice_spec = BuiltinParameterSpecNoKeywords("slice", ("start", "stop", "step"), 2)

class BuiltinRangeSpec(BuiltinParameterSpecNoKeywords):
    def __init__(self, *args):
        BuiltinParameterSpecNoKeywords.__init__(self, *args)

    def isCompileTimeComputable(self, values):
        # For ranges, we need have many cases that can prevent the ability
        # to pre-compute, pylint: disable=R0911,R0912

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


def extractBuiltinArgs(node, builtin_spec, builtin_class,
                       empty_special_class = None):
    try:
        kw = node.getCallKw()

        # TODO: Could check for too many / too few, even if they are unknown, we
        # might raise that error, but that need not be optimized immediately.
        if not kw.isMappingWithConstantStringKeys():
            return None

        pairs = kw.getMappingStringKeyPairs()

        if pairs and not builtin_spec.allowsKeywords():
            raise TooManyArguments(
                TypeError(builtin_spec.getKeywordRefusalText())
            )

        args = node.getCallArgs()

        if not args.canPredictIterationValues():
            return None

        positional = args.getIterationValues()

        if not positional and not pairs and empty_special_class is not None:
            return empty_special_class(source_ref = node.getSourceReference())

        args_dict = matchCall(
            func_name     = builtin_spec.getName(),
            args          = builtin_spec.getArgumentNames(),
            star_list_arg = builtin_spec.getStarListArgumentName(),
            star_dict_arg = builtin_spec.getStarDictArgumentName(),
            num_defaults  = builtin_spec.getDefaultCount(),
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
            side_effects = node.extractPreCallSideEffects()
        )

    args_list = []

    for argument_name in builtin_spec.getArgumentNames():
        args_list.append(args_dict[argument_name])

    if builtin_spec.getStarListArgumentName() is not None:
        args_list.append(args_dict[builtin_spec.getStarListArgumentName()])

    if builtin_spec.getStarDictArgumentName() is not None:
        args_list.append(args_dict[builtin_spec.getStarDictArgumentName()])

    # Using list reference for passing the arguments without names,
    # pylint: disable=W0142
    result = builtin_class(
        *args_list,
        source_ref = node.getSourceReference()
    )
    result.setCompatibleSourceReference(node.getCompatibleSourceReference())

    return result
