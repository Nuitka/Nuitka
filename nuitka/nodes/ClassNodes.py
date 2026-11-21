#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nodes for classes and their creation."""

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.PythonVersions import python_version
from nuitka.tree.Extractions import getClonedProvider

from .ChildrenHavingMixins import (
    ChildHavingBodyOptionalMixin,
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


def _translateClonedDescendant(old_root, new_root, target_node):
    """Find the node corresponding to 'target_node' in a cloned tree.

    Notes:
        'target_node' must be a descendant of 'old_root', and 'new_root' must
        be its 'makeClone' result, which clones children in
        'getVisitableNodes' order. The result has the same 'kind' as
        'target_node'.
    """

    assert new_root.__class__ is old_root.__class__, (old_root, new_root)

    path = []
    current = target_node

    while current is not old_root:
        parent = current.parent
        assert parent is not None, (target_node, old_root)

        for index, child in enumerate(parent.getVisitableNodes()):
            if child is current:
                path.append(index)
                break
        else:
            assert False, (current, parent)

        current = parent

    result = new_root
    for index in reversed(path):
        result = result.getVisitableNodes()[index]

    assert result.kind == target_node.kind, (result, target_node)
    return result


class ExpressionClassBodyBase(ExpressionOutlineFunctionBase):
    kind = "EXPRESSION_CLASS_BODY"

    __slots__ = (
        "doc",
        "locals_scope",
        "conditional_annotation_indices",
        "conditional_annotations_variable",
        "deferred_class_dict",
    )

    def __init__(self, provider, name, doc, source_ref, body=None, flags=None):
        ExpressionOutlineFunctionBase.__init__(
            self,
            provider=provider,
            name=name,
            body=body,
            code_prefix="class",
            flags=flags,
            source_ref=source_ref,
        )

        self.doc = doc

        # Python 3.14+ PEP 649 conditional annotations.
        self.conditional_annotation_indices = None
        self.conditional_annotations_variable = None
        self.deferred_class_dict = None

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
            "provider": self.provider,
            "name": self.name,
            "doc": self.doc,
            "flags": None if self.flags is None else set(self.flags),
        }

    def _getCloneDetails(self):
        # Preserve the Python class name instead of appending "_clone".
        result = self.getDetails()
        result["provider"] = getClonedProvider(result["provider"])

        return result

    def getCloneArgs(self):
        # Preserve the Python class name instead of appending "_clone".
        return ChildHavingBodyOptionalMixin.getCloneArgs(self)

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
        if "doc" not in args:
            args["doc"] = None

        if "flags" in args and isinstance(args["flags"], str):
            args["flags"] = set(args["flags"].split(",")) if args["flags"] else None

        return cls(provider=provider, source_ref=source_ref, **args)

    def _copyClassBodyCloneState(self, result, variable_translations):
        if python_version >= 0x300:
            if self.qualname_provider is not self.provider:
                result.qualname_provider = getClonedProvider(self.qualname_provider)

            if self.non_local_declarations is not None:
                result.non_local_declarations = list(self.non_local_declarations)

        if self.deferred_class_dict is not None:
            result.deferred_class_dict = variable_translations.get(
                self.deferred_class_dict, self.deferred_class_dict
            )

        if self.conditional_annotation_indices is not None:
            result.conditional_annotation_indices = dict(
                self.conditional_annotation_indices
            )

        if self.conditional_annotations_variable is not None:
            result.conditional_annotations_variable = variable_translations.get(
                self.conditional_annotations_variable,
                self.conditional_annotations_variable,
            )

    def getDoc(self):
        return self.doc

    @staticmethod
    def isEarlyClosure():
        return True

    def registerVariableBinding(self, variable_name):
        self.getLocalsScope().registerBoundVariableName(variable_name)

    def getVariableForClosure(self, variable_name):
        # The class bodies provide no closure, except under CPython3.x, there
        # they provide "__class__" and the "__conditional_annotations__" for 3.14
        # but nothing else.
        if variable_name in ("__class__", "__conditional_annotations__"):
            if python_version < 0x300:
                return self.provider.getVariableForClosure(variable_name)
            else:
                return ExpressionOutlineFunctionBase.getVariableForClosure(
                    self, variable_name=variable_name
                )
        else:
            result = self.provider.getVariableForClosure(variable_name)
            self.taken.add(result)
            return result

    def getDeferredClassDictVariable(self):
        if self.deferred_class_dict is None:
            self.deferred_class_dict = self.getLocalsScope().getLocalVariable(
                owner=self,
                variable_name="classdict$",
            )
            self.getLocalsScope().registerProvidedVariable(self.deferred_class_dict)

        return self.deferred_class_dict

    @staticmethod
    def markAsDirectlyCalled():
        pass

    def getChildQualname(self, function_name):
        return self.getFunctionQualname() + "." + function_name

    @staticmethod
    def mayHaveSideEffects():
        return False

    def mayRaiseException(self, exception_type):
        return self.subnode_body.mayRaiseException(exception_type)

    def isUnoptimized(self):
        return True


class ExpressionClassBodyQualnameSetupMixin(object):
    """Mixin for class bodies whose '__qualname__' assignment must follow clones."""

    __slots__ = ()

    def _copyClassBodyQualnameSetup(self, result):
        if self.qualname_setup is not None:
            class_variable_name, qualname_assign = self.qualname_setup
            result.qualname_setup = (
                class_variable_name,
                _translateClonedDescendant(
                    old_root=self, new_root=result, target_node=qualname_assign
                ),
            )


class ExpressionClassMappingBody(
    MarkNeedsAnnotationsMixin,
    ExpressionClassBodyQualnameSetupMixin,
    ExpressionClassBodyBase,
):
    """Python 3 class body whose namespace may be an arbitrary mapping."""

    kind = "EXPRESSION_CLASS_MAPPING_BODY"

    __slots__ = (
        "needs_annotations_dict",
        "qualname_setup",
        "static_attributes",
        "deferred_annotations",
    )

    locals_kind = "python_mapping_class"

    def __init__(self, provider, name, doc, source_ref, body=None, flags=None):
        ExpressionClassBodyBase.__init__(
            self,
            provider=provider,
            name=name,
            doc=doc,
            body=body,
            flags=flags,
            source_ref=source_ref,
        )

        MarkNeedsAnnotationsMixin.__init__(self)

        self.qualname_setup = None
        self.static_attributes = OrderedSet() if python_version >= 0x3D0 else None
        self.deferred_annotations = []

    def _copyClassBodyCloneState(self, result, variable_translations):
        ExpressionClassBodyBase._copyClassBodyCloneState(
            self, result=result, variable_translations=variable_translations
        )

        result.needs_annotations_dict = self.needs_annotations_dict

        self._copyClassBodyQualnameSetup(result=result)

        if self.static_attributes is not None:
            result.static_attributes = OrderedSet(self.static_attributes)

        result.deferred_annotations = list(self.deferred_annotations)

    def addStaticAttribute(self, static_attribute):
        self.static_attributes.add(static_attribute)

    def getStaticAttributes(self):
        return tuple(self.static_attributes)


class ExpressionClassDictBodyP2(ExpressionDictShapeExactMixin, ExpressionClassBodyBase):
    kind = "EXPRESSION_CLASS_DICT_BODY_P2"

    __slots__ = ()

    locals_kind = "python_dict_class"

    def __init__(self, provider, name, doc, source_ref, body=None, flags=None):
        ExpressionClassBodyBase.__init__(
            self,
            provider=provider,
            name=name,
            doc=doc,
            body=body,
            flags=flags,
            source_ref=source_ref,
        )


class ExpressionClassDictBody(  # pylint: disable=too-many-ancestors
    MarkNeedsAnnotationsMixin,
    ExpressionClassBodyQualnameSetupMixin,
    ExpressionClassDictBodyP2,
):
    """Python 3 class body whose namespace is known to be an exact dict."""

    kind = "EXPRESSION_CLASS_DICT_BODY"

    __slots__ = ("needs_annotations_dict", "qualname_setup")

    def __init__(self, provider, name, doc, source_ref, body=None, flags=None):
        ExpressionClassDictBodyP2.__init__(
            self,
            provider=provider,
            name=name,
            doc=doc,
            body=body,
            flags=flags,
            source_ref=source_ref,
        )

        MarkNeedsAnnotationsMixin.__init__(self)

        self.qualname_setup = None

    def _copyClassBodyCloneState(self, result, variable_translations):
        ExpressionClassDictBodyP2._copyClassBodyCloneState(
            self, result=result, variable_translations=variable_translations
        )

        result.needs_annotations_dict = self.needs_annotations_dict

        self._copyClassBodyQualnameSetup(result=result)


class ExpressionClassDictFromClass(ExpressionBase):
    """The dictionary of a created class for annotation scopes.

    This is only for the case of the created object being a class, the rare
    case of a metaclass returning something that is not a class, is handled
    by using the prepared class namespace instead.
    """

    kind = "EXPRESSION_CLASS_DICT_FROM_CLASS"

    __slots__ = ("variable",)

    def __init__(self, variable, source_ref):
        ExpressionBase.__init__(self, source_ref)

        self.variable = variable

    def finalize(self):
        del self.parent
        del self.variable

    def getDetails(self):
        return {
            "variable": self.variable,
        }

    def setVariable(self, variable):
        self.variable = variable

    def computeExpressionRaw(self, trace_collection):
        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        return False


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

    @staticmethod
    def isExpressionBuiltinCall():
        return True

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
        # TODO: Specialize to a dedicated class creation node with compile-time
        # metaclass selection via _calculateMetaClass() when bases and dict
        # allow it.
        if self.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionCallMetaclass(ExpressionCallMetaclassBase):
    kind = "EXPRESSION_CALL_METACLASS"

    named_children = ("metaclass", "name", "bases", "dict_arg", "class_decl_dict")
    node_attributes = ("class_variable",)

    def getClassVariable(self):
        return self.class_variable

    def setClassVariable(self, variable):
        # pylint: disable=I0021,attribute-defined-outside-init
        self.class_variable = variable

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return True


class ExpressionCallClassPrepareCommonBase(ExpressionCallClassPrepareBase):
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
