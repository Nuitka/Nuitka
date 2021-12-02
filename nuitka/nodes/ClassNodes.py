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
""" Nodes for classes and their creations.

The classes are are at the core of the language and have their complexities.

"""

from nuitka.PythonVersions import python_version

from .ExpressionBases import ExpressionChildrenHavingBase
from .IndicatorMixins import MarkNeedsAnnotationsMixin
from .LocalsScopes import getLocalsDictHandle
from .OutlineNodes import ExpressionOutlineFunctionBase


class ExpressionClassBody(MarkNeedsAnnotationsMixin, ExpressionOutlineFunctionBase):
    kind = "EXPRESSION_CLASS_BODY"

    __slots__ = ("needs_annotations_dict", "doc")

    if python_version >= 0x340:
        __slots__ += ("qualname_setup",)

    def __init__(self, provider, name, doc, source_ref):
        ExpressionOutlineFunctionBase.__init__(
            self,
            provider=provider,
            name=name,
            body=None,
            code_prefix="class",
            source_ref=source_ref,
        )

        MarkNeedsAnnotationsMixin.__init__(self)

        self.doc = doc

        # Force creation with proper type.
        if python_version >= 0x300:
            locals_kind = "python3_class"
        else:
            locals_kind = "python2_class"

        self.locals_scope = getLocalsDictHandle(
            "locals_%s_%d" % (self.getCodeName(), source_ref.getLineNumber()),
            locals_kind,
            self,
        )

        if python_version >= 0x340:
            self.qualname_setup = None

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

    def markAsDirectlyCalled(self):
        pass

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


class ExpressionSelectMetaclass(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SELECT_METACLASS"

    named_children = ("metaclass", "bases")

    def __init__(self, metaclass, bases, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, values={"metaclass": metaclass, "bases": bases}, source_ref=source_ref
        )

    def computeExpression(self, trace_collection):
        # TODO: Meta class selection is very computable, and should be done.
        return self, None, None


class ExpressionBuiltinType3(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_TYPE3"

    named_children = ("type_name", "bases", "dict")

    def __init__(self, type_name, bases, type_dict, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"type_name": type_name, "bases": bases, "dict": type_dict},
            source_ref=source_ref,
        )

    def _calculateMetaClass(self):
        # TODO: Share code with ExpressionSelectMetaclass

        if not self.subnode_bases.isCompileTimeConstant():
            return None

        # TODO: Want to cache this result probably for speed reasons and it may also
        # contain allocations for dataclasses, generics, etc.

        # Need to use private CPython API unless we want to re-implement it, pylint: disable=protected-access
        import ctypes

        ctypes.pythonapi._PyType_CalculateMetaclass.argtypes = [
            ctypes.py_object,
            ctypes.py_object,
        ]
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
