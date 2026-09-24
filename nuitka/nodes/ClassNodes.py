#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nodes for classes and their creations.

The classes are are at the core of the language and have their complexities.

"""

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.PythonVersions import python_version

from .ChildrenHavingMixins import (
    ChildrenExpressionBuiltinType3Mixin,
    ChildrenHavingMetaclassBasesMixin,
)
from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import ExpressionBase
from .ExpressionBasesGenerated import (
    ExpressionCallClassPrepareBase,
    ExpressionCallMetaclassBase,
)
from .ExpressionShapeMixins import ExpressionDictShapeExactMixin
from .IndicatorMixins import MarkNeedsAnnotationsMixin
from .IterationHandles import ConstantDictIterationHandle
from .LocalsScopes import getLocalsDictHandle
from .NodeMakingHelpers import makeConstantReplacementNode
from .OutlineNodes import ExpressionOutlineFunctionBase
from .shapes.BuiltinTypeShapes import tshape_dict
from .shapes.StandardShapes import tshape_unknown


class ExpressionClassBodyBase(ExpressionOutlineFunctionBase):
    kind = "EXPRESSION_CLASS_BODY"

    __slots__ = ("doc", "locals_scope")

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

    __slots__ = (
        "needs_annotations_dict",
        "qualname_setup",
        "static_attributes",
        "deferred_annotations",
    )

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
        self.static_attributes = OrderedSet() if python_version >= 0x3D0 else None
        self.deferred_annotations = OrderedDict() if python_version >= 0x3E0 else None

    def addStaticAttribute(self, static_attribute):
        self.static_attributes.add(static_attribute)

    def getStaticAttributes(self):
        return tuple(self.static_attributes)


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

        # spell-checker: ignore pythonapi
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
        # meta_class = self._calculateMetaClass()

        # TODO: Should be compile time computable if bases and dict are
        # allowing that to happen into a dedicated class creation node,
        # with known metaclass selection.

        # Any exception may be raised.
        if self.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionCallMetaclass(ExpressionCallMetaclassBase):
    kind = "EXPRESSION_CALL_METACLASS"

    named_children = ("metaclass", "name", "bases", "dict_arg", "class_decl_dict")
    node_attributes = ("class_variable",)

    def __init__(
        self,
        metaclass,
        name,
        bases,
        dict_arg,
        class_decl_dict,
        class_variable,
        source_ref,
    ):
        ExpressionCallMetaclassBase.__init__(
            self,
            metaclass=metaclass,
            name=name,
            bases=bases,
            dict_arg=dict_arg,
            class_decl_dict=class_decl_dict,
            class_variable=class_variable,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # Any exception may be raised by metaclass call.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return True


class ExpressionCallClassPrepareCommonBase(ExpressionCallClassPrepareBase):
    """Common base for the class prepare nodes."""

    def computeExpression(self, trace_collection):
        if self.subnode_called.isCompileTimeConstant():
            return (
                makeConstantReplacementNode(
                    constant=self.subnode_called.getCompileTimeConstant(),
                    node=self,
                    user_provided=False,
                ),
                "new_constant",
                "Result of '__prepare__' computed at compile time.",
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionCallClassPrepare(ExpressionCallClassPrepareCommonBase):
    kind = "EXPRESSION_CALL_CLASS_PREPARE"

    named_children = ("called",)
    node_attributes = (
        "type_shape",
        "code_name",
        "expected_value",
    )

    # Without a start value, there is no PGO data to check.
    pgo_policy = None

    def __init__(
        self,
        called,
        type_shape,
        code_name,
        expected_value,
        source_ref,
    ):
        # TODO: Add a "tshape_sane_mapping" shape for non-dict mappings, where
        # setting does not raise and set values persist, which is what class
        # body optimizations need. A plain mapping shape would not help, and
        # "collections.OrderedDict" is not usable as a dict, since it keeps its
        # own item order and dict operations would bypass it.
        if type_shape is not tshape_dict:
            type_shape = tshape_unknown
            expected_value = None

        assert expected_value is None or type(expected_value) is dict, expected_value

        ExpressionCallClassPrepareCommonBase.__init__(
            self,
            called=called,
            type_shape=type_shape,
            code_name=code_name,
            expected_value=expected_value,
            source_ref=source_ref,
        )

    def getExpectedValue(self):
        if self.expected_value is not None:
            return True, self.expected_value

        return False, None

    def getExpressionDictInConstant(self, value):
        # The PGO value is asserted at run time, so it can be used for
        # compile time decisions.
        if self.expected_value is not None:
            return value in self.expected_value

        return None

    @staticmethod
    def mayRaiseExceptionOperation():
        return False

    def mayRaiseException(self, exception_type):
        return self.subnode_called.mayRaiseException(exception_type)

    def getTypeShape(self):
        return self.type_shape


class ExpressionCallClassPrepareKnownStartValueDictBase(
    ExpressionDictShapeExactMixin, ExpressionCallClassPrepareCommonBase
):
    """Base for class prepare nodes with a known start value."""

    named_children = ("called",)
    node_attributes = (
        "type_shape",
        "code_name",
        "expected_value",
    )

    __slots__ = ("constant",)

    def __init__(
        self,
        called,
        type_shape,
        code_name,
        expected_value,
        source_ref,
    ):
        assert type_shape is tshape_dict, type_shape
        assert (
            expected_value is not None and type(expected_value) is dict
        ), expected_value
        assert self.pgo_policy in ("ignore", "assertion", "exception"), self.pgo_policy

        ExpressionCallClassPrepareCommonBase.__init__(
            self,
            called=called,
            type_shape=type_shape,
            code_name=code_name,
            expected_value=expected_value,
            source_ref=source_ref,
        )

        self.constant = expected_value

    # With the start value present, parity to dictionary constant nodes is
    # possible, and the interfaces do not need to check the value presence.

    def getExpectedValue(self):
        return True, self.expected_value

    def getExpressionDictInConstant(self, value):
        return value in self.expected_value

    @staticmethod
    def isMutable():
        return True

    @staticmethod
    def isIterableConstant():
        return True

    def getIterationLength(self):
        return len(self.expected_value)

    def getIterationHandle(self):
        return ConstantDictIterationHandle(self)

    def getIterationValue(self, count):
        assert count < len(self.expected_value)

        return makeConstantRefNode(
            constant=tuple(self.expected_value)[count], source_ref=self.source_ref
        )

    def getIterationValueRange(self, start, stop):
        return [
            makeConstantRefNode(constant=value, source_ref=self.source_ref)
            for value in tuple(self.expected_value)[start:stop]
        ]

    def getIterationValues(self):
        return tuple(
            makeConstantRefNode(constant=value, source_ref=self.source_ref)
            for value in self.expected_value
        )

    def getTruthValue(self):
        return bool(self.expected_value)

    def getComparisonValue(self):
        return True, self.expected_value

    def mayRaiseException(self, exception_type):
        return (
            self.pgo_policy != "ignore"
            and self.subnode_called.mayRaiseException(exception_type)
        ) or self.mayRaiseExceptionOperation()


class ExpressionCallClassPrepareKnownStartValueDictIgnored(
    ExpressionCallClassPrepareKnownStartValueDictBase
):
    kind = "EXPRESSION_CALL_CLASS_PREPARE_KNOWN_START_VALUE_DICT_IGNORED"

    pgo_policy = "ignore"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionCallClassPrepareKnownStartValueDictAsserted(
    ExpressionCallClassPrepareKnownStartValueDictBase
):
    kind = "EXPRESSION_CALL_CLASS_PREPARE_KNOWN_START_VALUE_DICT_ASSERTED"

    pgo_policy = "assertion"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionCallClassPrepareKnownStartValueDictException(
    ExpressionCallClassPrepareKnownStartValueDictBase
):
    kind = "EXPRESSION_CALL_CLASS_PREPARE_KNOWN_START_VALUE_DICT_EXCEPTION"

    pgo_policy = "exception"

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
