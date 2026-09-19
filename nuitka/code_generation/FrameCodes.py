#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Frame codes

This is about frame stacks and their management. There are different kinds
of frames for different uses.
"""

from nuitka.options.Options import isExperimental
from nuitka.PythonVersions import python_version
from nuitka.utils.Jinja2 import renderTemplateFromString

from .CodeHelpers import _generateStatementSequenceCode
from .CodeObjectCodes import getCodeObjectAccessCode
from .Emission import SourceCodeCollector
from .ExceptionCodes import getTracebackMakingIdentifier
from .Indentation import indented
from .LabelCodes import getGotoCode, getLabelCode
from .ModuleCodes import getModuleAccessCode
from .templates.CodeTemplatesFrames import (
    template_frame_attach_locals,
    template_frame_guard_generator_exception_handler,
    template_frame_guard_generator_return_handler,
    template_frame_guard_normal_exception_handler,
    template_frame_guard_normal_main_block,
    template_frame_guard_normal_return_handler,
)

_frame_locals_proxy_used = False


def hasFrameLocalsProxy():
    """Whether any frame of the program can publish a FrameLocalsProxy.

    Returns:
        bool
    """
    return _frame_locals_proxy_used


def _getFrameVariableIndicators(context):
    frame_variables = context.frame_variables_stack[-1]
    frame_var_types = context.frame_variable_types

    return [
        frame_var_types[variable][1] if variable in frame_var_types else "N"
        for variable in frame_variables
    ]


def _searchLocalVariableByName(local_variables, variable_name):
    for local_variable in local_variables:
        if local_variable.getName() == variable_name:
            return local_variable

    return None


def generateStatementsFrameCode(statement_sequence, emit, context):
    # This is a wrapper that provides also handling of frames. The standard
    # and generator frame variety ought to be merged once generators are
    # possible to inline.
    # TODO: This will get simpler, pylint: disable=too-many-locals
    # Many branches and statements for the nested frame handling, which
    # includes the exception line number handover, pylint: disable=too-many-branches,too-many-statements
    context.pushCleanupScope()

    guard_mode = statement_sequence.getGuardMode()

    code_object = statement_sequence.getCodeObject()
    code_object_access_code = getCodeObjectAccessCode(
        code_object=code_object, context=context
    )

    parent_exception_exit = context.getExceptionEscape()

    # For nested frames, make sure to restore set the type description.
    if context.getFrameHandle() is not None:
        real_parent_exception_exit = parent_exception_exit
        parent_exception_exit = context.allocateLabel("nested_frame_exit")

    # Allow stacking of frame handles.
    context.pushFrameHandle(
        statement_sequence.getFrameCodeName(), statement_sequence.hasStructureMember()
    )

    context.setExceptionEscape(context.allocateLabel("frame_exception_exit"))

    needs_preserve = statement_sequence.needsFrameExceptionPreserving()

    if statement_sequence.mayReturn():
        parent_return_exit = context.getReturnTarget()

        context.setReturnTarget(context.allocateLabel("frame_return_exit"))
    else:
        parent_return_exit = None

    # We need to define that all the variables needs to be pushed. We do not
    # have a flag that says "always NULL" for variables. With efficient NULL
    # passing however (not at all, TODO), that doesn't matter much.
    provider = statement_sequence.getParentVariableProvider()
    local_variables = provider.getLocalVariables()

    context.pushFrameVariables(
        tuple(
            _searchLocalVariableByName(local_variables, variable_name)
            for variable_name in code_object.getVarNames()
        )
    )

    # Now generate the statements code into a local buffer, to we can wrap
    # the frame stuff around it.
    local_emit = SourceCodeCollector()

    _generateStatementSequenceCode(
        statement_sequence=statement_sequence, emit=local_emit, context=context
    )

    if statement_sequence.mayRaiseException(BaseException):
        frame_exception_exit = context.getExceptionEscape()
    else:
        frame_exception_exit = None

    if parent_return_exit is not None:
        frame_return_exit = context.getReturnTarget()
    else:
        frame_return_exit = None

    if guard_mode == "generator":
        # TODO: This case should also care about "needs_preserve", as for
        # Python3 it is actually not a stub of empty code.

        # TODO: Rename "code_identifier" to "code_object_access_code" in these
        # functions and make it work with function call result properly and not
        # have to be a variable name.
        getFrameGuardGeneratorCode(
            frame_node=statement_sequence,
            code_identifier=code_object_access_code,
            codes=local_emit,
            parent_exception_exit=parent_exception_exit,
            frame_exception_exit=frame_exception_exit,
            parent_return_exit=parent_return_exit,
            frame_return_exit=frame_return_exit,
            emit=emit,
            context=context,
        )
    elif guard_mode in ("full", "once"):
        getFrameGuardHeavyCode(
            frame_node=statement_sequence,
            code_identifier=code_object_access_code,
            parent_exception_exit=parent_exception_exit,
            parent_return_exit=parent_return_exit,
            frame_exception_exit=frame_exception_exit,
            frame_return_exit=frame_return_exit,
            codes=local_emit,
            needs_preserve=needs_preserve,
            emit=emit,
            context=context,
        )
    else:
        assert False, guard_mode

    context.popFrameVariables()
    context.popFrameHandle()

    # For nested frames, make sure to restore set the type description.
    if context.getFrameHandle() is not None:
        label = context.allocateLabel("skip_nested_handling")
        getGotoCode(label, emit)
        getLabelCode(parent_exception_exit, emit)

        # The nested frame used its own exception line number, give the
        # caller the line of the frame statement instead, which is what
        # CPython does for class bodies. This is done with the frame's own
        # line variable, which is then handed over by the outline escape.
        frame_source_ref = statement_sequence.getSourceReference()

        if not frame_source_ref.isInternal():
            (
                _outline_exception_state_name,
                outline_exception_lineno,
            ) = context.getExceptionVariableDescriptions()

            emit(
                "%s = %d;"
                % (outline_exception_lineno, frame_source_ref.getLineNumber())
            )

        getGotoCode(real_parent_exception_exit, emit)
        getLabelCode(label, emit)

        parent_exception_exit = real_parent_exception_exit

    context.popCleanupScope()

    context.setExceptionEscape(parent_exception_exit)

    if frame_return_exit is not None:
        context.setReturnTarget(parent_return_exit)


def getFrameAttachLocalsCode(frame_identifier):
    return template_frame_attach_locals % {
        "frame_identifier": frame_identifier,
    }


def getFrameAttachLocalsCopyCode(context, frame_identifier, type_description):
    struct_name = context.variable_storage.struct_name
    struct_type_name = context.variable_storage.struct_type_name

    return """\
*(%(struct_type_name)s *)NUITKA_FRAME_LOCALS_STORAGE(%(frame_identifier)s) = %(struct_name)s;
Nuitka_Frame_AttachLocalsCopied(
    %(frame_identifier)s,
    %(type_description)s
);""" % {
        "struct_type_name": struct_type_name,
        "frame_identifier": frame_identifier,
        "struct_name": struct_name,
        "type_description": type_description,
    }


def getFrameGuardHeavyCode(
    frame_node,
    code_identifier,
    codes,
    parent_exception_exit,
    parent_return_exit,
    frame_exception_exit,
    frame_return_exit,
    needs_preserve,
    emit,
    context,
):
    # A lot of details go into the frame guard code,
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    no_exception_exit = context.allocateLabel("frame_no_exception")

    frame_identifier = context.getFrameHandle()
    if frame_node.getGuardMode() == "full":
        frame_cache_identifier = context.variable_storage.addFrameCacheDeclaration(
            frame_identifier.code_name
        )
    else:
        frame_cache_identifier = None

    frame_init_code = ""
    frame_exit_code = ""

    # Expose the locals dictionary with the frame locals if it exists.
    if frame_node.isStatementsFrameClass():
        attach_locals_code = getFrameAttachLocalsCode(frame_identifier)
        module_identifier = getModuleAccessCode(context)
        locals_dict_name = context.variable_storage.getVariableDeclarationTop(
            frame_node.getLocalsScope().getCodeName()
        )
        use_locals_dict = locals_dict_name in context.getLocalsDictNames()

        make_frame_code = (
            """MAKE_CLASS_FRAME(tstate, %(code_identifier)s, %(module_identifier)s, NULL, 0, NULL)"""
            % {
                "code_identifier": code_identifier,
                "module_identifier": module_identifier,
            }
        )

        if use_locals_dict:
            frame_init_code = """\
Nuitka_Frame_AssignLocals(%(frame_identifier)s, %(locals_dict)s);
""" % {
                "frame_identifier": frame_identifier,
                "locals_dict": locals_dict_name,
            }
        elif python_version < 0x300:
            frame_init_code = """\
Nuitka_Frame_AssignLocals(%(frame_identifier)s, %(module_identifier)s);
""" % {
                "frame_identifier": frame_identifier,
                "module_identifier": module_identifier,
            }

        if use_locals_dict or python_version < 0x300:
            frame_exit_code = """\
Nuitka_Frame_ClearLocals(%(frame_identifier)s);
""" % {
                "frame_identifier": frame_identifier,
            }
    elif frame_node.isStatementsFrameFunction():
        if context.variable_storage.makeCStructLevelDeclarations():
            indicators = _getFrameVariableIndicators(context)

            # The runtime walkers use the code object's co_nlocals as the
            # description length, so they must agree at build time already.
            assert len(indicators) == len(frame_node.getCodeObject().getVarNames())

            # A struct with only outline variables has no frame variables and
            # would produce an empty type description, which is invalid C.
            assert indicators, (
                "empty type description",
                frame_node,
                context.getOwner(),
                context.variable_storage.makeCStructLevelDeclarations(),
            )

            locals_size = "sizeof(%s)" % context.variable_storage.struct_name
            type_description_name = context.getTypeDescriptionCode("".join(indicators))

            if isExperimental("force-locals-frame-proxy"):
                if python_version >= 0x3D0:
                    # Singleton, pylint: disable=global-statement
                    global _frame_locals_proxy_used
                    _frame_locals_proxy_used = True

                attach_locals_code = getFrameAttachLocalsCode(frame_identifier)
                # A cached frame can have been cleared in the meantime, e.g.
                # by "frame.clear()", which resets the type description and
                # writability, so publish them again, not only the pointer
                # to the stack struct.
                frame_init_code = """\
%(frame_identifier)s->m_type_description = %(type_description)s;
%(frame_identifier)s->m_locals_writable = 1;
%(frame_identifier)s->m_locals_ptr = &%(struct_name)s;""" % {
                    "frame_identifier": frame_identifier,
                    "type_description": type_description_name,
                    "struct_name": context.variable_storage.struct_name,
                }
                # On normal exit the frame is cached and nobody reads the stack
                # struct anymore; on the exception path the attach above has
                # already copied the values into the frame heap buffer.
                frame_exit_code = "%s->m_locals_ptr = NULL;" % frame_identifier
                frame_type_description = type_description_name
            else:
                # Same struct, but its address is not published on the normal
                # path, so the C compiler can keep the locals in registers. At
                # the exception exit the struct is copied by value, which is
                # not an address escape either.
                attach_locals_code = getFrameAttachLocalsCopyCode(
                    context, frame_identifier, type_description_name
                )
                frame_init_code = ""
                frame_exit_code = ""
                frame_type_description = "NULL"
        else:
            attach_locals_code = ""
            frame_init_code = ""
            frame_exit_code = ""
            frame_type_description = "NULL"
            locals_size = "0"

        make_frame_code = """MAKE_FUNCTION_FRAME(tstate, %(code_identifier)s, %(module_identifier)s, %(locals_size)s, \
%(type_description)s)""" % {
            "code_identifier": code_identifier,
            "module_identifier": getModuleAccessCode(context),
            "locals_size": locals_size,
            "type_description": frame_type_description,
        }
    elif frame_node.isStatementsFrameModule():
        attach_locals_code = ""
        make_frame_code = (
            """MAKE_MODULE_FRAME(%(code_identifier)s, %(module_identifier)s)"""
            % {
                "code_identifier": code_identifier,
                "module_identifier": getModuleAccessCode(context),
            }
        )
    else:
        assert False, frame_node

    context_identifier = frame_node.getStructureMember()

    emit(
        renderTemplateFromString(
            template_frame_guard_normal_main_block,
            frame_identifier=frame_identifier,
            frame_cache_identifier=frame_cache_identifier,
            codes=indented(codes),
            no_exception_exit=no_exception_exit,
            needs_preserve=needs_preserve,
            make_frame_code=make_frame_code,
            frame_init_code=frame_init_code,
            frame_exit_code=frame_exit_code,
            context_identifier=context_identifier,
            is_python3=python_version >= 0x300,
        )
    )

    if frame_return_exit is not None:
        emit(
            renderTemplateFromString(
                template_frame_guard_normal_return_handler,
                frame_identifier=frame_identifier,
                return_exit=parent_return_exit,
                frame_return_exit=frame_return_exit,
                needs_preserve=needs_preserve,
                frame_exit_code=frame_exit_code,
            )
        )

    if frame_exception_exit is not None:
        (
            exception_state_name,
            exception_lineno,
        ) = context.getExceptionVariableDescriptions()

        emit(
            renderTemplateFromString(
                template_frame_guard_normal_exception_handler,
                frame_identifier=context.getFrameHandle(),
                frame_cache_identifier=frame_cache_identifier,
                tb_making_code=getTracebackMakingIdentifier(
                    context=context, lineno_name=exception_lineno
                ),
                attach_locals_code=attach_locals_code,
                parent_exception_exit=parent_exception_exit,
                frame_exception_exit=frame_exception_exit,
                needs_preserve=needs_preserve,
                exception_state_name=exception_state_name,
                exception_lineno=exception_lineno,
            )
        )

    getLabelCode(no_exception_exit, emit)


def getFrameGuardGeneratorCode(
    frame_node,
    code_identifier,
    codes,
    parent_exception_exit,
    parent_return_exit,
    frame_exception_exit,
    frame_return_exit,
    emit,
    context,
):
    # We really need this many parameters here and it gets very
    # detail rich, pylint: disable=too-many-locals
    (
        exception_state_name,
        exception_lineno,
    ) = context.getExceptionVariableDescriptions()

    context_identifier = frame_node.getStructureMember()

    no_exception_exit = context.allocateLabel("frame_no_exception")

    frame_identifier = context.getFrameHandle()
    frame_cache_identifier = context.variable_storage.addFrameCacheDeclaration(
        frame_identifier.code_name
    )

    # TODO: Wire the FrameLocalsProxy to generator/coroutine/asyncgen frames by
    # emitting a type description and pointing m_locals_ptr at the generator
    # object's m_heap_storage. That storage is owned by the generator object, so
    # the frame must borrow (not release) those references, unlike the copy
    # detach of ordinary functions. Until then no type description is passed
    # (matching the resume-time MAKE_FUNCTION_FRAME in the generator type code).
    make_frame_code = (
        """MAKE_FUNCTION_FRAME(tstate, %(code_identifier)s, %(module_identifier)s, 0, NULL)"""
        % {
            "code_identifier": code_identifier,
            "module_identifier": getModuleAccessCode(context),
        }
    )
    is_generator = True

    frame_init_code = ""
    frame_exit_code = ""

    emit(
        renderTemplateFromString(
            template_frame_guard_normal_main_block,
            frame_identifier=frame_identifier,
            frame_cache_identifier=frame_cache_identifier,
            context_identifier=context_identifier,
            codes=indented(codes),
            no_exception_exit=no_exception_exit,
            needs_preserve=False,  # TODO: Clears stuff
            make_frame_code=make_frame_code,
            frame_init_code=frame_init_code,
            frame_exit_code=frame_exit_code,
            is_generator=is_generator,
            is_python3=python_version >= 0x300,
        )
    )

    if frame_return_exit is not None:
        emit(
            template_frame_guard_generator_return_handler
            % {
                "context_identifier": context_identifier,
                "return_exit": parent_return_exit,
                "frame_return_exit": frame_return_exit,
            }
        )

    if frame_exception_exit is not None:
        emit(
            renderTemplateFromString(
                template_frame_guard_generator_exception_handler,
                context_identifier=context_identifier,
                frame_identifier=frame_identifier,
                frame_cache_identifier=frame_cache_identifier,
                exception_state_name=exception_state_name,
                exception_lineno=exception_lineno,
                tb_making=getTracebackMakingIdentifier(
                    context=context, lineno_name=exception_lineno
                ),
                attach_locals=getFrameAttachLocalsCode(frame_identifier),
                frame_exception_exit=frame_exception_exit,
                parent_exception_exit=parent_exception_exit,
                is_python3=python_version >= 0x300,
            )
        )

    getLabelCode(no_exception_exit, emit)


def generateFramePreserveExceptionCode(statement, emit, context):
    if python_version < 0x300:
        emit("// Preserve existing published exception.")

        emit(
            "PRESERVE_FRAME_EXCEPTION(tstate, %(frame_identifier)s);"
            % {"frame_identifier": context.getFrameHandle()}
        )
    else:
        preserver_id = statement.getPreserverId()

        assert preserver_id != 0, statement
        exception_preserved = context.addExceptionPreserverVariables(preserver_id)

        emit(
            """\
// Preserve existing published exception id %(preserver_id)d.
%(exception_preserved)s = GET_CURRENT_EXCEPTION(tstate);
"""
            % {
                "exception_preserved": exception_preserved,
                "preserver_id": preserver_id,
            }
        )


def generateFrameRestoreExceptionCode(statement, emit, context):
    if python_version < 0x300:
        emit(
            """\
// Restore previous exception.
RESTORE_FRAME_EXCEPTION(%(frame_identifier)s);"""
            % {"frame_identifier": context.getFrameHandle()}
        )
    else:
        preserver_id = statement.getPreserverId()

        exception_preserved = context.addExceptionPreserverVariables(preserver_id)

        emit(
            """\
// Restore previous exception id %(preserver_id)d.
SET_CURRENT_EXCEPTION(tstate, &%(exception_preserved)s);
"""
            % {
                "exception_preserved": exception_preserved,
                "preserver_id": preserver_id,
            }
        )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
