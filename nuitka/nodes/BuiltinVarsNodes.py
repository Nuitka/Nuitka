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
""" Builtin vars node.

Not used much, esp. not in the form with arguments. Maybe used in some meta programming,
and hopefully can be predicted, because at run time, it is hard to support.
"""


from .NodeBases import ExpressionChildrenHavingBase


class ExpressionBuiltinVars(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_VARS"

    named_children = ( "source", )

    def __init__(self, source, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"  : source,
            },
            source_ref = source_ref
        )

    getSource = ExpressionChildrenHavingBase.childGetter( "source" )

    def computeExpression(self, constraint_collection):
        # TODO: Should be possible. pylint: disable=W0613
        return self, None, None
