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
""" The type1 node.

This one just determines types. It's great for optimization. We may be able to
predict its value, but knowing it. In that case, we have a built-in name
reference for that type to convert to, or when checking the result of it, we
will then know it's limited after the fact.

"""

from nuitka.Builtins import builtin_names

from .BuiltinRefNodes import (
    ExpressionBuiltinAnonymousRef,
    ExpressionBuiltinRef,
    makeExpressionBuiltinRef,
)
from .ExpressionBases import (
    ExpressionBuiltinSingleArgBase,
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
)
from .ExpressionShapeMixins import ExpressionBoolShapeExactMixin
from .NodeBases import SideEffectsFromChildrenMixin
from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects
from .shapes.BuiltinTypeShapes import tshape_type


class ExpressionBuiltinType1(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_TYPE1"

    def computeExpression(self, trace_collection):
        value = self.subnode_value

        type_shape = value.getTypeShape()

        if type_shape is not None:
            type_name = type_shape.getTypeName()

            if type_name is not None and type_name in __builtins__:
                result = ExpressionBuiltinRef(
                    builtin_name=type_name, source_ref=value.getSourceReference()
                )

                result = wrapExpressionWithNodeSideEffects(
                    new_node=result, old_node=value
                )

                return (
                    result,
                    "new_builtin",
                    "Replaced predictable type lookup with builtin type '%s'."
                    % (type_name),
                )

        if value.isCompileTimeConstant():
            # The above code is supposed to catch these in a better way.
            value = value.getCompileTimeConstant()

            type_name = value.__class__.__name__

            if type_name in builtin_names:
                new_node = makeExpressionBuiltinRef(
                    builtin_name=type_name,
                    locals_scope=None,
                    source_ref=self.source_ref,
                )
            else:
                new_node = ExpressionBuiltinAnonymousRef(
                    builtin_name=type_name, source_ref=self.source_ref
                )

            return (
                new_node,
                "new_builtin",
                "Replaced predictable type lookup with builtin type '%s'."
                % (type_name),
            )

        return self, None, None

    @staticmethod
    def getTypeShape():
        return tshape_type

    def computeExpressionDrop(self, statement, trace_collection):
        from .NodeMakingHelpers import (
            makeStatementExpressionOnlyReplacementNode,
        )

        result = makeStatementExpressionOnlyReplacementNode(
            expression=self.subnode_value, node=statement
        )

        return (
            result,
            "new_statements",
            """\
Removed type taking for unused result.""",
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(exception_type)

    def mayHaveSideEffects(self):
        return self.subnode_value.mayHaveSideEffects()


class ExpressionBuiltinSuper2(ExpressionChildrenHavingBase):
    """Two arguments form of super."""

    kind = "EXPRESSION_BUILTIN_SUPER2"

    named_children = ("type_arg", "object_arg")

    def __init__(self, type_arg, object_arg, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"type_arg": type_arg, "object_arg": object_arg},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Quite some cases should be possible to predict.
        return self, None, None


class ExpressionBuiltinSuper0(ExpressionChildrenHavingBase):
    """Python3 form of super, arguments determined from cells and function arguments."""

    kind = "EXPRESSION_BUILTIN_SUPER0"

    named_children = ("type_arg", "object_arg")

    def __init__(self, type_arg, object_arg, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"type_arg": type_arg, "object_arg": object_arg},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Quite some cases should be possible to predict.
        return self, None, None


class ExpressionBuiltinIsinstance(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_ISINSTANCE"

    named_children = ("instance", "classes")

    def __init__(self, instance, classes, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"instance": instance, "classes": classes},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Quite some cases should be possible to predict.

        instance = self.subnode_instance

        # TODO: Should be possible to query run time type instead, but we don't
        # have that method yet. Later this will be essential.
        if not instance.isCompileTimeConstant():
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        classes = self.subnode_classes

        if not classes.isCompileTimeConstant():
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        # So if both are compile time constant, we are able to compute it.
        return trace_collection.getCompileTimeComputationResult(
            node=self,
            computation=lambda: isinstance(
                instance.getCompileTimeConstant(), classes.getCompileTimeConstant()
            ),
            description="Built-in call to 'isinstance' computed.",
        )


class ExpressionBuiltinIssubclass(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_ISSUBCLASS"

    named_children = ("cls", "classes")

    def __init__(self, cls, classes, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"cls": cls, "classes": classes},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Quite some cases should be possible to predict.

        cls = self.subnode_cls

        # TODO: Should be possible to query run time type instead, but we don't
        # have that method yet. Later this will be essential.
        if not cls.isCompileTimeConstant():
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        classes = self.subnode_classes

        if not classes.isCompileTimeConstant():
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        # So if both are compile time constant, we are able to compute it.
        return trace_collection.getCompileTimeComputationResult(
            node=self,
            computation=lambda: issubclass(
                cls.getCompileTimeConstant(), classes.getCompileTimeConstant()
            ),
            description="Built-in call to 'issubclass' computed.",
        )


class ExpressionTypeCheck(
    ExpressionBoolShapeExactMixin,
    SideEffectsFromChildrenMixin,
    ExpressionChildHavingBase,
):
    kind = "EXPRESSION_TYPE_CHECK"

    named_child = "cls"

    def __init__(self, cls, source_ref):
        ExpressionChildHavingBase.__init__(
            self,
            value=cls,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Quite some cases should be possible to predict, but I am not aware of
        # 100% true Python equivalent at this time.
        return self, None, None
