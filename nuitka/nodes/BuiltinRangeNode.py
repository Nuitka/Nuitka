#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Node the calls to the 'range' builtin.

This is a rather complex beast as it has many cases, is difficult to know if it's sizable
enough to compute, and there are complex cases, where the bad result of it can be
predicted still, and these are interesting for warnings.

"""

from .NodeBases import (
    CPythonExpressionChildrenHavingBase,
    CPythonSideEffectsFromChildrenMixin,
    CPythonExpressionMixin,
    CPythonNodeBase
)

from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    getComputationResult
)

from nuitka.transform.optimizations import BuiltinOptimization

from nuitka.Utils import python_version

import math

class CPythonExpressionBuiltinRangeBase( CPythonSideEffectsFromChildrenMixin, \
                                         CPythonExpressionChildrenHavingBase ):

    def __init__( self, values, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = values,
            source_ref = source_ref
        )

class CPythonExpressionBuiltinRange0( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_BUILTIN_RANGE0"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__(
            self,
            source_ref = source_ref
        )

    def computeNode( self, constraint_collection ):
        # Intentional to get exception, pylint: disable=W0108
        return getComputationResult(
            node        = self,
            computation = lambda : range(),
            description = "No arg range builtin"
        )

    def getIterationLength( self, constraint_collection ):
        return None

    def canPredictIterationValues( self, constraint_collection ):
        return False

    def getIterationValue( self, element_index, constraint_collection ):
        return None

    def isKnownToBeIterable( self, count ):
        return False


class CPythonExpressionBuiltinRange1( CPythonExpressionBuiltinRangeBase ):
    kind = "EXPRESSION_BUILTIN_RANGE1"

    named_children = ( "low", )

    def __init__( self, low, source_ref ):
        CPythonExpressionBuiltinRangeBase.__init__(
            self,
            values     = {
                "low"  : low,
            },
            source_ref = source_ref
        )

    getLow = CPythonExpressionChildrenHavingBase.childGetter( "low" )

    def computeNode( self, constraint_collection ):
        # TODO: Support Python3 range objects too.
        if python_version >= 300:
            return self, None, None

        given_values = ( self.getLow(), )

        if not BuiltinOptimization.builtin_range_spec.isCompileTimeComputable( given_values ):
            return self, None, None

        return getComputationResult(
            node        = self,
            computation = lambda : BuiltinOptimization.builtin_range_spec.simulateCall( given_values ),
            description = "Builtin call to range precomputed."
        )

    def getIterationLength( self, constraint_collection ):
        low = self.getLow().getIntegerValue( constraint_collection )

        if low is None:
            return None

        return max( 0, low )

    def canPredictIterationValues( self, constraint_collection ):
        return self.getIterationLength( constraint_collection ) is not None

    def getIterationValue( self, element_index, constraint_collection ):
        length = self.getIterationLength( constraint_collection )

        if length is None:
            return None

        if element_index > length:
            return None

        # TODO: Make sure to cast element_index to what CPython will give, for now a
        # downcast will do.
        return makeConstantReplacementNode(
            constant = int( element_index ),
            node     = self
        )

    def isKnownToBeIterable( self, count ):
        return count is None or count == self.getIterationLength()


class CPythonExpressionBuiltinRange2( CPythonExpressionBuiltinRangeBase ):
    kind = "EXPRESSION_BUILTIN_RANGE2"

    named_children = ( "low", "high" )

    def __init__( self, low, high, source_ref ):
        CPythonExpressionBuiltinRangeBase.__init__(
            self,
            values     = {
                "low"  : low,
                "high" : high
            },
            source_ref = source_ref
        )

    getLow  = CPythonExpressionChildrenHavingBase.childGetter( "low" )
    getHigh = CPythonExpressionChildrenHavingBase.childGetter( "high" )

    builtin_spec = BuiltinOptimization.builtin_range_spec

    def computeBuiltinSpec( self, given_values ):
        assert self.builtin_spec is not None, self

        if not self.builtin_spec.isCompileTimeComputable( given_values ):
            return self, None, None

        return getComputationResult(
            node        = self,
            computation = lambda : self.builtin_spec.simulateCall( given_values ),
            description = "Builtin call to %s precomputed." % self.builtin_spec.getName()
        )

    def computeNode( self, constraint_collection ):
        if python_version >= 300:
            return self, None, None

        low  = self.getLow()
        high = self.getHigh()

        return self.computeBuiltinSpec( ( low, high ) )

    def getIterationLength( self, constraint_collection ):
        low  = self.getLow()
        high = self.getHigh()

        low = low.getIntegerValue( constraint_collection )

        if low is None:
            return None

        high = high.getIntegerValue( constraint_collection )

        if high is None:
            return None

        return max( 0, high - low )

    def canPredictIterationValues( self, constraint_collection ):
        return self.getIterationLength( constraint_collection ) is not None

    def getIterationValue( self, element_index, constraint_collection ):
        low  = self.getLow()
        high = self.getHigh()

        low = low.getIntegerValue( constraint_collection )

        if low is None:
            return None

        high = high.getIntegerValue( constraint_collection )

        if high is None:
            return None

        result = low + element_index

        if result >= high:
            return None
        else:
            return makeConstantReplacementNode(
                constant = result,
                node     = self
            )

    def isKnownToBeIterable( self, count ):
        return count is None or count == self.getIterationLength()


class CPythonExpressionBuiltinRange3( CPythonExpressionBuiltinRangeBase ):
    kind = "EXPRESSION_BUILTIN_RANGE3"

    named_children = ( "low", "high", "step" )

    def __init__( self, low, high, step, source_ref ):
        CPythonExpressionBuiltinRangeBase.__init__(
            self,
            values     = {
                "low"  : low,
                "high" : high,
                "step" : step
            },
            source_ref = source_ref
        )

    getLow  = CPythonExpressionChildrenHavingBase.childGetter( "low" )
    getHigh = CPythonExpressionChildrenHavingBase.childGetter( "high" )
    getStep = CPythonExpressionChildrenHavingBase.childGetter( "step" )

    builtin_spec = BuiltinOptimization.builtin_range_spec

    def computeBuiltinSpec( self, given_values ):
        assert self.builtin_spec is not None, self

        if not self.builtin_spec.isCompileTimeComputable( given_values ):
            return self, None, None

        return getComputationResult(
            node        = self,
            computation = lambda : self.builtin_spec.simulateCall( given_values ),
            description = "Builtin call to %s precomputed." % self.builtin_spec.getName()
        )

    def computeNode( self, constraint_collection ):
        if python_version >= 300:
            return self, None, None

        low  = self.getLow()
        high = self.getHigh()
        step = self.getStep()

        return self.computeBuiltinSpec( ( low, high, step ) )

    def getIterationLength( self, constraint_collection ):
        low  = self.getLow()
        high = self.getHigh()
        step = self.getStep()

        low = low.getIntegerValue( constraint_collection )

        if low is None:
            return None

        high = high.getIntegerValue( constraint_collection )

        if high is None:
            return None

        step = step.getIntegerValue( constraint_collection )

        if step is None:
            return None

        # Give up on this, will raise ValueError.
        if step == 0:
            return None

        if low < high:
            if step < 0:
                estimate = 0
            else:
                estimate = math.ceil( float( high - low ) / step )
        else:
            if step > 0:
                estimate = 0
            else:
                estimate = math.ceil( float( high - low ) / step )

        estimate = round( estimate )

        assert not estimate < 0

        return int( estimate )

    def canPredictIterationValues( self, constraint_collection ):
        return self.getIterationLength( constraint_collection ) is not None

    def getIterationValue( self, element_index, constraint_collection ):
        low  = self.getLow().getIntegerValue( constraint_collection )

        if low is None:
            return None

        high = self.getHigh().getIntegerValue( constraint_collection )

        if high is None:
            return None

        step = self.getStep().getIntegerValue( constraint_collection )

        result = low + step * element_index

        if result >= high:
            return None
        else:
            return makeConstantReplacementNode(
                constant = result,
                node     = self
            )

    def isKnownToBeIterable( self, count ):
        return count is None or count == self.getIterationLength()
