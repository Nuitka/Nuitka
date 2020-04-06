#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Base class for all C types.

Defines the interface to use by code generation on C types. Different
types then have to overload the class methods.
"""

type_indicators = {
    "PyObject *": "o",
    "PyObject **": "O",
    "struct Nuitka_CellObject *": "c",
    "nuitka_bool": "b",
    "nuitka_ilong": "L",
}


class CTypeBase(object):
    # For overload.
    c_type = None

    @classmethod
    def getTypeIndicator(cls):
        return type_indicators[cls.c_type]

    @classmethod
    def getInitValue(cls, init_from):
        """ Convert to init value for the type. """

        # Need to overload this for each type it is used for, pylint: disable=unused-argument
        assert False, cls.c_type

    @classmethod
    def getVariableInitCode(cls, variable_code_name, init_from):
        init_value = cls.getInitValue(init_from)

        return "%s%s%s = %s;" % (
            cls.c_type,
            " " if cls.c_type[-1] not in "*" else "",
            variable_code_name,
            init_value,
        )

    @classmethod
    def getLocalVariableInitTestCode(cls, value_name, inverted):
        """ Get code to test for uninitialized.

        """

        # Need to overload this for each type it is used for, pylint: disable=unused-argument
        assert False, cls.c_type

    @classmethod
    def emitVariableAssignCode(
        cls, value_name, needs_release, tmp_name, ref_count, in_place, emit, context
    ):
        """ Get code to assign local variable.

        """

        # Need to overload this for each type it is used for, pylint: disable=unused-argument
        assert False, cls.c_type

    @classmethod
    def getDeleteObjectCode(
        cls, to_name, value_name, needs_check, tolerant, emit, context
    ):
        """ Get code to delete (del) local variable.

        """

        # Need to overload this for each type it is used for, pylint: disable=unused-argument
        assert False, cls.c_type

    @classmethod
    def getVariableArgReferencePassingCode(cls, variable_code_name):
        """ Get code to pass variable as reference argument.

        """

        # Need to overload this for each type it is used for, pylint: disable=unused-argument
        assert False, cls.c_type

    @classmethod
    def getVariableArgDeclarationCode(cls, variable_code_name):
        """ Get variable declaration code with given name.

        """

        # Need to overload this for each type it is used for, pylint: disable=unused-argument
        assert False, cls.c_type

    @classmethod
    def getCellObjectAssignmentCode(cls, target_cell_code, variable_code_name, emit):
        """ Get assignment code to given cell object from object.

        """

        # Need to overload this for each type it is used for, pylint: disable=unused-argument
        assert False, cls.c_type

    @classmethod
    def emitAssignmentCodeFromBoolCondition(cls, to_name, condition, emit):
        """ Get the assignment code from C boolean condition.

        """
        # Need to overload this for each type it is used for, pylint: disable=unused-argument
        assert False, cls.c_type

    @classmethod
    def emitAssignmentCodeToNuitkaIntOrLong(
        cls, to_name, value_name, needs_check, emit, context
    ):
        """ Get the assignment code to int or long type.

        """
        # Need to overload this for each type it is used for, pylint: disable=unused-argument
        assert False, to_name

    @classmethod
    def getReleaseCode(cls, variable_code_name, needs_check, emit):
        """ Get release code for given object.

        """
        # Need to overload this for each type it is used for, pylint: disable=unused-argument
        assert False, cls.c_type
