#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes for classes and their creations.

The classes are are at the core of the language and have their complexities.

"""

from nuitka.PythonVersions import python_version

from .ChildrenHavingMixins import (
    ChildrenExpressionBuiltinType3Mixin,
    ChildrenHavingMetaclassBasesMixin,
)
from .ExpressionBases import ExpressionBase
from .ExpressionShapeMixins import ExpressionDictShapeExactMixin
from .IndicatorMixins import MarkNeedsAnnotationsMixin
from .LocalsScopes import getLocalsDictHandle
from .OutlineNodes import ExpressionOutlineFunctionBase


class ExpressionClassBodyBase(ExpressionOutlineFunctionBase):
    kind = "EXPRESSION_CLASS_BODY"

    __slots__ = ("doc",)

    def __init__(self, provider, name, doc, source_ref):
        ExpressionOutlineFunctionBase.__init__(
            self,
            provider=provider,
            name=name,
            body=None,
            code_prefix="class",
            source_ref=source_ref,
        )

        self.doc = doc

        self.locals_scope = getLocalsDictHandle(
            "locals_%s_%d" % (self.getCodeName(), source_ref.getLineNumber()),
            self.locals_kind,
            self,
        )

    @staticmethod
    def isExpressionClassBodyBase():
        return True

    def getDetails(self):
        return {
            "name": self.getFunctionName(),
            "provider": self.provider.getCodeName(),
            "doc": self.doc,
            "flags": self.flags,
        }

    def getDetailsForDisplay(self):
        result = {
            "name": self.getFunctionName(),
            "provider": self.provider.getCodeName(),
            "flags": "" if self.flags is None else ",".join(sorted(self.flags)),
        }

        if self.doc is not None:
            result["doc"] = self.doc

        return result

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        return cls(provider=provider, source_ref=source_ref, **args)

    def getDoc(self):
        return self.doc

    @staticmethod
    def isEarlyClosure():
        return True

    def getVariableForClosure(self, variable_name):
        # print( "getVariableForClosure", self, variable_name )

        # The class bodies provide no closure, except under CPython3.x, there
        # they provide "__class__" but nothing else.

        if variable_name == "__class__":
            if python_version < 0x300:
                return self.provider.getVariableForClosure("__class__")
            else:
                return ExpressionOutlineFunctionBase.getVariableForClosure(
                    self, variable_name="__class__"
                )
        else:
            result = self.provider.getVariableForClosure(variable_name)
            self.taken.add(result)
            return result

    @staticmethod
    def markAsDirectlyCalled():
        pass

    def getChildQualname(self, function_name):
        return self.getFunctionQualname() + "." + function_name

    @staticmethod
    def mayHaveSideEffects():
        # The function definition has no side effects, calculating the defaults
        # would be, but that is done outside of this.
        return False

    def mayRaiseException(self, exception_type):
        return self.subnode_body.mayRaiseException(exception_type)

    def isUnoptimized(self):
        # Classes all are that.
        return True


class ExpressionClassMappingBody(MarkNeedsAnnotationsMixin, ExpressionClassBodyBase):
    """For use in cases, where the Python3 class is possibly a mapping."""

    kind = "EXPRESSION_CLASS_MAPPING_BODY"

    __slots__ = ("needs_annotations_dict", "qualname_setup")

    # Force creation with proper type.
    locals_kind = "python_mapping_class"

    def __init__(self, provider, name, doc, source_ref):
        ExpressionClassBodyBase.__init__(
            self,
            provider=provider,
            name=name,
            doc=doc,
            source_ref=source_ref,
        )

        MarkNeedsAnnotationsMixin.__init__(self)

        self.qualname_setup = None


class ExpressionClassDictBodyP2(ExpressionDictShapeExactMixin, ExpressionClassBodyBase):
    kind = "EXPRESSION_CLASS_DICT_BODY_P2"

    __slots__ = ()

    locals_kind = "python_dict_class"

    def __init__(self, provider, name, doc, source_ref):
        ExpressionClassBodyBase.__init__(
            self,
            provider=provider,
            name=name,
            doc=doc,
            source_ref=source_ref,
        )


class ExpressionClassDictBody(MarkNeedsAnnotationsMixin, ExpressionClassDictBodyP2):
    """For use in cases, where it's compile time pre-optimization determined to be a dictionary."""

    kind = "EXPRESSION_CLASS_DICT_BODY"

    __slots__ = ("needs_annotations_dict", "qualname_setup")

    def __init__(self, provider, name, doc, source_ref):
        ExpressionClassDictBodyP2.__init__(
            self,
            provider=provider,
            name=name,
            doc=doc,
            source_ref=source_ref,
        )

        MarkNeedsAnnotationsMixin.__init__(self)

        self.qualname_setup = None


class ExpressionSelectMetaclass(ChildrenHavingMetaclassBasesMixin, ExpressionBase):
    kind = "EXPRESSION_SELECT_METACLASS"

    named_children = ("metaclass", "bases")

    def __init__(self, metaclass, bases, source_ref):
        ChildrenHavingMetaclassBasesMixin.__init__(
            self,
            metaclass=metaclass,
            bases=bases,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bases.isExpressionConstantTupleEmptyRef():
            return (
                self.subnode_metaclass,
                "new_expression",
                "Metaclass selection without bases is trivial.",
            )

        # TODO: Meta class selection is very computable, and should be done, but we need
        # dictionary tracing for that.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return not self.subnode_bases.isExpressionConstantTupleEmptyRef()


class ExpressionBuiltinType3(ChildrenExpressionBuiltinType3Mixin, ExpressionBase):
    kind = "EXPRESSION_BUILTIN_TYPE3"

    named_children = ("type_name", "bases", "dict_arg")

    def __init__(self, type_name, bases, dict_arg, source_ref):
        ChildrenExpressionBuiltinType3Mixin.__init__(
            self,
            type_name=type_name,
            bases=bases,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def _calculateMetaClass(self):
        # TODO: Share code with ExpressionSelectMetaclass

        if not self.subnode_bases.isCompileTimeConstant():
            return None

        # TODO: Want to cache this result probably for speed reasons and it may also
        # contain allocations for dataclasses, generics, etc.

        # Need to use private CPython API unless we want to re-implement it, pylint: disable=protected-access
        import ctypes

        ctypes.pythonapi._PyType_CalculateMetaclass.argtypes = (
            ctypes.py_object,
            ctypes.py_object,
        )
        ctypes.pythonapi._PyType_CalculateMetaclass.restype = ctypes.py_object

        bases = self.subnode_bases.getCompileTimeConstant()

        return ctypes.pythonapi._PyType_CalculateMetaclass(type, bases)

    def mayRaiseException(self, exception_type):
        # TODO: In many cases, this will not raise for compile time knowable
        # case classes. We might ask the bases for the metaclass selected by
        # compile time inspection.
        return True

    def computeExpression(self, trace_collection):
        # TODO: Can use this to specialize to the correct metaclass at compile
        # time.
        # metacls = self._calculateMetaClass()

        # TODO: Should be compile time computable if bases and dict are
        # allowing that to happen into a dedicated class creation node,
        # with known metaclass selection.

        # Any exception may be raised.
        if self.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


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
