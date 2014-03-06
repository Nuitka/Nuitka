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
""" This module maintains the parameter specification classes.

These are used for function, lambdas, generators. They are also a factory
for the respective variable objects. One of the difficulty of Python and
its parameter parsing is that they are allowed to be nested like this:

(a,b), c

Much like in assignments, which are very similar to parameters, except
that parameters may also be assigned from a dictionary, they are no less
flexible.

"""

class TooManyArguments(Exception):
    def __init__(self, real_exception):
        Exception.__init__( self )

        self.real_exception = real_exception

    def getRealException(self):
        return self.real_exception


from nuitka import Variables, Utils

class ParameterSpecTuple:
    def __init__(self, normal_args, nest_count = 1):
        self.normal_args = tuple( normal_args )
        self.nest_count = nest_count

        self.owner = None
        self.normal_variables = None

    def getNormalParameters(self):
        return self.normal_variables

    def setOwner(self, owner):
        assert self.owner is None

        self.owner = owner

        self.normal_variables = []

        for count, normal_arg in enumerate( self.normal_args ):
            if type( normal_arg ) == str:
                normal_variable = Variables.ParameterVariable(
                    owner          = self.owner,
                    parameter_name = normal_arg,
                    kw_only        = False
                )
            elif type( normal_arg ) == tuple:
                sub_parameter_spec = ParameterSpecTuple(
                    normal_args = normal_arg,
                    nest_count  = self.nest_count + 1
                )
                sub_parameter_spec.setOwner( self.owner )

                sub_parameter_name = "Unpackable_%s_%s" % (
                    self.nest_count,
                    count+1
                )

                normal_variable = Variables.NestedParameterVariable(
                    owner          = self.owner,
                    parameter_name = sub_parameter_name,
                    parameter_spec = sub_parameter_spec
                )
            else:
                assert False, normal_arg

            self.normal_variables.append( normal_variable )


    def getVariables(self):
        result = []

        for variable in self.normal_variables:
            if variable.isNestedParameterVariable():
                result += variable.getVariables()
            else:
                result.append( variable )

        return result

    def hasNestedParameterVariables(self):
        for variable in self.normal_variables:
            if variable.isNestedParameterVariable():
                return True
        else:
            return False

    def getAllVariables(self):
        result = self.normal_variables[:]

        for variable in self.normal_variables:
            if variable.isNestedParameterVariable():
                result += variable.getAllVariables()

        return result

    def getAllNames(self):
        result = []

        def extractArg(normal_arg):
            if type( normal_arg ) is str:
                result.append( normal_arg )
            elif type( normal_arg ) is tuple:
                for normal_arg in normal_arg:
                    extractArg( normal_arg )
            else:
                assert False

        for normal_arg in self.normal_args:
            extractArg( normal_arg )

        return result

    def getTopLevelVariables(self):
        return self.normal_variables

    def getParameterNames(self):
        return Variables.getNames( self.getVariables() )


class ParameterSpec(ParameterSpecTuple):
    def __init__( self, name, normal_args, kw_only_args, list_star_arg,
                  dict_star_arg, default_count ):
        assert None not in normal_args

        self.name = name

        self.nest_count = 1

        ParameterSpecTuple.__init__( self, normal_args )

        assert list_star_arg is None or type( list_star_arg ) is str, \
          list_star_arg
        assert dict_star_arg is None or type( dict_star_arg ) is str, \
          dict_star_arg

        self.list_star_arg = list_star_arg
        self.dict_star_arg = dict_star_arg

        self.list_star_variable = None
        self.dict_star_variable = None

        self.default_count = default_count

        self.kw_only_args = tuple( kw_only_args )
        self.kw_only_variables = None

    def checkValid(self):
        arg_names = self.getAllNames()

        # Check for duplicate arguments, could happen.
        for arg_name in arg_names:
            if arg_names.count( arg_name ) != 1:
                return "duplicate argument '%s' in function definition" % arg_name
        else:
            return None

    def __repr__(self):
        parts = [ str(normal_arg) for normal_arg in self.normal_args ]

        if self.list_star_arg is not None:
            parts.append( "*%s" % self.list_star_arg )

        if self.dict_star_variable is not None:
            parts.append( "**%s" % self.dict_star_variable )

        if parts:
            return "<ParameterSpec '%s'>" % ",".join( parts )
        else:
            return "<NoParameters>"

    def getArgumentCount(self):
        return len( self.normal_args )

    def setOwner(self, owner):
        if self.owner is not None:
            return

        ParameterSpecTuple.setOwner( self, owner )

        if self.list_star_arg:
            self.list_star_variable = Variables.ParameterVariable( owner, self.list_star_arg, False )
        else:
            self.list_star_variable = None

        if self.dict_star_arg:
            self.dict_star_variable = Variables.ParameterVariable(
                owner          = owner,
                parameter_name = self.dict_star_arg,
                kw_only        = False
            )
        else:
            self.dict_star_variable = None

        self.kw_only_variables = [
            Variables.ParameterVariable( self.owner, kw_only_arg, True )
            for kw_only_arg in
            self.kw_only_args
        ]

    def isEmpty(self):
        return len( self.normal_args ) == 0 and self.list_star_arg is None and \
               self.dict_star_arg is None and len( self.kw_only_args ) == 0

    def getDefaultParameterVariables(self):
        result = ParameterSpecTuple.getTopLevelVariables( self )

        return result[ len( self.normal_args ) - self.default_count : ]

    def getDefaultParameterNames(self):
        return self.normal_args[ \
            len( self.normal_args ) - self.default_count : ]

    def getDefaultCount(self):
        return self.default_count

    def hasDefaultParameters(self):
        return self.getDefaultCount() > 0

    def getVariables(self):
        result = ParameterSpecTuple.getVariables( self )[:]

        if self.list_star_variable is not None:
            result.append( self.list_star_variable )

        if self.dict_star_variable is not None:
            result.append( self.dict_star_variable )

        return result + self.kw_only_variables

    def getTopLevelVariables(self):
        result = ParameterSpecTuple.getTopLevelVariables( self )

        return result + self.kw_only_variables

    def getAllVariables(self):
        result = ParameterSpecTuple.getAllVariables( self )[:]

        if self.list_star_variable is not None:
            result.append( self.list_star_variable )

        if self.dict_star_variable is not None:
            result.append( self.dict_star_variable )

        return result + self.kw_only_variables

    def getAllNames(self):
        result = ParameterSpecTuple.getAllNames( self )[:]

        if self.list_star_arg is not None:
            result.append( self.list_star_arg )

        if self.dict_star_arg is not None:
            result.append( self.dict_star_arg )

        return result + list( self.kw_only_args )

    def getStarListArgumentName(self):
        return self.list_star_arg

    def getListStarArgVariable(self):
        return self.list_star_variable

    def getStarDictArgumentName(self):
        return self.dict_star_arg

    def getDictStarArgVariable(self):
        return self.dict_star_variable

    def getKwOnlyVariables(self):
        return self.kw_only_variables

    def allowsKeywords(self):
        # Abstract method, pylint: disable=R0201
        return True

    def getKeywordRefusalText(self):
        return "%s() takes no keyword arguments" % self.name

    def getArgumentNames(self):
        return self.normal_args

    def getKwOnlyParameterNames(self):
        return self.kw_only_args

    def getKwOnlyParameterCount(self):
        return len( self.kw_only_args )

    def getCoArgNames(self):
        result = []

        for count, variable in enumerate( self.getTopLevelVariables() ):
            if variable.isNestedParameterVariable():
                result.append( ".%d" % count )
            else:
                result.append( variable.getName() )

        if self.list_star_variable is not None:
            result.append( self.list_star_arg )

        if self.dict_star_variable is not None:
            result.append( self.dict_star_arg )

        return result


# Note: Based loosley on "inspect.getcallargs" with corrections.
def matchCall(func_name, args, star_list_arg, star_dict_arg, num_defaults, positional, pairs, improved = False ):
    # This is of incredible code complexity, but there really is no other way to
    # express this with less statements, branches, or variables.
    # pylint: disable=R0914,R0912,R0915

    assert type( positional ) is tuple
    assert type( pairs ) in ( tuple, list )

    # Make a copy, we are going to modify it.
    pairs = list( pairs )

    result = {}

    assigned_tuple_params = []

    def assign(arg, value):
        if type( arg ) is str:
            # Normal case:
            result[ arg ] = value
        else:
            # Tuple argument case:

            assigned_tuple_params.append( arg )
            value = iter( value )

            for i, subarg in enumerate( arg ):
                try:
                    subvalue = next( value )
                except StopIteration:
                    raise TooManyArguments(
                        ValueError(
                            "need more than %d %s to unpack" % (
                                i,
                                "values" if i > 1 else "value"
                            )
                        )
                    )

                # Recurse into tuple argument values, could be more tuples.
                assign( subarg, subvalue )

            # Check that not too many values we provided.
            try:
                next( value )
            except StopIteration:
                pass
            else:
                raise TooManyArguments(
                    ValueError( "too many values to unpack" )
                )

    def isAssigned(arg):
        if type( arg ) is str:
            return arg in result

        return arg in assigned_tuple_params

    num_pos = len( positional )
    num_total = num_pos + len( pairs )
    num_args = len( args )

    for arg, value in zip( args, positional ):
        assign( arg, value )

    # Python3 does this check earlier.
    if Utils.python_version >= 300 and not star_dict_arg:
        for pair in pairs:
            if pair[0] not in args:
                message = "'%s' is an invalid keyword argument for this function" % pair[0]

                raise TooManyArguments(
                    TypeError( message )
                )

    if star_list_arg:
        if num_pos > num_args:
            assign( star_list_arg, positional[ -(num_pos-num_args) : ] )
        else:
            assign( star_list_arg, () )
    elif 0 < num_args < num_total:
        if num_defaults == 0:
            if num_args != 1:
                raise TooManyArguments(
                    TypeError(
                        "%s expected %d arguments, got %d" % (
                            func_name,
                            num_args,
                            num_total
                        )
                    )
                )

            raise TooManyArguments(
                TypeError(
                    "%s() takes exactly %s (%d given)" % (
                        func_name,
                        "one argument" if num_args == 1 else "%d arguments" % num_args,
                        num_total
                    )
                )
            )
        else:
            raise TooManyArguments(
                TypeError(
                    "%s() takes at most %d %s (%d given)" % (
                        func_name,
                        num_args,
                        "argument" if num_args == 1 else "arguments",
                        num_total
                    )
                )
            )
    elif num_args == 0 and num_total:
        if star_dict_arg:
            if num_pos:
                # Could use num_pos, but Python also uses num_total.
                raise TooManyArguments(
                    TypeError(
                        "%s() takes exactly 0 arguments (%d given)" % (
                            func_name,
                            num_total
                        )
                    )
                )
        else:
            raise TooManyArguments(
                TypeError(
                    "%s() takes no arguments (%d given)" % (
                        func_name,
                        num_total
                    )
                )
            )

    named_argument_names = [
        pair[0]
        for pair in
        pairs
    ]

    for arg in args:
        if type( arg ) is str and arg in named_argument_names:
            if isAssigned( arg ):
                raise TooManyArguments(
                    TypeError(
                        "%s() got multiple values for keyword argument '%s'" % (
                            func_name,
                            arg
                        )
                    )
                )
            else:
                new_pairs = []

                for pair in pairs:
                    if arg == pair[0]:
                        assign( arg, pair[1] )
                    else:
                        new_pairs.append( pair )

                assert len( new_pairs ) == len( pairs ) - 1

                pairs = new_pairs

    # Fill in any missing values with the None to indicate "default".
    if num_defaults > 0:
        for arg in args[ -num_defaults : ]:
            if not isAssigned( arg ):
                assign( arg, None )

    if star_dict_arg:
        assign( star_dict_arg, pairs )
    elif pairs:
        unexpected = next( iter( dict( pairs ) ) )

        if improved:
            message = "%s() got an unexpected keyword argument '%s'" % (
                func_name,
                unexpected
            )
        else:
            message = "'%s' is an invalid keyword argument for this function" % unexpected

        raise TooManyArguments(
            TypeError( message )
        )

    unassigned = num_args - len(
        [
            arg
            for arg in args
            if isAssigned( arg )
        ]
    )

    if unassigned:
        num_required = num_args - num_defaults

        if num_required > 0 or improved:
            if num_defaults == 0 and num_args != 1:
                raise TooManyArguments(
                    TypeError(
                        "%s expected %d arguments, got %d" % (
                            func_name,
                            num_args,
                            num_total
                        )
                    )
                )

            if num_required == 1:
                arg_desc = "1 argument"
            else:
                arg_desc = "%d arguments" % num_required

            raise TooManyArguments(
                TypeError(
                    "%s() takes %s %s (%d given)" % (
                        func_name,
                        "at least" if num_defaults > 0 else "exactly",
                        arg_desc,
                        num_total
                    )
                )
            )
        else:
            raise TooManyArguments(
                TypeError(
                    "%s expected %s%s, got %d" % (
                        func_name,
                        ( "at least " if Utils.python_version < 300 else "" )
                            if num_defaults > 0
                        else "exactly ",
                        "%d arguments" % num_required,
                        num_total
                    )
                )
            )

    return result
