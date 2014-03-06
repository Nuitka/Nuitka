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
""" Slice nodes.

Slices are important when working with lists. Tracking them can allow to achieve more
compact code, or predict results at compile time.

There will be a method "computeExpressionSlice" to aid predicting them.
"""

from .NodeBases import ExpressionChildrenHavingBase
from .NodeMakingHelpers import convertNoneConstantToNone


class ExpressionSliceLookup(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SLICE_LOOKUP"

    named_children = (
        "expression",
        "lower",
        "upper"
    )

    checkers   = {
        "upper" : convertNoneConstantToNone,
        "lower" : convertNoneConstantToNone
    }

    def __init__(self, expression, lower, upper, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression,
                "upper"      : upper,
                "lower"      : lower
            },
            source_ref = source_ref
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter( "expression" )

    getLower = ExpressionChildrenHavingBase.childGetter("lower")
    setLower = ExpressionChildrenHavingBase.childSetter("lower")

    getUpper = ExpressionChildrenHavingBase.childGetter("upper")
    setUpper = ExpressionChildrenHavingBase.childSetter("upper")

    def computeExpression(self, constraint_collection):
        lookup_source = self.getLookupSource()

        return lookup_source.computeExpressionSlice(
            lookup_node           = self,
            lower                 = self.getLower(),
            upper                 = self.getUpper(),
            constraint_collection = constraint_collection
        )

    def isKnownToBeIterable(self, count):
        # TODO: Should ask SlicetRegistry
        return None


class ExpressionSliceObject(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SLICE_OBJECT"

    named_children = ( "lower", "upper", "step" )

    def __init__(self, lower, upper, step, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "upper"      : upper,
                "lower"      : lower,
                "step"       : step
            },
            source_ref = source_ref
        )

    getLower = ExpressionChildrenHavingBase.childGetter( "lower" )
    getUpper = ExpressionChildrenHavingBase.childGetter( "upper" )
    getStep  = ExpressionChildrenHavingBase.childGetter( "step" )

    def computeExpression(self, constraint_collection):
        # TODO: Not much to do, potentially simplify to slice instead?
        return self, None, None
