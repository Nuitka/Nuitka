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
""" Helpers for code generation.

This dispatch building of expressions and statements, as well as providing
typical support functions to building parts.

"""

from contextlib import contextmanager

from nuitka.Options import isExperimental, shallTraceExecution
from nuitka.PythonVersions import python_version
from nuitka.Tracing import my_print, printError

from .Emission import SourceCodeCollector
from .Indentation import indented
from .LabelCodes import getStatementTrace
from .Reports import onMissingHelper

expression_dispatch_dict = {}


def setExpressionDispatchDict(dispatch_dict):
    # Using global here, as this is really a singleton, in the form of a module,
    # and this is to break the cyclic dependency it has, pylint: disable=global-statement

    # Please call us only once.
    global expression_dispatch_dict

    assert not expression_dispatch_dict
    expression_dispatch_dict = dispatch_dict


def generateExpressionCode(to_name, expression, emit, context, allow_none=False):
    try:
        _generateExpressionCode(
            to_name=to_name,
            expression=expression,
            emit=emit,
            context=context,
            allow_none=allow_none,
        )
    except Exception:
        printError(
            "Problem with %r at %s"
            % (
                expression,
                ""
                if expression is None
                else expression.getSourceReference().getAsString(),
            )
        )
        raise


def _generateExpressionCode(to_name, expression, emit, context, allow_none=False):
    # This is a dispatching function for every expression.

    if expression is None and allow_none:
        return None

    # Make sure we don't generate code twice for any node, this uncovers bugs
    # where nodes are shared in the tree, which is not allowed.
    assert not hasattr(expression, "code_generated"), expression
    expression.code_generated = True

    old_source_ref = context.setCurrentSourceCodeReference(
        expression.getSourceReference()
    )

    if not expression.isExpression():
        printError("No expression %r" % expression)

        expression.dump()
        assert False, expression

    expression_dispatch_dict[expression.kind](
        to_name=to_name, expression=expression, emit=emit, context=context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateExpressionsCode(names, expressions, emit, context):
    assert len(names) == len(expressions)

    result = []
    for name, expression in zip(names, expressions):
        if expression is not None:
            to_name = context.allocateTempName(name)

            generateExpressionCode(
                to_name=to_name, expression=expression, emit=emit, context=context
            )
        else:
            to_name = None

        result.append(to_name)

    return result


def generateChildExpressionsCode(expression, emit, context):
    value_names = []

    for child_name, child_value in expression.getVisitableNodesNamed():
        if child_value is not None:
            # Allocate anyway, so names are aligned.
            value_name = context.allocateTempName(child_name + "_name")

            generateExpressionCode(
                to_name=value_name, expression=child_value, emit=emit, context=context
            )

            value_names.append(value_name)
        else:
            context.skipTempName(child_name + "_value")

            value_names.append(None)

    return value_names


def generateChildExpressionCode(expression, emit, context, child_name=None):
    assert expression is not None

    if child_name is None:
        child_name = expression.getChildName()

    # Allocate anyway, so names are aligned.
    value_name = context.allocateTempName(child_name + "_name")

    generateExpressionCode(
        to_name=value_name, expression=expression, emit=emit, context=context
    )

    return value_name


statement_dispatch_dict = {}


def setStatementDispatchDict(dispatch_dict):
    # Using global here, as this is really a singleton, in the form of a module,
    # and this is to break the cyclic dependency it has, pylint: disable=global-statement

    # Please call us only once.
    global statement_dispatch_dict

    assert not statement_dispatch_dict
    statement_dispatch_dict = dispatch_dict


def generateStatementCode(statement, emit, context):
    try:
        statement_dispatch_dict[statement.kind](
            statement=statement, emit=emit, context=context
        )

        # Complain if any temporary was not dealt with yet.
        assert not context.getCleanupTempnames(), context.getCleanupTempnames()
    except Exception:
        printError(
            "Problem with %r at %s"
            % (statement, statement.getSourceReference().getAsString())
        )
        raise


def _generateStatementSequenceCode(statement_sequence, emit, context):
    if statement_sequence is None:
        return

    for statement in statement_sequence.getStatements():
        if shallTraceExecution():
            source_ref = statement.getSourceReference()

            statement_repr = repr(statement)
            source_repr = source_ref.getAsString()

            if python_version >= 300:
                statement_repr = statement_repr.encode("utf8")
                source_repr = source_repr.encode("utf8")

            emit(getStatementTrace(source_repr, statement_repr))

        # Might contain frame statement sequences as children.
        if statement.isStatementsFrame():
            from .FrameCodes import generateStatementsFrameCode

            generateStatementsFrameCode(
                statement_sequence=statement, emit=emit, context=context
            )
        else:
            context.pushCleanupScope()

            with context.variable_storage.withLocalStorage():
                statement_codes = SourceCodeCollector()

                generateStatementCode(
                    statement=statement, emit=statement_codes, context=context
                )

                statement_declarations = (
                    context.variable_storage.makeCLocalDeclarations()
                )

                block = False
                for s in statement_declarations:
                    if not block:
                        emit("{")

                        block = True
                    emit(indented(s))

                statement_codes.emitTo(emit, 1 if statement_declarations else 0)
                if block:
                    emit("}")

            context.popCleanupScope()


def generateStatementSequenceCode(statement_sequence, emit, context, allow_none=False):
    if allow_none and statement_sequence is None:
        return None

    assert statement_sequence.kind == "STATEMENTS_SEQUENCE", statement_sequence

    _generateStatementSequenceCode(
        statement_sequence=statement_sequence, emit=emit, context=context
    )


def decideConversionCheckNeeded(to_name, expression):
    if to_name.c_type == "nuitka_bool":
        conversion_check = expression.mayRaiseExceptionBool(BaseException)
    else:
        conversion_check = False

    return conversion_check


@contextmanager
def withObjectCodeTemporaryAssignment(to_name, value_name, expression, emit, context):
    if to_name.c_type == "PyObject *":
        value_name = to_name
    else:
        value_name = context.allocateTempName(value_name)

    yield value_name

    if to_name is not value_name:
        to_name.getCType().emitAssignConversionCode(
            to_name=to_name,
            value_name=value_name,
            needs_check=decideConversionCheckNeeded(to_name, expression),
            emit=emit,
            context=context,
        )

        from .ErrorCodes import getReleaseCode

        getReleaseCode(value_name, emit, context)


class HelperCallHandle(object):
    def __init__(
        self,
        helper_name,
        target_type,
        helper_target,
        left_shape,
        helper_left,
        right_shape,
        helper_right,
    ):
        self.helper_name = helper_name
        self.target_type = target_type
        self.helper_target = helper_target
        self.left_shape = left_shape
        self.helper_left = helper_left
        self.right_shape = right_shape
        self.helper_right = helper_right

    def __str__(self):
        return self.helper_name

    def emitHelperCall(self, to_name, arg_names, ref_count, needs_check, emit, context):
        if (
            self.target_type is not None
            and self.target_type.helper_code != self.helper_target.helper_code
        ):
            value_name = context.allocateTempName(
                to_name.code_name + "_" + self.helper_target.helper_code.lower(),
                type_name=self.helper_target.c_type,
                unique=to_name.code_name == "tmp_unused",
            )
        else:
            value_name = to_name

        emit(
            "%s = %s(%s);"
            % (
                value_name,
                self.helper_name,
                ", ".join(
                    "%s%s"
                    % (
                        "&" if count == 0 and "INPLACE" in self.helper_name else "",
                        arg_name,
                    )
                    for count, arg_name in enumerate(arg_names)
                ),
            )
        )

        # TODO: Move helper calling to something separate.
        from .ErrorCodes import getErrorExitCode, getReleaseCode

        getErrorExitCode(
            check_name=value_name,
            release_names=arg_names,
            needs_check=needs_check,
            emit=emit,
            context=context,
        )

        if ref_count:
            context.addCleanupTempName(value_name)

        if (
            self.target_type is not None
            and self.target_type.helper_code != self.helper_target.helper_code
        ):
            if self.target_type.helper_code in ("NBOOL", "NVOID"):
                self.target_type.emitAssignConversionCode(
                    to_name=to_name,
                    value_name=value_name,
                    needs_check=needs_check,
                    emit=emit,
                    context=context,
                )

                # TODO: Push that release into the emitAssignConversionCode for higher efficiency
                # in code generation, or else error releases are done as well as later release.
                if ref_count:
                    getReleaseCode(value_name, emit, context)
            else:
                assert False, (
                    self.target_type.helper_code,
                    self.helper_target.helper_code,
                )


def pickCodeHelper(
    prefix,
    suffix,
    target_type,
    left_shape,
    right_shape,
    helpers,
    nonhelpers,
    source_ref,
):
    # Lots of details to deal with, # pylint: disable=too-many-locals

    left_part = left_shape.helper_code
    right_part = right_shape.helper_code

    assert left_part != "INVALID", left_shape
    assert right_part != "INVALID", right_shape

    if target_type is None:
        target_part = None
    else:
        target_part = target_type.helper_code

        assert target_part != "INVALID", target_type

    # Special hack for "NVOID", lets go to "NBOOL more automatically"

    ideal_helper = "_".join(
        p for p in (prefix, target_part, left_part, right_part, suffix) if p
    )

    if target_part == "NVOID" and ideal_helper not in helpers:
        target_part = "NBOOL"

        ideal_helper = "_".join(
            p for p in (prefix, target_part, left_part, right_part, suffix) if p
        )

        from .c_types.CTypeNuitkaBools import CTypeNuitkaBoolEnum

        helper_target = CTypeNuitkaBoolEnum
    else:
        helper_target = target_type

    if ideal_helper in helpers:
        return HelperCallHandle(
            helper_name=ideal_helper,
            target_type=target_type,
            helper_target=helper_target,
            left_shape=left_shape,
            helper_left=left_shape,
            right_shape=right_shape,
            helper_right=right_shape,
        )

    if isExperimental("nuitka_ilong"):
        my_print(ideal_helper)

    if source_ref is not None and (not nonhelpers or ideal_helper not in nonhelpers):
        onMissingHelper(ideal_helper, source_ref)

    fallback_helper = "%s_%s_%s_%s%s" % (prefix, "OBJECT", "OBJECT", "OBJECT", suffix)

    fallback_helper = "_".join(
        p
        for p in (prefix, "OBJECT" if target_part else "", "OBJECT", "OBJECT", suffix)
        if p
    )

    from .c_types.CTypePyObjectPtrs import CTypePyObjectPtr

    return HelperCallHandle(
        helper_name=fallback_helper,
        target_type=target_type,
        helper_target=CTypePyObjectPtr,
        left_shape=left_shape,
        helper_left=CTypePyObjectPtr,
        right_shape=right_shape,
        helper_right=CTypePyObjectPtr,
    )
