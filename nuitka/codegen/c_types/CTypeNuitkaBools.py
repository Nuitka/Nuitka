#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" CType classes for nuitka_bool, an enum to represent True, False, unassigned.

"""

from nuitka.codegen.ErrorCodes import (
    getAssertionCode,
    getLocalVariableReferenceErrorCode
)

from .CTypeBases import CTypeBase


class CTypeNuitkaBoolEnum(CTypeBase):
    c_type = "nuitka_bool"

    @classmethod
    def getLocalVariableAssignCode(cls, variable_code_name, needs_release,
                                   tmp_name, ref_count, in_place):

        assert not in_place
        assert not ref_count

        return """\
if (%(tmp_name)s == Py_True)
{
    %(variable_code_name)s = NUITKA_BOOL_TRUE;
}
else
{
    %(variable_code_name)s = NUITKA_BOOL_FALSE;
}
        """ % {
            "variable_code_name" : variable_code_name,
            "tmp_name"            : tmp_name,
        }


    @classmethod
    def getVariableObjectAccessCode(cls, to_name, needs_check, variable_code_name,
                                    variable, emit, context):
        emit(
            """\
switch (%(variable_code_name)s)
{
    case NUITKA_BOOL_TRUE:
    {
        %(to_name)s = Py_True;
        break;
    }
    case NUITKA_BOOL_FALSE:
    {
        %(to_name)s = Py_False;
        break;
    }
    // case NUITKA_BOOL_UNASSIGNED: (MSVC wants default to believe it). We may
    // try to add an illegal default instead, but that may trigger warnings
    // from better compilers.
    default:
    {
#if %(needs_check)s
        %(to_name)s = NULL;
#else
        NUITKA_CANNOT_GET_HERE(%(identifier)s);
#endif
        break;
    }
}""" % {
        "variable_code_name" : variable_code_name,
        "to_name"            : to_name,
        "identifier"         : context.getOwner().getCodeName(),
        "needs_check"        : '1' if needs_check else '0'
    }
        )

        if 0: # Future work, pylint: disable=using-constant-test
            context.reportObjectConversion(variable)

    @classmethod
    def getLocalVariableInitTestCode(cls, variable_code_name):
        return "%s != NUITKA_BOOL_UNASSIGNED" % variable_code_name

    @classmethod
    def getLocalVariableObjectAccessCode(cls, variable_code_name):
        return "%s == NUITKA_BOOL_TRUE ? Py_True : Py_False" % variable_code_name

    @classmethod
    def getInitValue(cls, init_from):
        if init_from is None:
            return "NUITKA_BOOL_UNASSIGNED"
        else:
            assert False, init_from
            return init_from

    @classmethod
    def getReleaseCode(cls, variable_code_name, needs_check, emit):
        # TODO: Allow optimization to not get here.
        pass

    @classmethod
    def getDeleteObjectCode(cls, variable_code_name, needs_check, tolerant,
                            variable, emit, context):
        if not needs_check:
            emit(
                "%s = NUITKA_BOOL_UNASSIGNED;" % variable_code_name
            )
        elif tolerant:
            emit(
                "%s = NUITKA_BOOL_UNASSIGNED;" % variable_code_name
            )
        else:
            res_name = context.getBoolResName()

            emit(
                "%s = %s == NUITKA_BOOL_UNASSIGNED;" % (
                    res_name,
                    variable_code_name,
                )
            )
            emit(
                "%s = NUITKA_BOOL_UNASSIGNED;" % variable_code_name
            )

            if variable.isLocalVariable():
                getLocalVariableReferenceErrorCode(
                    variable  = variable,
                    condition = "%s == false" % res_name,
                    emit      = emit,
                    context   = context
                )
            else:
                getAssertionCode(
                    check = "%s != false" % res_name,
                    emit  = emit
                )
