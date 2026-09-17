#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Deferred releases for code generation.

Values whose release cannot happen at the point where code generation drops
them can be registered for release at the end of the enclosing code scope. The
concrete release behavior is supplied by the code generation that registers
such values.
"""

_deferred_release_emitter = None


def registerDeferredReleaseEmitter(emitter):
    # Singleton, pylint: disable=global-statement
    global _deferred_release_emitter
    _deferred_release_emitter = emitter


def addDeferredRelease(context, tmp_name, release_info):
    """Register a value for a release at the end of the code scope."""
    context.addDeferredReleaseName(tmp_name, release_info)


def emitDeferredReleases(emit, context):
    """Emit the release of all registered values of the current scope."""
    if _deferred_release_emitter is not None:
        _deferred_release_emitter.emitReleases(emit=emit, context=context)


def getDeferredReleaseErrorCode(context, tmp_name, release_info):
    """Get the error exit release code for a registered value, or None."""
    if _deferred_release_emitter is None:
        return None

    return _deferred_release_emitter.getErrorReleaseCode(
        context=context, tmp_name=tmp_name, release_info=release_info
    )


def checkDeferredReleaseUse(usage, tmp_name, context, detail):
    """Check if the usage of a registered value is disallowed."""
    if _deferred_release_emitter is not None and context.isDeferredReleaseName(
        tmp_name
    ):
        _deferred_release_emitter.disallowUse(
            usage=usage, tmp_name=tmp_name, context=context, detail=detail
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
