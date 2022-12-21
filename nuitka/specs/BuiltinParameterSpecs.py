#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Options
from nuitka.__past__ import builtins
from nuitka.PythonVersions import python_version
from nuitka.Tracing import optimization_logger

from .ParameterSpecs import ParameterSpec, TooManyArguments, matchCall


class BuiltinParameterSpec(ParameterSpec):
    __slots__ = ("builtin",)

    def __init__(
        self,
        name,
        arg_names,
        default_count,
        list_star_arg=None,
        is_list_star_arg_single=False,
        dict_star_arg=None,
        pos_only_args=(),
        kw_only_args=(),
        type_shape=None,
    ):
        ParameterSpec.__init__(
            self,
            ps_name=name,
            ps_normal_args=arg_names,
            ps_list_star_arg=list_star_arg,
            ps_is_list_star_arg_single=is_list_star_arg_single,
            ps_dict_star_arg=dict_star_arg,
            ps_default_count=default_count,
            ps_pos_only_args=pos_only_args,
            ps_kw_only_args=kw_only_args,
            type_shape=type_shape,
        )

        self.builtin = getattr(builtins, name, None)

        assert default_count <= len(arg_names) + len(kw_only_args) + len(pos_only_args)

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

    @staticmethod
    def isUserProvided(values):
        if Options.is_debug:
            for value in values:
                if (
                    value is not None
                    and not value.isExpressionConstantRef()
                    and getattr(value, "user_provided", True)
                ):
                    return False

            return True
        else:
            return False

    def simulateCall(self, given_values):
        # Using star dict call for simulation and catch any exception as really
        # fatal, pylint: disable=broad-except,too-many-branches

        try:
            given_normal_args = given_values[: self.getArgumentCount()]

            if self.list_star_arg:
                given_list_star_args = given_values[self.getArgumentCount()]
            else:
                given_list_star_args = None

            if self.dict_star_arg:
                given_dict_star_args = given_values[-1]
            else:
                given_dict_star_args = None

            arg_dict = {}

            for arg_name, given_value in zip(
                self.getArgumentNames(), given_normal_args
            ):
                assert type(given_value) not in (
                    tuple,
                    list,
                ), "do not like a tuple %s" % (given_value,)

                if given_value is not None:
                    arg_dict[arg_name] = given_value.getCompileTimeConstant()

            if given_dict_star_args:
                for given_dict_star_arg in reversed(given_dict_star_args):
                    arg_name = given_dict_star_arg.getKeyCompileTimeConstant()
                    arg_value = given_dict_star_arg.getValueCompileTimeConstant()

                    arg_dict[arg_name] = arg_value

            arg_list = []

            for arg_name in self.getArgumentNames():
                if arg_name not in arg_dict:
                    break

                arg_list.append(arg_dict[arg_name])
                del arg_dict[arg_name]

        except Exception as e:
            optimization_logger.sysexit_exception("Fatal optimization problem", e)

        if given_list_star_args:
            return self.builtin(
                *(
                    arg_list
                    + list(
                        value.getCompileTimeConstant() for value in given_list_star_args
                    )
                ),
                **arg_dict
            )
        else:
            return self.builtin(*arg_list, **arg_dict)


class BuiltinParameterSpecNoKeywords(BuiltinParameterSpec):
    __slots__ = ()

    def allowsKeywords(self):
        return False

    def simulateCall(self, given_values):
        # Using star dict call for simulation and catch any exception as really fatal,
        # pylint: disable=broad-except

        try:
            if self.list_star_arg:
                given_list_star_arg = given_values[self.getArgumentCount()]
            else:
                given_list_star_arg = None

            arg_list = []
            refuse_more = False

            for _arg_name, given_value in zip(self.getArgumentNames(), given_values):
                assert type(given_value) not in (
                    tuple,
                    list,
                ), "do not like tuple %s" % (given_value,)

                if given_value is not None:
                    if not refuse_more:
                        arg_list.append(given_value.getCompileTimeConstant())
                    else:
                        assert False
                else:
                    refuse_more = True

            if given_list_star_arg is not None:
                arg_list += [
                    value.getCompileTimeConstant() for value in given_list_star_arg
                ]
        except Exception as e:
            optimization_logger.sysexit_exception("matching call", e)

        return self.builtin(*arg_list)


class BuiltinParameterSpecExceptionsKwOnly(BuiltinParameterSpec):
    def __init__(self, exception_name, kw_only_args):
        BuiltinParameterSpec.__init__(
            self,
            name=exception_name,
            arg_names=(),
            default_count=len(kw_only_args),  # For exceptions, they will be required.
            list_star_arg="args",
            kw_only_args=kw_only_args,
        )


class BuiltinParameterSpecExceptions(BuiltinParameterSpec):
    def __init__(self, exception_name):
        BuiltinParameterSpec.__init__(
            self,
            name=exception_name,
            arg_names=(),
            default_count=0,
            list_star_arg="args",
        )

    def allowsKeywords(self):
        return False

    def getKeywordRefusalText(self):
        return "exceptions.%s does not take keyword arguments" % self.name

    def getCallableName(self):
        return "exceptions." + self.getName()


def makeBuiltinExceptionParameterSpec(exception_name):
    """Factory function to create parameter spec for an exception from its name.

    Args:
        exception_name - (str) name of the built-in exception

    Returns:
        ParameterSpec that can be used to evaluate calls of these exceptions.
    """
    if exception_name == "ImportError" and python_version >= 0x300:
        # This is currently the only known built-in exception that does it, but let's
        # be general, as surely that list is going to expand only.

        return BuiltinParameterSpecExceptionsKwOnly(
            exception_name=exception_name, kw_only_args=("name", "path")
        )
    else:
        return BuiltinParameterSpecExceptions(exception_name=exception_name)


class BuiltinParameterSpecPosArgs(BuiltinParameterSpec):
    def __init__(
        self,
        name,
        pos_only_args,
        arg_names,
        default_count,
        list_star_arg=None,
        dict_star_arg=None,
    ):
        BuiltinParameterSpec.__init__(
            self,
            name=name,
            arg_names=arg_names,
            default_count=default_count,
            pos_only_args=pos_only_args,
            list_star_arg=list_star_arg,
            dict_star_arg=dict_star_arg,
        )


if python_version < 0x370:
    builtin_int_spec = BuiltinParameterSpec("int", ("x", "base"), default_count=2)
else:
    builtin_int_spec = BuiltinParameterSpecPosArgs(
        "int", ("x",), ("base",), default_count=2
    )


# These builtins are only available for Python2
builtin_long_spec = BuiltinParameterSpec("long", ("x", "base"), default_count=2)
builtin_execfile_spec = BuiltinParameterSpecNoKeywords(
    "execfile", ("filename", "globals", "locals"), default_count=2
)

builtin_unicode_p2_spec = BuiltinParameterSpec(
    "unicode", ("string", "encoding", "errors"), default_count=3
)

builtin_xrange_spec = BuiltinParameterSpecNoKeywords(
    "xrange" if python_version < 0x300 else "range",
    ("start", "stop", "step"),
    default_count=2,
)


if python_version < 0x370:
    builtin_bool_spec = BuiltinParameterSpec("bool", ("x",), default_count=1)
else:
    builtin_bool_spec = BuiltinParameterSpecNoKeywords("bool", ("x",), default_count=1)

if python_version < 0x370:
    builtin_float_spec = BuiltinParameterSpec("float", ("x",), default_count=1)
else:
    builtin_float_spec = BuiltinParameterSpecNoKeywords(
        "float", ("x",), default_count=1
    )

builtin_complex_spec = BuiltinParameterSpec(
    "complex", ("real", "imag"), default_count=2
)

# This built-in have variable parameters for Python2/3
if python_version < 0x300:
    builtin_str_spec = BuiltinParameterSpec("str", ("object",), default_count=1)
else:
    builtin_str_spec = BuiltinParameterSpec(
        "str", ("object", "encoding", "errors"), default_count=3
    )

builtin_len_spec = BuiltinParameterSpecNoKeywords("len", ("object",), default_count=0)


class BuiltinParameterSpecSinglePosArgStarDictArgs(BuiltinParameterSpec):
    def __init__(
        self, name, list_star_arg="list_args", dict_star_arg="kw_args", type_shape=None
    ):
        BuiltinParameterSpec.__init__(
            self,
            name=name,
            arg_names=(),
            default_count=0,
            list_star_arg=list_star_arg,
            is_list_star_arg_single=True,
            dict_star_arg=dict_star_arg,
            type_shape=type_shape,
        )


builtin_dict_spec = BuiltinParameterSpecSinglePosArgStarDictArgs("dict")
builtin_any_spec = BuiltinParameterSpecNoKeywords("any", ("object",), default_count=0)
builtin_abs_spec = BuiltinParameterSpecNoKeywords("abs", ("object",), default_count=0)
builtin_all_spec = BuiltinParameterSpecNoKeywords("all", ("object",), default_count=0)

if python_version < 0x370:
    builtin_tuple_spec = BuiltinParameterSpec("tuple", ("sequence",), default_count=1)
    builtin_list_spec = BuiltinParameterSpec("list", ("sequence",), default_count=1)
else:
    builtin_tuple_spec = BuiltinParameterSpecNoKeywords(
        "tuple", ("sequence",), default_count=1
    )
    builtin_list_spec = BuiltinParameterSpecNoKeywords(
        "list", ("sequence",), default_count=1
    )

builtin_set_spec = BuiltinParameterSpecNoKeywords("set", ("iterable",), default_count=1)
builtin_frozenset_spec = BuiltinParameterSpecNoKeywords(
    "frozenset", ("iterable",), default_count=1
)

builtin_import_spec = BuiltinParameterSpec(
    "__import__", ("name", "globals", "locals", "fromlist", "level"), default_count=4
)

if python_version < 0x300:
    builtin_open_spec = BuiltinParameterSpec(
        "open", ("name", "mode", "buffering"), default_count=3
    )
else:
    builtin_open_spec = BuiltinParameterSpec(
        "open",
        (
            "file",
            "mode",
            "buffering",
            "encoding",
            "errors",
            "newline",
            "closefd",
            "opener",
        ),
        default_count=7,
    )

builtin_chr_spec = BuiltinParameterSpecNoKeywords("chr", ("i",), default_count=0)
builtin_ord_spec = BuiltinParameterSpecNoKeywords("ord", ("c",), default_count=0)
builtin_bin_spec = BuiltinParameterSpecNoKeywords("bin", ("number",), default_count=0)
builtin_oct_spec = BuiltinParameterSpecNoKeywords("oct", ("number",), default_count=0)
builtin_hex_spec = BuiltinParameterSpecNoKeywords("hex", ("number",), default_count=0)
builtin_id_spec = BuiltinParameterSpecNoKeywords("id", ("object",), default_count=0)
builtin_repr_spec = BuiltinParameterSpecNoKeywords("repr", ("object",), default_count=0)

builtin_dir_spec = BuiltinParameterSpecNoKeywords("dir", ("object",), default_count=1)
builtin_vars_spec = BuiltinParameterSpecNoKeywords("vars", ("object",), default_count=1)

builtin_locals_spec = BuiltinParameterSpecNoKeywords("locals", (), default_count=0)
builtin_globals_spec = BuiltinParameterSpecNoKeywords("globals", (), default_count=0)
builtin_eval_spec = BuiltinParameterSpecNoKeywords(
    "eval", ("source", "globals", "locals"), 2
)
if python_version < 0x300:
    builtin_compile_spec = BuiltinParameterSpec(
        "compile",
        ("source", "filename", "mode", "flags", "dont_inherit"),
        default_count=2,
    )
else:
    builtin_compile_spec = BuiltinParameterSpec(
        "compile",
        ("source", "filename", "mode", "flags", "dont_inherit", "optimize"),
        default_count=3,
    )
if python_version >= 0x300:
    builtin_exec_spec = BuiltinParameterSpecNoKeywords(
        "exec", ("source", "globals", "locals"), default_count=2
    )

# Note: Iter in fact names its first argument if the default applies
# "collection", fixed up in a wrapper.
builtin_iter_spec = BuiltinParameterSpecNoKeywords(
    "iter", ("callable", "sentinel"), default_count=1
)
builtin_next_spec = BuiltinParameterSpecNoKeywords(
    "next", ("iterator", "default"), default_count=1
)

# Note: type with 1 and type with 3 arguments are too different.
builtin_type1_spec = BuiltinParameterSpecNoKeywords(
    "type", ("object",), default_count=0
)
builtin_type3_spec = BuiltinParameterSpecNoKeywords(
    "type", ("name", "bases", "dict"), default_count=0
)

builtin_super_spec = BuiltinParameterSpecNoKeywords(
    "super", ("type", "object"), default_count=1 if python_version < 0x300 else 2
)

builtin_hasattr_spec = BuiltinParameterSpecNoKeywords(
    "hasattr", ("object", "name"), default_count=0
)
builtin_getattr_spec = BuiltinParameterSpecNoKeywords(
    "getattr", ("object", "name", "default"), default_count=1
)
builtin_setattr_spec = BuiltinParameterSpecNoKeywords(
    "setattr", ("object", "name", "value"), default_count=0
)

builtin_isinstance_spec = BuiltinParameterSpecNoKeywords(
    "isinstance", ("instance", "classes"), default_count=0
)

builtin_issubclass_spec = BuiltinParameterSpecNoKeywords(
    "issubclass", ("cls", "classes"), default_count=0
)


class BuiltinBytearraySpec(BuiltinParameterSpecPosArgs):
    def isCompileTimeComputable(self, values):
        # For bytearrays, we need to avoid the case of large bytearray
        # construction from an integer at compile time.

        result = BuiltinParameterSpec.isCompileTimeComputable(self, values=values)

        if result and len(values) == 1:
            index_value = values[0].getIndexValue()

            if index_value is None:
                return result

            return index_value < 256
        else:
            return result


builtin_bytearray_spec = BuiltinBytearraySpec(
    "bytearray", ("string",), ("encoding", "errors"), default_count=2
)

builtin_bytes_p3_spec = BuiltinBytearraySpec(
    "bytes", ("string",), ("encoding", "errors"), default_count=3
)


# Beware: One argument version defines "stop", not "start".
builtin_slice_spec = BuiltinParameterSpecNoKeywords(
    "slice", ("start", "stop", "step"), default_count=2
)

builtin_hash_spec = BuiltinParameterSpecNoKeywords("hash", ("object",), default_count=0)

builtin_format_spec = BuiltinParameterSpecNoKeywords(
    "format", ("value", "format_spec"), default_count=1
)

if python_version < 0x380:
    builtin_sum_spec = BuiltinParameterSpecNoKeywords(
        "sum", ("sequence", "start"), default_count=1
    )
else:
    builtin_sum_spec = BuiltinParameterSpecPosArgs(
        "sum", ("sequence",), ("start",), default_count=1
    )

builtin_staticmethod_spec = BuiltinParameterSpecNoKeywords(
    "staticmethod", ("function",), default_count=0
)
builtin_classmethod_spec = BuiltinParameterSpecNoKeywords(
    "classmethod", ("function",), default_count=0
)

if python_version < 0x300:
    builtin_sorted_spec = BuiltinParameterSpecNoKeywords(
        "sorted", ("iterable", "cmp", "key", "reverse"), default_count=2
    )
else:
    builtin_sorted_spec = BuiltinParameterSpecNoKeywords(
        "sorted", ("iterable", "key", "reverse"), default_count=2
    )

builtin_reversed_spec = BuiltinParameterSpecNoKeywords(
    "reversed", ("object",), default_count=0
)

builtin_reversed_spec = BuiltinParameterSpecNoKeywords(
    "reversed", ("object",), default_count=0
)

if python_version < 0x300:
    builtin_enumerate_spec = BuiltinParameterSpec(
        "enumerate", ("sequence", "start"), default_count=1
    )
else:
    builtin_enumerate_spec = BuiltinParameterSpec(
        "enumerate", ("iterable", "start"), default_count=1
    )


class BuiltinRangeSpec(BuiltinParameterSpecNoKeywords):
    def isCompileTimeComputable(self, values):
        # For ranges, we need have many cases that can prevent the ability
        # to pre-compute, pylint: disable=too-many-branches,too-many-return-statements

        result = BuiltinParameterSpecNoKeywords.isCompileTimeComputable(
            self, values=values
        )

        if result:
            arg_count = len(values)

            if arg_count == 1:
                low = values[0]

                # If it's not a number constant, we can compute the exception
                # that will be raised.
                if not low.isNumberConstant():
                    return True

                return low.getCompileTimeConstant() < 256
            elif arg_count == 2:
                low, high = values

                # If it's not a number constant, we can compute the exception
                # that will be raised.
                if not low.isNumberConstant() or not high.isNumberConstant():
                    return True

                return (
                    high.getCompileTimeConstant() - low.getCompileTimeConstant() < 256
                )
            elif arg_count == 3:
                low, high, step = values

                if (
                    not low.isNumberConstant()
                    or not high.isNumberConstant()
                    or not step.isNumberConstant()
                ):
                    return True

                low = low.getCompileTimeConstant()
                high = high.getCompileTimeConstant()
                step = step.getCompileTimeConstant()

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


builtin_range_spec = BuiltinRangeSpec(
    "range", ("start", "stop", "step"), default_count=2
)

if python_version >= 0x300:
    builtin_ascii_spec = BuiltinParameterSpecNoKeywords(
        "ascii", ("object",), default_count=0
    )


builtin_divmod_spec = BuiltinParameterSpecNoKeywords(
    "divmod", ("left", "right"), default_count=0
)


def extractBuiltinArgs(node, builtin_spec, builtin_class, empty_special_class=None):
    # Many cases to deal with, pylint: disable=too-many-branches

    try:
        kw = node.subnode_kwargs

        # TODO: Could check for too many / too few, even if they are unknown, we
        # might raise that error, but that need not be optimized immediately.
        if kw is not None:
            if not kw.isMappingWithConstantStringKeys():
                return None

            pairs = kw.getMappingStringKeyPairs()

            if pairs and not builtin_spec.allowsKeywords():
                raise TooManyArguments(TypeError(builtin_spec.getKeywordRefusalText()))
        else:
            pairs = ()

        args = node.subnode_args

        if args:
            if not args.canPredictIterationValues():
                return None

            positional = args.getIterationValues()
        else:
            positional = ()

        if not positional and not pairs and empty_special_class is not None:
            return empty_special_class(source_ref=node.getSourceReference())

        args_dict = matchCall(
            func_name=builtin_spec.getName(),
            args=builtin_spec.getArgumentNames(),
            kw_only_args=builtin_spec.getKwOnlyParameterNames(),
            star_list_arg=builtin_spec.getStarListArgumentName(),
            star_list_single_arg=builtin_spec.isStarListSingleArg(),
            star_dict_arg=builtin_spec.getStarDictArgumentName(),
            num_defaults=builtin_spec.getDefaultCount(),
            num_pos_only=builtin_spec.getPosOnlyParameterCount(),
            positional=positional,
            pairs=pairs,
        )
    except TooManyArguments as e:
        from nuitka.nodes.NodeMakingHelpers import (
            makeRaiseExceptionReplacementExpressionFromInstance,
            wrapExpressionWithSideEffects,
        )

        return wrapExpressionWithSideEffects(
            new_node=makeRaiseExceptionReplacementExpressionFromInstance(
                expression=node, exception=e.getRealException()
            ),
            old_node=node,
            side_effects=node.extractSideEffectsPreCall(),
        )

    # Using list reference for passing the arguments without names where it
    # it possible, otherwise dictionary to make those distinguishable.
    args_list = []

    for argument_name in builtin_spec.getArgumentNames():
        args_list.append(args_dict[argument_name])

    if builtin_spec.getStarListArgumentName() is not None:
        args_list.append(args_dict[builtin_spec.getStarListArgumentName()])

    if builtin_spec.getStarDictArgumentName() is not None:
        args_list.append(args_dict[builtin_spec.getStarDictArgumentName()])

    for argument_name in builtin_spec.getKwOnlyParameterNames():
        args_list.append(args_dict[argument_name])

    # Using list reference for passing the arguments without names,
    result = builtin_class(*args_list, source_ref=node.getSourceReference())

    if python_version < 0x380:
        result.setCompatibleSourceReference(node.getCompatibleSourceReference())

    return result
