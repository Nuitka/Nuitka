#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Tree nodes for built-in references.

There is 2 major types of built-in references. One is the values from
built-ins, the other is built-in exceptions. They work differently and
mean different things, but they have similar origin, that is, access
to variables only ever read.

"""


from nuitka.Builtins import (
    builtin_anon_names,
    builtin_exception_names,
    builtin_exception_values,
    builtin_names,
    builtin_type_names,
)
from nuitka.Options import getPythonFlags
from nuitka.PythonVersions import python_version
from nuitka.specs import BuiltinParameterSpecs

from .ConstantRefNodes import makeConstantRefNode
from .ExceptionNodes import ExpressionBuiltinMakeException
from .ExpressionBases import CompileTimeConstantExpressionBase


class ExpressionBuiltinRefBase(CompileTimeConstantExpressionBase):
    # Base classes can be abstract, pylint: disable=abstract-method

    __slots__ = ("builtin_name",)

    def __init__(self, builtin_name, source_ref):
        CompileTimeConstantExpressionBase.__init__(self, source_ref=source_ref)

        self.builtin_name = builtin_name

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {"builtin_name": self.builtin_name}

    def getBuiltinName(self):
        return self.builtin_name

    def isKnownToBeHashable(self):
        return True

    def mayRaiseException(self, exception_type):
        return False

    def mayHaveSideEffects(self):
        return False

    def getStrValue(self):
        return makeConstantRefNode(
            constant=str(self.getCompileTimeConstant()),
            user_provided=True,
            source_ref=self.getSourceReference(),
        )


_debug_value = "no_asserts" not in getPythonFlags()


def makeExpressionBuiltinRef(builtin_name, source_ref):
    assert builtin_name in builtin_names, builtin_name

    quick_names = {
        "None": None,
        "True": True,
        "False": False,
        "__debug__": _debug_value,
        "Ellipsis": Ellipsis,
    }

    if builtin_name in quick_names:
        return makeConstantRefNode(
            constant=quick_names[builtin_name], source_ref=source_ref
        )
    elif builtin_name in builtin_type_names:
        return makeConstantRefNode(
            constant=__builtins__[builtin_name], source_ref=source_ref
        )
    else:
        return ExpressionBuiltinRef(builtin_name=builtin_name, source_ref=source_ref)


class ExpressionBuiltinRef(ExpressionBuiltinRefBase):
    kind = "EXPRESSION_BUILTIN_REF"

    __slots__ = ()

    def __init__(self, builtin_name, source_ref):
        ExpressionBuiltinRefBase.__init__(
            self, builtin_name=builtin_name, source_ref=source_ref
        )

    def isCompileTimeConstant(self):
        return True

    def getCompileTimeConstant(self):
        return __builtins__[self.builtin_name]

    def computeExpressionRaw(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        from nuitka.optimizations.OptimizeBuiltinCalls import computeBuiltinCall

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        new_node, tags, message = computeBuiltinCall(
            builtin_name=self.builtin_name, call_node=call_node
        )

        if self.builtin_name in ("dir", "eval", "exec", "execfile", "locals", "vars"):
            # Just inform the collection that all has escaped.
            trace_collection.onLocalsUsage(self.getParentVariableProvider())

        return new_node, tags, message

    def getStringValue(self):
        return repr(self.getCompileTimeConstant())

    def isKnownToBeIterable(self, count):
        # TODO: Why yes, some may be, could be told here.
        return None


class ExpressionBuiltinAnonymousRef(ExpressionBuiltinRefBase):
    kind = "EXPRESSION_BUILTIN_ANONYMOUS_REF"

    __slots__ = ()

    def __init__(self, builtin_name, source_ref):
        assert builtin_name in builtin_anon_names, builtin_name

        ExpressionBuiltinRefBase.__init__(
            self, builtin_name=builtin_name, source_ref=source_ref
        )

    def isCompileTimeConstant(self):
        return True

    def getCompileTimeConstant(self):
        return builtin_anon_names[self.builtin_name]

    def computeExpressionRaw(self, trace_collection):
        return self, None, None

    def getStringValue(self):
        return repr(self.getCompileTimeConstant())


class ExpressionBuiltinExceptionRef(ExpressionBuiltinRefBase):
    kind = "EXPRESSION_BUILTIN_EXCEPTION_REF"

    __slots__ = ()

    def __init__(self, exception_name, source_ref):
        assert exception_name in builtin_exception_names, exception_name

        ExpressionBuiltinRefBase.__init__(
            self, builtin_name=exception_name, source_ref=source_ref
        )

    def getDetails(self):
        return {"exception_name": self.builtin_name}

    getExceptionName = ExpressionBuiltinRefBase.getBuiltinName

    def isCompileTimeConstant(self):
        return True

    def mayRaiseException(self, exception_type):
        return False

    def getCompileTimeConstant(self):
        return builtin_exception_values[self.builtin_name]

    def computeExpressionRaw(self, trace_collection):
        # Not much that can be done here.
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        exception_name = self.getExceptionName()

        # TODO: Keyword only arguments of it, are not properly handled yet by
        # the built-in call code.
        if exception_name == "ImportError" and python_version >= 300:
            if call_kw is not None and (
                not call_kw.isExpressionConstantRef() or call_kw.getConstant() != {}
            ):
                return call_node, None, None

        def createBuiltinMakeException(args, source_ref):
            return ExpressionBuiltinMakeException(
                exception_name=exception_name, args=args, source_ref=source_ref
            )

        new_node = BuiltinParameterSpecs.extractBuiltinArgs(
            node=call_node,
            builtin_class=createBuiltinMakeException,
            builtin_spec=BuiltinParameterSpecs.makeBuiltinExceptionParameterSpec(
                exception_name=exception_name
            ),
        )

        # TODO: Don't allow this to happen.
        if new_node is None:
            return call_node, None, None

        return new_node, "new_expression", "Detected built-in exception making."
