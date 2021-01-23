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
from .ExceptionNodes import (
    ExpressionBuiltinMakeException,
    ExpressionBuiltinMakeExceptionImportError,
)
from .ExpressionBases import CompileTimeConstantExpressionBase
from .shapes.BuiltinTypeShapes import tshape_exception_class


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

    @staticmethod
    def isKnownToBeHashable():
        return True

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    @staticmethod
    def mayHaveSideEffects():
        return False

    def getStrValue(self):
        return makeConstantRefNode(
            constant=str(self.getCompileTimeConstant()),
            user_provided=True,
            source_ref=self.source_ref,
        )


def makeExpressionBuiltinTypeRef(builtin_name, source_ref):
    return makeConstantRefNode(
        constant=__builtins__[builtin_name], source_ref=source_ref
    )


quick_names = {"None": None, "True": True, "False": False, "Ellipsis": Ellipsis}


def makeExpressionBuiltinRef(builtin_name, locals_scope, source_ref):
    assert builtin_name in builtin_names, builtin_name

    if builtin_name in quick_names:
        return makeConstantRefNode(
            constant=quick_names[builtin_name], source_ref=source_ref
        )
    elif builtin_name == "__debug__":
        return makeConstantRefNode(
            constant="no_asserts" not in getPythonFlags(), source_ref=source_ref
        )
    elif builtin_name in builtin_type_names:
        return makeExpressionBuiltinTypeRef(
            builtin_name=builtin_name, source_ref=source_ref
        )
    elif builtin_name in ("dir", "eval", "exec", "execfile", "locals", "vars"):
        return ExpressionBuiltinWithContextRef(
            builtin_name=builtin_name, locals_scope=locals_scope, source_ref=source_ref
        )
    else:
        return ExpressionBuiltinRef(builtin_name=builtin_name, source_ref=source_ref)


class ExpressionBuiltinRef(ExpressionBuiltinRefBase):
    kind = "EXPRESSION_BUILTIN_REF"

    __slots__ = ()

    # For overload
    locals_scope = None

    @staticmethod
    def isExpressionBuiltinRef():
        return True

    def __init__(self, builtin_name, source_ref):
        ExpressionBuiltinRefBase.__init__(
            self, builtin_name=builtin_name, source_ref=source_ref
        )

    def getCompileTimeConstant(self):
        return __builtins__[self.builtin_name]

    def computeExpressionRaw(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        from nuitka.optimizations.OptimizeBuiltinCalls import (
            computeBuiltinCall,
        )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        new_node, tags, message = computeBuiltinCall(
            builtin_name=self.builtin_name, call_node=call_node
        )

        if self.builtin_name in ("dir", "eval", "exec", "execfile", "locals", "vars"):
            # Just inform the collection that all has escaped.
            trace_collection.onLocalsUsage(locals_scope=self.getLocalsScope())

        return new_node, tags, message

    @staticmethod
    def isKnownToBeIterable(count):
        # TODO: Why yes, some may be, could be told here.
        return None


class ExpressionBuiltinWithContextRef(ExpressionBuiltinRef):
    """Same as ExpressionBuiltinRef, but with a context it refers to."""

    kind = "EXPRESSION_BUILTIN_WITH_CONTEXT_REF"

    __slots__ = ("locals_scope",)

    def __init__(self, builtin_name, locals_scope, source_ref):
        ExpressionBuiltinRef.__init__(
            self, builtin_name=builtin_name, source_ref=source_ref
        )

        self.locals_scope = locals_scope

    def getDetails(self):
        return {"builtin_name": self.builtin_name, "locals_scope": self.locals_scope}

    def getLocalsScope(self):
        return self.locals_scope


class ExpressionBuiltinAnonymousRef(ExpressionBuiltinRefBase):
    kind = "EXPRESSION_BUILTIN_ANONYMOUS_REF"

    __slots__ = ()

    def __init__(self, builtin_name, source_ref):
        assert builtin_name in builtin_anon_names, builtin_name

        ExpressionBuiltinRefBase.__init__(
            self, builtin_name=builtin_name, source_ref=source_ref
        )

    def getCompileTimeConstant(self):
        return builtin_anon_names[self.builtin_name]

    def computeExpressionRaw(self, trace_collection):
        return self, None, None


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

    @staticmethod
    def getTypeShape():
        return tshape_exception_class

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    def getCompileTimeConstant(self):
        return builtin_exception_values[self.builtin_name]

    def computeExpressionRaw(self, trace_collection):
        # Not much that can be done here.
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        exception_name = self.getExceptionName()

        def createBuiltinMakeException(args, name=None, path=None, source_ref=None):
            if exception_name == "ImportError" and python_version >= 0x300:
                return ExpressionBuiltinMakeExceptionImportError(
                    exception_name=exception_name,
                    args=args,
                    name=name,
                    path=path,
                    source_ref=source_ref,
                )
            else:
                # We expect to only get the star arguments for these.
                assert name is None
                assert path is None

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

        assert new_node is not None

        return new_node, "new_expression", "Detected built-in exception making."
