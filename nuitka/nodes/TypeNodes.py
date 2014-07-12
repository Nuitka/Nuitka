#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
predict its value, but knowing it. In that case, we have a builtin name
reference for that type to convert to, or when checking the result of it, we
will then know it's limited after the fact.

"""

from nuitka.Builtins import builtin_names

from .NodeBases import (
    ExpressionBuiltinSingleArgBase,
    ExpressionChildrenHavingBase
)


class ExpressionBuiltinType1(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_TYPE1"

    def computeExpression(self, constraint_collection):
        value = self.getValue()

        if value.isCompileTimeConstant():
            value = value.getCompileTimeConstant()

            type_name = value.__class__.__name__

            from .BuiltinRefNodes import (
                ExpressionBuiltinAnonymousRef,
                ExpressionBuiltinRef
            )

            if type_name in builtin_names:
                new_node = ExpressionBuiltinRef(
                    builtin_name = type_name,
                    source_ref   = self.getSourceReference()
                )
            else:
                new_node = ExpressionBuiltinAnonymousRef(
                    builtin_name = type_name,
                    source_ref   = self.getSourceReference()
                )

            return (
                new_node,
                "new_builtin",
                "Replaced predictable type lookup with builtin type '%s'." % (
                    type_name
                )
            )

        return self, None, None

    def computeExpressionDrop(self, statement, constraint_collection):
        from .NodeMakingHelpers import \
          makeStatementExpressionOnlyReplacementNode

        result = makeStatementExpressionOnlyReplacementNode(
            expression = self.getValue(),
            node       = statement
        )

        return result, "new_statements", """\
Removed type taking for unused result."""


class ExpressionBuiltinSuper(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_SUPER"

    named_children = (
        "type",
        "object"
    )

    def __init__(self, super_type, super_object, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "type"   : super_type,
                "object" : super_object

            },
            source_ref = source_ref )

    getType = ExpressionChildrenHavingBase.childGetter("type")
    getObject = ExpressionChildrenHavingBase.childGetter("object")

    def computeExpression(self, constraint_collection):
        # TODO: Quite some cases should be possible to predict.
        return self, None, None


class ExpressionBuiltinIsinstance(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_ISINSTANCE"

    named_children = (
        "instance",
        "cls"
    )

    def __init__(self, instance, cls, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "instance" : instance,
                "cls"      : cls

            },
            source_ref = source_ref )

    getInstance = ExpressionChildrenHavingBase.childGetter( "instance" )
    getCls = ExpressionChildrenHavingBase.childGetter( "cls" )

    def computeExpression(self, constraint_collection):
        # TODO: Quite some cases should be possible to predict.
        return self, None, None

    def mayProvideReference(self):
        # Dedicated code returns "True" or "False" only, which requires no reference,
        # except for rich comparisons, which do.
        return False
