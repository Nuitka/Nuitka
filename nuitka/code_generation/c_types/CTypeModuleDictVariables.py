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
""" Pseudo CType for module variables, object values contained in a dictionary.

    These are to integrate module variables with what is normally local
    stuff. Going from an to "PyObject *" is mostly its trick, then put
    into the dict.

"""

from nuitka.code_generation.templates.CodeTemplatesVariables import (
    template_del_global_known,
    template_del_global_unclear,
    template_read_mvar_unclear,
)

from .CTypeBases import CTypeBase


class CTypeModuleDictVariable(CTypeBase):
    @classmethod
    def emitVariableAssignCode(
        cls, value_name, needs_release, tmp_name, ref_count, inplace, emit, context
    ):
        if inplace:
            orig_name = context.getInplaceLeftName()

            emit("if (%s != %s) {" % (orig_name, tmp_name))

            emit(
                "UPDATE_STRING_DICT_INPLACE(moduledict_%s, (Nuitka_StringObject *)%s, %s);"
                % (
                    context.getModuleCodeName(),
                    context.getConstantCode(constant=value_name.code_name),
                    tmp_name,
                )
            )

            emit("}")

        else:
            emit(
                "UPDATE_STRING_DICT%s(moduledict_%s, (Nuitka_StringObject *)%s, %s);"
                % (
                    ref_count,
                    context.getModuleCodeName(),
                    context.getConstantCode(constant=value_name.code_name),
                    tmp_name,
                )
            )

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        tmp_name = context.allocateTempName("mvar_value")

        emit(
            template_read_mvar_unclear
            % {
                "module_identifier": context.getModuleCodeName(),
                "tmp_name": tmp_name,
                "var_name": context.getConstantCode(constant=value_name.code_name),
            }
        )

        return tmp_name

    @classmethod
    def getDeleteObjectCode(
        cls, to_name, value_name, needs_check, tolerant, emit, context
    ):

        if not needs_check or tolerant:
            emit(
                template_del_global_known
                % {
                    "module_identifier": context.getModuleCodeName(),
                    "res_name": context.getIntResName(),
                    "var_name": context.getConstantCode(constant=value_name.code_name),
                }
            )
        else:
            emit(
                template_del_global_unclear
                % {
                    "module_identifier": context.getModuleCodeName(),
                    "res_name": context.getIntResName(),
                    "result": to_name,
                    "var_name": context.getConstantCode(constant=value_name.code_name),
                }
            )
