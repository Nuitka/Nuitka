#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Reformulation of try/finally statements.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.LoopNodes import StatementLoopBreak, StatementLoopContinue
from nuitka.nodes.ReturnNodes import (
    ExpressionReturnedValueRef,
    StatementReturn
)
from nuitka.nodes.StatementNodes import (
    StatementPreserveFrameException,
    StatementPublishException,
    StatementRestoreFrameException,
    StatementsSequence
)
from nuitka.nodes.TryNodes import StatementTry
from nuitka.Options import isDebug
from nuitka.PythonVersions import python_version

from .TreeHelpers import (
    buildStatementsNode,
    getStatementsAppended,
    getStatementsPrepended,
    makeReraiseExceptionStatement,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceFromStatements,
    mergeStatements,
    popBuildContext,
    pushBuildContext
)


def makeTryFinallyStatement(provider, tried, final, source_ref, public_exc = False):
    # Complex handling, due to the many variants, pylint: disable=too-many-branches,too-many-locals

    if type(tried) in (tuple, list):
        tried = makeStatementsSequenceFromStatements(
            *tried
        )
    if type(final) in (tuple, list):
        final = StatementsSequence(
            statements = mergeStatements(final, False),
            source_ref = source_ref
        )

    if tried is not None and not tried.isStatementsSequence():
        tried = makeStatementsSequenceFromStatement(tried)
    if final is not None and not final.isStatementsSequence():
        final = makeStatementsSequenceFromStatement(final)

    if tried is None:
        return final

    if final is None:
        return tried

    if provider is not None:
        tried.parent = provider
        final.parent = provider

    assert tried is not None, source_ref
    assert final is not None, source_ref

    # TODO: Currently it's not possible anymore to get at XML for all codes
    # during the building phase. So this error catcher cannot work currently.
    if False and isDebug():
        final2 = final.makeClone()
        final2.parent = provider

        import nuitka.TreeXML
        if nuitka.TreeXML.Element is not None:
            f1 = final.asXml()
            f2 = final2.asXml()

            def compare(a, b):
                for c1, c2 in zip(a, b):
                    compare(c1, c2)

                assert a.attrib == b.attrib, (a.attrib, b.attrib)

            compare(f1, f2)

    def getFinal():
        # Make a clone of "final" only if necessary.
        if hasattr(getFinal, "used"):
            return final.makeClone()
        else:
            getFinal.used = True
            return final

    if tried.mayRaiseException(BaseException):
        except_handler = getStatementsAppended(
            statement_sequence = getFinal(),
            statements         = makeReraiseExceptionStatement(
                source_ref = source_ref
            )
        )

        if public_exc:
            preserver_id = provider.allocatePreserverId()

            except_handler = getStatementsPrepended(
                statement_sequence = except_handler,
                statements         = (
                    StatementPreserveFrameException(
                        preserver_id = preserver_id,
                        source_ref   = source_ref.atInternal()
                    ),
                    StatementPublishException(
                        source_ref = source_ref
                    )
                )
            )

            except_handler = makeTryFinallyStatement(
                provider   = provider,
                tried      = except_handler,
                final      = StatementRestoreFrameException(
                    preserver_id = preserver_id,
                    source_ref   = source_ref.atInternal()
                ),
                public_exc = False,
                source_ref = source_ref,
            )

            except_handler = makeStatementsSequenceFromStatement(
                statement = except_handler
            )

        except_handler.parent = provider
    else:
        except_handler = None

    if tried.mayBreak():
        break_handler = getStatementsAppended(
            statement_sequence = getFinal(),
            statements         = StatementLoopBreak(
                source_ref = source_ref
            )
        )

        break_handler.parent = provider
    else:
        break_handler = None

    if tried.mayContinue():
        continue_handler = getStatementsAppended(
            statement_sequence = getFinal(),
            statements         = StatementLoopContinue(
                source_ref = source_ref
            )
        )

        continue_handler.parent = provider
    else:
        continue_handler = None

    if tried.mayReturn():
        return_handler = getStatementsAppended(
            statement_sequence = getFinal(),
            statements         = StatementReturn(
                expression = ExpressionReturnedValueRef(
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        )

        return_handler.parent = provider
    else:
        return_handler = None

    result = StatementTry(
        tried            = tried,
        except_handler   = except_handler,
        break_handler    = break_handler,
        continue_handler = continue_handler,
        return_handler   = return_handler,
        source_ref       = source_ref
    )

    if result.isStatementAborting():
        return result
    else:
        return makeStatementsSequence(
            statements = (
                result,
                getFinal()
            ),
            allow_none = False,
            source_ref = source_ref
        )


def buildTryFinallyNode(provider, build_tried, node, source_ref):

    if python_version < 300:
        # Prevent "continue" statements in the final blocks
        pushBuildContext("finally")
        final = buildStatementsNode(
            provider   = provider,
            nodes      = node.finalbody,
            source_ref = source_ref
        )
        popBuildContext()

        return makeTryFinallyStatement(
            provider   = provider,
            tried      = build_tried(),
            final      = final,
            source_ref = source_ref
        )
    else:
        tried = build_tried()

        # Prevent "continue" statements in the final blocks, these have to
        # become "SyntaxError".
        pushBuildContext("finally")
        final = buildStatementsNode(
            provider   = provider,
            nodes      = node.finalbody,
            source_ref = source_ref
        )
        popBuildContext()

        return makeTryFinallyStatement(
            provider   = provider,
            tried      = tried,
            final      = final,
            public_exc = True,
            source_ref = source_ref
        )
