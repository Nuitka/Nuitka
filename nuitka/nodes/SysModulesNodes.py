#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nodes for "sys.modules" operations.

The nodes exist in every compilation mode. For a statically resolved included
module, the loader entry value is the source of truth, and "sys.modules" is the
public side effect or the fallback for modules without an entry.
"""

from nuitka.__past__ import unicode
from nuitka.utils.ModuleNames import ModuleName, checkModuleName

from .DictionaryNodes import (
    ExpressionDictOperationGet2,
    ExpressionDictOperationGet3,
    ExpressionDictOperationPop2,
    ExpressionDictOperationPop3,
)
from .ExpressionBases import ExpressionBase
from .shapes.BuiltinTypeShapes import tshape_dict
from .SubscriptNodes import (
    ExpressionSubscriptLookup,
    StatementAssignmentSubscript,
    StatementDelSubscript,
)


def _resolveSysModulesModuleName(subscript):
    """Resolve a statically known "sys.modules" key to a module name.

    Args:
        subscript: Node of the subscript or method key.

    Returns:
        ModuleName of the target, or None if the key is not statically known.
    """
    # In module mode, the default runtime name mode keeps "__name__" as a
    # module attribute reference, so constant folding cannot resolve it. The
    # module it belongs to is still known, which is what the loader entry needs.
    if subscript.isExpressionModuleAttributeNameRef():
        return subscript.getVariable().getModule().getFullName()

    if subscript.isCompileTimeConstant():
        value = subscript.getCompileTimeConstant()

        if type(value) in (str, unicode) and checkModuleName(value):
            return ModuleName(value)

    return None


def makeExpressionSysModulesGet2(dict_arg, key, source_ref):
    return ExpressionSysModulesGet2(
        dict_arg=dict_arg,
        key=key,
        module_name=_resolveSysModulesModuleName(subscript=key),
        source_ref=source_ref,
    )


def makeExpressionSysModulesGet3(dict_arg, key, default, source_ref):
    return ExpressionSysModulesGet3(
        dict_arg=dict_arg,
        key=key,
        default=default,
        module_name=_resolveSysModulesModuleName(subscript=key),
        source_ref=source_ref,
    )


def makeExpressionSysModulesPop2(dict_arg, key, source_ref):
    return ExpressionSysModulesPop2(
        dict_arg=dict_arg,
        key=key,
        module_name=_resolveSysModulesModuleName(subscript=key),
        source_ref=source_ref,
    )


def makeExpressionSysModulesPop3(dict_arg, key, default, source_ref):
    return ExpressionSysModulesPop3(
        dict_arg=dict_arg,
        key=key,
        default=default,
        module_name=_resolveSysModulesModuleName(subscript=key),
        source_ref=source_ref,
    )


def makeExpressionSysModulesRef(source_ref):
    return ExpressionSysModulesRef(source_ref=source_ref)


class ExpressionSysModulesRef(ExpressionBase):
    """The "sys.modules" dictionary value."""

    kind = "EXPRESSION_SYS_MODULES_REF"

    __slots__ = ()

    @staticmethod
    def isExpressionSysModulesRef():
        return True

    @staticmethod
    def mayHaveSideEffects():
        return False

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    @staticmethod
    def getDetails():
        return {}

    @staticmethod
    def getTypeShape():
        return tshape_dict

    def finalize(self):
        del self.parent

    def computeExpressionRaw(self, trace_collection):
        return self, None, None

    def computeExpressionSubscript(self, lookup_node, subscript, trace_collection):
        result = ExpressionSysModulesLookup(
            expression=self,
            subscript=subscript,
            module_name=_resolveSysModulesModuleName(subscript=subscript),
            source_ref=lookup_node.getSourceReference(),
        )

        return (
            result,
            "new_expression",
            """\
"sys.modules" subscript lookup recognized.""",
        )

    def computeExpressionSetSubscript(
        self, set_node, subscript, value_node, trace_collection
    ):
        result = StatementAssignmentSysModulesSubscript(
            source=value_node,
            subscribed=self,
            subscript=subscript,
            module_name=_resolveSysModulesModuleName(subscript=subscript),
            source_ref=set_node.getSourceReference(),
        )

        return (
            result,
            "new_statements",
            """\
"sys.modules" subscript assignment recognized.""",
        )

    def computeExpressionDelSubscript(self, del_node, subscript, trace_collection):
        result = StatementDelSysModulesSubscript(
            subscribed=self,
            subscript=subscript,
            module_name=_resolveSysModulesModuleName(subscript=subscript),
            source_ref=del_node.getSourceReference(),
        )

        return (
            result,
            "new_statements",
            """\
"sys.modules" subscript deletion recognized.""",
        )


class ExpressionSysModulesLookup(ExpressionSubscriptLookup):
    """A "sys.modules[subscript]" lookup with a statically known target."""

    kind = "EXPRESSION_SYS_MODULES_LOOKUP"

    __slots__ = ("module_name",)

    def __init__(self, expression, subscript, module_name, source_ref):
        ExpressionSubscriptLookup.__init__(
            self,
            expression=expression,
            subscript=subscript,
            source_ref=source_ref,
        )

        self.module_name = module_name

    def getDetails(self):
        return {"module_name": self.module_name}

    def getModuleName(self):
        if self.module_name is None:
            self.module_name = _resolveSysModulesModuleName(
                subscript=self.subnode_subscript,
            )

        return self.module_name

    def computeExpression(self, trace_collection):
        if self.subnode_subscript.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        # Looking up a dictionary key can run "__hash__" and "__eq__".
        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class _ExpressionSysModulesCallMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    def _initSysModulesCall(self, module_name):
        self.module_name = module_name

    def getDetails(self):
        return {"module_name": self.module_name}

    def getModuleName(self):
        if self.module_name is None:
            self.module_name = _resolveSysModulesModuleName(
                subscript=self.subnode_key,
            )

        return self.module_name


class ExpressionSysModulesGet2(
    _ExpressionSysModulesCallMixin, ExpressionDictOperationGet2
):
    """A "sys.modules.get(key)" call."""

    kind = "EXPRESSION_SYS_MODULES_GET2"

    __slots__ = ("module_name",)

    def __init__(self, dict_arg, key, module_name, source_ref):
        ExpressionDictOperationGet2.__init__(
            self, dict_arg=dict_arg, key=key, source_ref=source_ref
        )

        self._initSysModulesCall(module_name=module_name)


class ExpressionSysModulesGet3(
    _ExpressionSysModulesCallMixin, ExpressionDictOperationGet3
):
    """A "sys.modules.get(key, default)" call."""

    kind = "EXPRESSION_SYS_MODULES_GET3"

    __slots__ = ("module_name",)

    def __init__(self, dict_arg, key, default, module_name, source_ref):
        ExpressionDictOperationGet3.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
            default=default,
            source_ref=source_ref,
        )

        self._initSysModulesCall(module_name=module_name)


class ExpressionSysModulesPop2(
    _ExpressionSysModulesCallMixin, ExpressionDictOperationPop2
):
    """A "sys.modules.pop(key)" call."""

    kind = "EXPRESSION_SYS_MODULES_POP2"

    __slots__ = ("module_name",)

    def __init__(self, dict_arg, key, module_name, source_ref):
        ExpressionDictOperationPop2.__init__(
            self, dict_arg=dict_arg, key=key, source_ref=source_ref
        )

        self._initSysModulesCall(module_name=module_name)

    def needsModuleValueSetter(self):
        return self.getModuleName()

    @staticmethod
    def mayRaiseException(exception_type):
        # The entry variant can raise KeyError even when the key is hashable.
        return True


class ExpressionSysModulesPop3(
    _ExpressionSysModulesCallMixin, ExpressionDictOperationPop3
):
    """A "sys.modules.pop(key, default)" call."""

    kind = "EXPRESSION_SYS_MODULES_POP3"

    __slots__ = ("module_name",)

    def __init__(self, dict_arg, key, default, module_name, source_ref):
        ExpressionDictOperationPop3.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
            default=default,
            source_ref=source_ref,
        )

        self._initSysModulesCall(module_name=module_name)

    def needsModuleValueSetter(self):
        return self.getModuleName()

    @staticmethod
    def mayRaiseException(exception_type):
        # The entry variant can raise KeyError even when the key is hashable.
        return True


class StatementAssignmentSysModulesSubscript(StatementAssignmentSubscript):
    """A "sys.modules[subscript] = value" assignment."""

    kind = "STATEMENT_ASSIGNMENT_SYS_MODULES_SUBSCRIPT"

    __slots__ = ("module_name",)

    def __init__(self, source, subscribed, subscript, module_name, source_ref):
        StatementAssignmentSubscript.__init__(
            self,
            source=source,
            subscribed=subscribed,
            subscript=subscript,
            source_ref=source_ref,
        )

        self.module_name = module_name

    def needsModuleValueSetter(self):
        return self.getModuleName()

    def getDetails(self):
        return {"module_name": self.module_name}

    def getModuleName(self):
        if self.module_name is None:
            self.module_name = _resolveSysModulesModuleName(
                subscript=self.subnode_subscript,
            )

        return self.module_name

    def computeStatementOperation(self, trace_collection):
        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class StatementDelSysModulesSubscript(StatementDelSubscript):
    """A "del sys.modules[subscript]" deletion."""

    kind = "STATEMENT_DEL_SYS_MODULES_SUBSCRIPT"

    __slots__ = ("module_name",)

    def __init__(self, subscribed, subscript, module_name, source_ref):
        StatementDelSubscript.__init__(
            self,
            subscribed=subscribed,
            subscript=subscript,
            source_ref=source_ref,
        )

        self.module_name = module_name

    def needsModuleValueSetter(self):
        return self.getModuleName()

    def getDetails(self):
        return {"module_name": self.module_name}

    def getModuleName(self):
        if self.module_name is None:
            self.module_name = _resolveSysModulesModuleName(
                subscript=self.subnode_subscript,
            )

        return self.module_name

    def computeStatementOperation(self, trace_collection):
        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


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
