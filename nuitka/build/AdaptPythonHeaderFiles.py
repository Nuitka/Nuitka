#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Sandbox CPython's internal headers by stripping inline functions.

This ensures Nuitka modules only consume dynamically safe abstractions.
"""

import os
import re

from nuitka.options.Options import (
    isExperimental,
    isMingw64,
    shallMakeModule,
    shallUsePythonDebug,
)
from nuitka.PythonFlavors import isSelfCompiledPythonUninstalled
from nuitka.PythonVersions import (
    getTargetPythonIncludePath,
    isPythonWithGil,
    python_version,
    python_version_str,
)
from nuitka.Tracing import general
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.Diffs import getUnifiedDiff
from nuitka.utils.FileOperations import (
    copyFile,
    getFileContents,
    getFileList,
    makePath,
    putTextFileContents,
)
from nuitka.utils.Hashing import Hash
from nuitka.utils.Json import loadJsonFromFilename
from nuitka.utils.Utils import getArchitecture, getOS, isLinux, isWin32Windows


def getOffsetsJsonRequiredKeys(for_python_version_str):
    """Returns list of names we need to know the offset of."""
    # spell-checker: ignore stoptheworld,gilstate,ceval

    for_python_version_tuple = tuple(int(d) for d in for_python_version_str.split("."))
    keys = []
    if for_python_version_tuple >= (3, 12):
        keys.extend(["imports", "static_objects", "ceval"])
        if for_python_version_tuple >= (3, 13):
            keys.append("stoptheworld")
    else:
        keys.append("gilstate")

    return keys


def isOffsetsJsonOutdated(json_path, for_python_version_str):
    if not os.path.exists(json_path):
        return True

    data = loadJsonFromFilename(json_path)
    if data is None:
        return True

    expected_keys = set(
        "_PyRuntimeState_" + k
        for k in getOffsetsJsonRequiredKeys(for_python_version_str)
    )

    if set(data.keys()) != expected_keys:
        return True

    return False


def _replaceExpectedInAdaptedPythonHeaderFile(content, filename, old, new):
    count = content.count(old)

    assert count == 1, (
        "Expected exactly one adapted header replacement match in '%s', but got %d for %r."
        % (filename, count, old)
    )

    return content.replace(old, new)


def _substituteExpectedInAdaptedPythonHeaderFile(
    content, filename, pattern, replacement
):
    result, count = re.subn(pattern, replacement, content)

    assert count == 1, (
        "Expected exactly one adapted header regex replacement match in '%s', but got %d for %r."
        % (filename, count, pattern)
    )

    return result


def _applyExpectedAdaptedPythonHeaderReplacements(adapted, filename):
    if filename == "pycore_global_objects.h":
        adapted = _replaceExpectedInAdaptedPythonHeaderFile(
            content=adapted,
            filename=filename,
            old="(*((_PyRuntimeState*)Nuitka_Error_DoNotUseFunction())).static_objects.NAME",
            new="Nuitka_PyRuntime__static_objects->NAME",
        )

        if 0x3E0 <= python_version < 0x3F0 and shallMakeModule():
            adapted = _substituteExpectedInAdaptedPythonHeaderFile(
                content=adapted,
                filename=filename,
                pattern=(
                    r"#define _Py_INTERP_CACHED_OBJECT\(interp, NAME\) \\\n\s+"
                    r"\(interp\)->cached_objects\.NAME"
                ),
                replacement=(
                    "#define _Py_INTERP_CACHED_OBJECT(interp, NAME) \\\n"
                    "    Nuitka_PyInterpreterState_GetCachedObjects(interp)->NAME"
                ),
            )
            adapted = _substituteExpectedInAdaptedPythonHeaderFile(
                content=adapted,
                filename=filename,
                pattern=(
                    r"#define _Py_INTERP_STATIC_OBJECT\(interp, NAME\) \\\n\s+"
                    r"\(interp\)->static_objects\.NAME"
                ),
                replacement=(
                    "#define _Py_INTERP_STATIC_OBJECT(interp, NAME) \\\n"
                    "    Nuitka_PyInterpreterState_GetStaticObjects(interp)->NAME"
                ),
            )

    if filename == "pycore_object.h" and 0x3E0 <= python_version < 0x3F0:
        adapted = _substituteExpectedInAdaptedPythonHeaderFile(
            content=adapted,
            filename=filename,
            pattern=r"#\s+define _Py_DEC_REFTOTAL\(interp\) \\\n\s+interp->object_state\.reftotal--",
            replacement="#  define _Py_DEC_REFTOTAL(interp) \\\n    _Py_DecRefTotal(_PyThreadState_GET())",
        )

        if shallMakeModule() and isPythonWithGil():
            adapted = _replaceExpectedInAdaptedPythonHeaderFile(
                content=adapted,
                filename=filename,
                old="#  define _PyObject_GC_TRACK(op) \\\n        _PyObject_GC_TRACK(_PyObject_CAST(op))",
                new="#  define _PyObject_GC_TRACK(op) \\\n        Nuitka_GC_Track(_PyObject_CAST(op))",
            )
            adapted = _replaceExpectedInAdaptedPythonHeaderFile(
                content=adapted,
                filename=filename,
                old="#  define _PyObject_GC_UNTRACK(op) \\\n        _PyObject_GC_UNTRACK(_PyObject_CAST(op))",
                new="#  define _PyObject_GC_UNTRACK(op) \\\n        Nuitka_GC_UnTrack(_PyObject_CAST(op))",
            )
            adapted = _replaceExpectedInAdaptedPythonHeaderFile(
                content=adapted,
                filename=filename,
                old="""\
#  define _PyObject_GC_TRACK(op) \\
        _PyObject_GC_TRACK(__FILE__, __LINE__, _PyObject_CAST(op))""",
                new="#  define _PyObject_GC_TRACK(op) \\\n        Nuitka_GC_Track(_PyObject_CAST(op))",
            )
            adapted = _replaceExpectedInAdaptedPythonHeaderFile(
                content=adapted,
                filename=filename,
                old="""\
#  define _PyObject_GC_UNTRACK(op) \\
        _PyObject_GC_UNTRACK(__FILE__, __LINE__, _PyObject_CAST(op))""",
                new="#  define _PyObject_GC_UNTRACK(op) \\\n        Nuitka_GC_UnTrack(_PyObject_CAST(op))",
            )

    if filename == "pycore_stackref.h" and 0x3E0 <= python_version < 0x3F0:
        adapted = _substituteExpectedInAdaptedPythonHeaderFile(
            content=adapted,
            filename=filename,
            pattern=(
                r"(int tag = ref\.bits & Py_TAG_BITS;\n\s+)"
                r"PyObject \*obj = BITS_TO_PTR_MASKED\(ref\);"
            ),
            replacement=(
                r"\1NUITKA_MAY_BE_UNUSED PyObject *obj = BITS_TO_PTR_MASKED(ref);"
            ),
        )

    return adapted


def adaptPythonHeaderFile(content, filename):
    """Strip dangerous inline functions from a CPython header."""
    # A simple brace-matching state machine to rip out `static inline` blocks
    # that touch `_PyRuntime(State)`.

    lines = content.splitlines(True)
    out_lines = []

    in_inline_function = False
    brace_depth = 0
    current_block = []
    is_dangerous = False

    for line in lines:
        if not in_inline_function:
            # Detect start of static inline function
            if line.strip().startswith("static inline ") or line.strip().startswith(
                "Py_LOCAL_INLINE("
            ):
                in_inline_function = True
                brace_depth = 0
                current_block = [line]
                is_dangerous = False

                # Check for braces on the same line
                brace_depth += line.count("{")
                brace_depth -= line.count("}")
                continue

            out_lines.append(line)
        else:
            current_block.append(line)
            brace_depth += line.count("{")
            brace_depth -= line.count("}")

            # Simple heuristic detection within the block
            if any(
                t in line
                for t in (
                    "_PyRuntime",
                    "_PyLong_SMALL_INTS",
                    "_Py_tracemalloc_config",
                    "_Py_SINGLETON",
                )
            ):
                is_dangerous = True

            if brace_depth == 0 and any("{" in b for b in current_block):
                # End of function
                in_inline_function = False

                full_decl = " ".join(current_block)
                match = re.search(r"([_a-zA-Z0-9]+)\s*\(", full_decl)
                func_name = match.group(1) if match else "UNKNOWN_FUNC"

                if func_name == "_Py_freelists_GET":
                    is_dangerous = True

                if is_dangerous:
                    # Strip it entirely, replace with an error poison string
                    out_lines.append(
                        "/* Nuitka: Stripped dangerous inline function */\n"
                    )

                    out_lines.append(
                        "#define %s(...) Nuitka_Error_DoNotUseFunction()\n" % func_name
                    )
                else:
                    out_lines.extend(current_block)

    adapted = "".join(out_lines)
    # Poison any remaining direct property accesses to _PyRuntime by evaluating to an undefined function
    adapted = re.sub(
        r"(?<![a-zA-Z0-9_])_PyRuntime\.",
        "(*((_PyRuntimeState*)Nuitka_Error_DoNotUseFunction())).",
        adapted,
    )
    adapted = re.sub(
        r"&_PyRuntime(?![a-zA-Z0-9_])",
        "(&(*((_PyRuntimeState*)Nuitka_Error_DoNotUseFunction())))",
        adapted,
    )
    adapted = _applyExpectedAdaptedPythonHeaderReplacements(
        adapted=adapted, filename=filename
    )

    if "Nuitka_Error_DoNotUseFunction" in adapted:
        return "extern void * Nuitka_Error_DoNotUseFunction(void);\n" + adapted

    return adapted


def ensurePythonInternalsOffsets(cache_dir):
    """Ensure dynamic offsets are available, generating them to cache if missing."""

    if not isWin32Windows() or (python_version < 0x3D0 and not shallMakeModule()):
        return None

    keys = getOffsetsJsonRequiredKeys(python_version_str)
    if not keys:
        return None  # No offsets needed

    python_version_id = "%s-%s-%s-%s" % (
        python_version_str,
        getOS(),
        getArchitecture(),
        "gil" if isPythonWithGil() else "no-gil",
    )

    bundled_json_path = os.path.join(
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "python_internal_offset")
        ),
        "offsets_%s.json" % python_version_id,
    )

    cached_json_path = os.path.join(
        cache_dir,
        "offsets_%s.json" % python_version_id,
    )

    if not isOffsetsJsonOutdated(bundled_json_path, python_version_str):
        return None

    if not isOffsetsJsonOutdated(cached_json_path, python_version_str):
        return None  # Cache already contains mapping

    general.info(
        "Internal structure mapping for Python %s is missing. Extracting offsets dynamically via zig..."
        % python_version_str
    )

    try:
        from nuitka.tools.general.generate_header.GenerateHeader import (
            generateHeader,
        )

        generateHeader()
    except Exception as e:  # pylint: disable=broad-exception-caught
        return general.sysexit("Failed to generate headers dynamically: %s" % str(e))
    return cache_dir


def _getPythonInternalHeadersAndHash(internal_include_dir):
    # Hash the original header contents and mode-dependent adaptation settings.
    hash_obj = Hash()
    header_files = []

    hash_obj.updateFromValues(
        "adapted-python-headers-v9",
        "module" if shallMakeModule() else "non-module",
    )

    for filename in sorted(getFileList(internal_include_dir, only_suffixes=(".h",))):
        header_files.append(filename)
        hash_obj.updateFromFile(filename)

    return header_files, hash_obj.asHexDigest()


def _shallCreateAdaptedPythonHeaderFiles():
    # Python before 3.13 is not affected.
    if python_version < 0x3D0:
        return False

    needs_windows_mingw_opt_in = isWin32Windows() and not (
        isExperimental("force-mingw64") and isMingw64()
    )
    is_python314_module_mode = shallMakeModule() and 0x3E0 <= python_version < 0x3F0

    if not shallMakeModule():
        uses_default_platform_gate = True
    else:
        # Python 3.14 module mode needs adapted headers on all OSes due to
        # cross-patch interpreter layout changes.
        uses_default_platform_gate = not is_python314_module_mode

    if uses_default_platform_gate:
        # TODO: We delay this until we have a better way to detect the compiler
        # inside of Nuitka and not in Scons.
        if needs_windows_mingw_opt_in:
            return False

        if not isLinux() and not isWin32Windows():
            return False

    return True


def createAdaptedPythonHeaderFiles(source_dir):
    """Ensure sanitized internal headers exist in the build cache and JSON offsets are extracted."""

    if not _shallCreateAdaptedPythonHeaderFiles():
        return None

    internal_include_dir = os.path.join(
        getTargetPythonIncludePath(
            logger=general,
            python_debug=shallUsePythonDebug(),
            self_compiled_python_uninstalled=isSelfCompiledPythonUninstalled(),
        ),
        "internal",
    )

    header_files, total_hash = _getPythonInternalHeadersAndHash(internal_include_dir)

    cache_base_dir = getCacheDir("adapted_headers", create=True)

    # 1. Ensure Offsets Extracted
    ensurePythonInternalsOffsets(cache_dir=cache_base_dir)

    target_cache_dir = os.path.join(cache_base_dir, total_hash)
    adapt_cache_file = os.path.join(target_cache_dir, "adapted_headers.patch")

    # 2. Check if headers already stripped
    if os.path.exists(adapt_cache_file):
        copyFile(adapt_cache_file, os.path.join(source_dir, "adapted_headers.patch"))

        return target_cache_dir

    # 3. Adapt and Copy Headers
    makePath(os.path.join(target_cache_dir, "internal"))

    adapt_lines = []

    for filename in header_files:
        rel_path = os.path.relpath(filename, internal_include_dir)
        d = os.path.join(target_cache_dir, "internal", rel_path)
        makePath(os.path.dirname(d))

        item = os.path.basename(filename)
        if item.startswith("pycore_"):
            content = getFileContents(filename, mode="r", encoding="utf-8")
            adapted = adaptPythonHeaderFile(content, rel_path.replace(os.path.sep, "/"))
            putTextFileContents(d, adapted, encoding="utf-8")

            if content != adapted:
                # Add unified diff to our patch aggregator
                adapt_lines.extend(
                    getUnifiedDiff(
                        old_lines=content.splitlines(True),
                        new_lines=adapted.splitlines(True),
                        old_filename="a/internal/" + rel_path.replace(os.path.sep, "/"),
                        new_filename="b/internal/" + rel_path.replace(os.path.sep, "/"),
                    )
                )
                if adapt_lines and not adapt_lines[-1].endswith("\n"):
                    adapt_lines.append("\n")
        else:
            copyFile(filename, d)

    if adapt_lines:
        putTextFileContents(adapt_cache_file, "".join(adapt_lines), encoding="utf-8")
        copyFile(adapt_cache_file, os.path.join(source_dir, "adapted_headers.patch"))

    return target_cache_dir


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
