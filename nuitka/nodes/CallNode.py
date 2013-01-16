#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Call node

Function calls and generally calling expressions are the same thing. This is very
important, because it allows to predict most things, and avoid expensive operations like
parameter parsing at run time.

There will be a method "computeNodeCall" to aid predicting them.
"""

from .NodeBases import CPythonExpressionChildrenHavingBase

from .ConstantRefNode import CPythonExpressionConstantRef

class CPythonExpressionCallBase( CPythonExpressionChildrenHavingBase ):
    def __init__( self, called, values, source_ref ):
        assert called.isExpression()

        values[ "called" ] = called

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = values,
            source_ref = source_ref
        )

    getCalled = CPythonExpressionChildrenHavingBase.childGetter( "called" )
    setCalled = CPythonExpressionChildrenHavingBase.childSetter( "called" )

    def getPositionalArguments( self ):
        return ()

    def setPositionalArguments( self, value ):
        assert self.hasChild( "positional_args" )

        self.setChild( "positional_args", tuple( value ) )

    def getNamedArgumentPairs( self ):
        return ()

    def setNamedArgumentPairs( self, value ):
        assert self.hasChild( "pairs" )

        self.setChild( "pairs", tuple( value ) )

    def getStarListArg( self ):
        return None

    def setStarListArg( self, value ):
        assert self.hasChild( "list_star_arg" )

        self.setChild( "list_star_arg", value )

    def getStarDictArg( self ):
        return None

    def setStarDictArg( self, value ):
        assert self.hasChild( "dictl_star_arg" )

        self.setChild( "dict_star_arg", value )

    def isEmptyCall( self ):
        return not self.getPositionalArguments() and not self.getNamedArgumentPairs() and \
               not self.getStarListArg() and not self.getStarDictArg()

    def hasOnlyPositionalArguments( self ):
        return not self.getNamedArgumentPairs() and not self.getStarListArg() and \
               not self.getStarDictArg()

    def hasOnlyConstantArguments( self ):
        for positional_arg in self.getPositionalArguments():
            if not positional_arg.isExpressionConstantRef():
                return False

        for pair in self.getNamedArgumentPairs():
            if not pair.getKey().isExpressionConstantRef():
                return False

            if not pair.getValue().isExpressionConstantRef():
                return False

        list_star_arg = self.getStarListArg()

        if list_star_arg is not None and not list_star_arg.isExpressionConstantRef():
            return False

        dict_star_arg = self.getStarDictArg()

        if dict_star_arg is not None and not dict_star_arg.isExpressionConstantRef():
            return False

        return True

    def computeNode( self, constraint_collection ):
        star_list_arg = self.getStarListArg()

        if star_list_arg is not None:
            if star_list_arg.isExpressionMakeSequence():
                positional_args = self.getPositionalArguments()

                self.setPositionalArguments( positional_args + star_list_arg.getElements() )
                self.setStarListArg( None )
            elif star_list_arg.isExpressionConstantRef():
                if star_list_arg.isKnownToBeIterable( count = None ):
                    positional_args = self.getPositionalArguments()

                    constant_nodes = []

                    for constant in star_list_arg.getConstant():
                        constant_nodes.append(
                            CPythonExpressionConstantRef(
                                constant   = constant,
                                source_ref = star_list_arg.getSourceReference()
                            )
                        )

                    self.setPositionalArguments( positional_args + tuple( constant_nodes ) )
                    self.setStarListArg( None )

            star_dict_arg = self.getStarDictArg()

            if star_dict_arg is not None:
                if star_dict_arg.isExpressionMakeDict():
                    # TODO: Need to cleanup the named argument mess before it is possible.
                    pass
                elif star_dict_arg.isExpressionConstantRef():
                    # TODO: Need to cleanup the named argument mess before it is possible.
                    pass

        star_dict_arg = self.getStarDictArg()

        if star_list_arg is None and star_dict_arg is None and not self.isExpressionCallSimple():
            source_ref = self.getSourceReference()

            simple_call = CPythonExpressionCallSimple(
                called          = self.getCalled(),
                positional_args = self.getPositionalArguments(),
                pairs           = self.getNamedArgumentPairs(),
                source_ref      = source_ref
            )

            return simple_call, "new_expression", "Complex call downgraded so simple call"

        # TODO: This node is dying.
        return self, None, None

        called = self.getCalled()

        return called.computeNodeCall(
            call_node             = self,
            constraint_collection = constraint_collection
        )

    def isKnownToBeIterable( self, count ):
        # Virtual method and unpredicted calls are unknown if they can be iterated at all,
        # pylint: disable=R0201,W0613
        return None

    def extractPreCallSideEffects( self ):
        """ Dedicated method that a "called" can use to extract all side effects.

        It's all but itself and the actual calling process.
        """
        result = []

        for pos_arg in self.getPositionalArguments():
            result.extend( pos_arg.extractSideEffects() )

        for pair in self.getNamedArgumentPairs():
            result.extend( pair.getValue().extractSideEffects() )

        star_list_arg = self.getStarListArg()

        if star_list_arg is not None:
            result.extend( star_list_arg.extractSideEffects() )

        star_dict_arg = self.getStarDictArg()

        if star_dict_arg is not None:
            result.extend( star_dict_arg.extractSideEffects() )

        return result


class CPythonExpressionCallComplex( CPythonExpressionCallBase ):
    kind = "EXPRESSION_CALL_COMPLEX"

    named_children = ( "called", "positional_args", "pairs", "list_star_arg", "dict_star_arg" )

    def __init__( self, called, positional_args, pairs, list_star_arg, dict_star_arg, source_ref ):
        assert called.isExpression()

        for positional_arg in positional_args:
            assert positional_arg.isExpression()

        assert type( pairs ) in ( list, tuple ), pairs

        for pair in pairs:
            assert pair.isExpressionKeyValuePair()

        CPythonExpressionCallBase.__init__(
            self,
            called     = called,
            values     = {
                "positional_args" : tuple( positional_args ),
                "pairs"           : tuple( pairs ),
                "list_star_arg"   : list_star_arg,
                "dict_star_arg"   : dict_star_arg
            },
            source_ref = source_ref
        )

    getPositionalArguments = CPythonExpressionChildrenHavingBase.childGetter( "positional_args" )
    getNamedArgumentPairs = CPythonExpressionChildrenHavingBase.childGetter( "pairs" )
    getStarListArg = CPythonExpressionChildrenHavingBase.childGetter( "list_star_arg" )
    getStarDictArg = CPythonExpressionChildrenHavingBase.childGetter( "dict_star_arg" )


class CPythonExpressionCallSimple( CPythonExpressionCallBase ):
    kind = "EXPRESSION_CALL_SIMPLE"

    named_children = ( "called", "positional_args", "pairs" )

    def __init__( self, called, positional_args, pairs, source_ref ):
        assert called.isExpression()

        for positional_arg in positional_args:
            assert positional_arg.isExpression()

        assert type( pairs ) in ( list, tuple ), pairs

        for pair in pairs:
            assert pair.isExpressionKeyValuePair()

        CPythonExpressionCallBase.__init__(
            self,
            called     = called,
            values     = {
                "positional_args" : tuple( positional_args ),
                "pairs"           : tuple( pairs ),
            },
            source_ref = source_ref
        )

    getPositionalArguments = CPythonExpressionChildrenHavingBase.childGetter( "positional_args" )
    getNamedArgumentPairs = CPythonExpressionChildrenHavingBase.childGetter( "pairs" )


class CPythonExpressionCallRaw( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_CALL_RAW"

    named_children = ( "called", "args", "kw" )

    def __init__( self, called, args, kw, source_ref ):
        assert called.isExpression()
        assert args.isExpression()
        assert kw.isExpression()

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "called" : called,
                "args"   : args,
                "kw"     : kw,
            },
            source_ref = source_ref
        )

    getCalled = CPythonExpressionChildrenHavingBase.childGetter( "called" )
    getCallArgs = CPythonExpressionChildrenHavingBase.childGetter( "args" )
    getCallKw = CPythonExpressionChildrenHavingBase.childGetter( "kw" )

    def isExpressionCall( self ):
        return True

    def computeNode( self, constraint_collection ):
        return self.getCalled().computeNodeCall(
            call_node             = self,
            constraint_collection = constraint_collection
        )

    def extractPreCallSideEffects( self ):
        args = self.getCallArgs()
        kw = self.getCallKw()

        return args.extractSideEffects() + kw.extractSideEffects()


class CPythonExpressionCallNoKeywords( CPythonExpressionCallRaw ):
    kind = "EXPRESSION_CALL_NO_KEYWORDS"

    named_children = ( "called", "args", "kw" )

    def __init__( self, called, args, source_ref ):
        assert called.isExpression()

        CPythonExpressionCallRaw.__init__(
            self,
            called = called,
            args   = args,
            kw     = CPythonExpressionConstantRef(
                constant   = {},
                source_ref = source_ref,
            ),
            source_ref = source_ref
        )


class CPythonExpressionCallEmpty( CPythonExpressionCallRaw ):
    kind = "EXPRESSION_CALL_EMPTY"

    named_children = ( "called", "args", "kw" )

    def __init__( self, called, source_ref ):
        assert called.isExpression()

        CPythonExpressionCallRaw.__init__(
            self,
            called = called,
            args   = CPythonExpressionConstantRef(
                constant   = (),
                source_ref = source_ref
            ),
            kw     = CPythonExpressionConstantRef(
                constant   = {},
                source_ref = source_ref,
            ),
            source_ref = source_ref
        )
