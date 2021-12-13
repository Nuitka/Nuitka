#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Common test infrastructure functions. To be used by test runners. """

import ast
import atexit
import gc
import hashlib
import os
import shutil
import signal
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from optparse import OptionGroup, OptionParser

from nuitka.__past__ import subprocess
from nuitka.PythonVersions import (
    getPartiallySupportedPythonVersions,
    getSupportedPythonVersions,
)
from nuitka.Tracing import OurLogger, my_print
from nuitka.tree.SourceReading import readSourceCodeFromFilename
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.Execution import check_output, getNullInput, getNullOutput
from nuitka.utils.FileOperations import (
    areSamePaths,
    getExternalUsePath,
    getFileContentByLine,
    getFileContents,
    getFileList,
    isPathBelowOrSameAs,
    makePath,
    openTextFile,
    removeDirectory,
)
from nuitka.utils.Jinja2 import getTemplate
from nuitka.utils.Utils import getOS

from .SearchModes import (
    SearchModeAll,
    SearchModeByPattern,
    SearchModeCoverage,
    SearchModeImmediate,
    SearchModeOnly,
    SearchModeResume,
)

test_logger = OurLogger("", base_style="blue")


def check_result(*popenargs, **kwargs):
    if "stdout" in kwargs:
        raise ValueError("stdout argument not allowed, it will be overridden.")

    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    _unused_output, _unused_err = process.communicate()
    retcode = process.poll()

    if retcode:
        return False
    else:
        return True


def goMainDir():
    # Go its own directory, to have it easy with path knowledge.
    os.chdir(os.path.dirname(os.path.abspath(sys.modules["__main__"].__file__)))


_python_version_str = None
_python_version = None
_python_arch = None
_python_executable = None
_python_vendor = None


def setup(suite="", needs_io_encoding=False, silent=False, go_main=True):
    if go_main:
        goMainDir()

    if "PYTHON" not in os.environ:
        os.environ["PYTHON"] = sys.executable

    # Allow test code to use this to make caching specific.
    os.environ["NUITKA_TEST_SUITE"] = suite

    # Allow providing 33, 27, and expand that to python2.7
    if (
        len(os.environ["PYTHON"]) == 2
        and os.environ["PYTHON"].isdigit()
        and os.name != "nt"
    ):

        os.environ["PYTHON"] = "python%s.%s" % (
            os.environ["PYTHON"][0],
            os.environ["PYTHON"][1],
        )

    if needs_io_encoding and "PYTHONIOENCODING" not in os.environ:
        os.environ["PYTHONIOENCODING"] = "utf-8"

    version_output = check_output(
        (
            os.environ["PYTHON"],
            "-c",
            """\
import sys, os;\
print(".".join(str(s) for s in list(sys.version_info)[:3]));\
print(("x86_64" if "AMD64" in sys.version else "x86") if os.name == "nt" else os.uname()[4]);\
print(sys.executable);\
print("Anaconda" if os.path.exists(os.path.join(sys.prefix, 'conda-meta')) else "Unknown")\
""",
        ),
        stderr=subprocess.STDOUT,
    )

    global _python_version_str, _python_version, _python_arch, _python_executable, _python_vendor  # singleton, pylint: disable=global-statement

    _python_version_str = version_output.split(b"\n")[0].strip()
    _python_arch = version_output.split(b"\n")[1].strip()
    _python_executable = version_output.split(b"\n")[2].strip()
    _python_vendor = version_output.split(b"\n")[3].strip()

    if str is not bytes:
        _python_version_str = _python_version_str.decode("utf8")
        _python_arch = _python_arch.decode("utf8")
        _python_executable = _python_executable.decode("utf8")
        _python_vendor = _python_vendor.decode("utf8")

    assert type(_python_version_str) is str, repr(_python_version_str)
    assert type(_python_arch) is str, repr(_python_arch)
    assert type(_python_executable) is str, repr(_python_executable)

    if not silent:
        my_print("Using concrete python", _python_version_str, "on", _python_arch)

    if "COVERAGE_FILE" not in os.environ:
        os.environ["COVERAGE_FILE"] = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", ".coverage"
        )

    _python_version = tuple(int(d) for d in _python_version_str.split("."))

    return _python_version


def getPythonArch():
    return _python_arch


def getPythonVendor():
    return _python_vendor


def getPythonVersionString():
    return _python_version_str


tmp_dir = None


def getTempDir():
    # Create a temporary directory to work in, automatically remove it in case
    # it is empty in the end.
    global tmp_dir  # singleton, pylint: disable=global-statement

    if tmp_dir is None:
        tmp_dir = tempfile.mkdtemp(
            prefix=os.path.basename(
                os.path.dirname(os.path.abspath(sys.modules["__main__"].__file__))
            )
            + "-",
            dir=tempfile.gettempdir() if not os.path.exists("/var/tmp") else "/var/tmp",
        )

        def removeTempDir():
            removeDirectory(path=tmp_dir, ignore_errors=True)

        atexit.register(removeTempDir)

    return tmp_dir


def convertUsing2to3(path, force=False):
    command = [os.environ["PYTHON"], "-m", "py_compile", path]

    if not force:
        if "xrange" not in getFileContents(path):
            if check_result(command, stderr=getNullOutput()):
                return path, False

    filename = os.path.basename(path)

    new_path = os.path.join(getTempDir(), filename)

    # This may already be a temp file, e.g. because of construct creation.
    try:
        shutil.copy(path, new_path)
    except shutil.Error:
        pass

    # For Python2.6 and 3.2 the -m lib2to3 was not yet supported.
    use_binary = sys.version_info[:2] in ((2, 6), (3, 2))

    if use_binary:
        # On Windows, we cannot rely on 2to3 to be in the path.
        if os.name == "nt":
            command = [
                sys.executable,
                os.path.join(os.path.dirname(sys.executable), "Tools/Scripts/2to3.py"),
            ]
        else:
            command = ["2to3"]
    else:
        command = [sys.executable, "-m", "lib2to3"]

    command += ("-w", "-n", "--no-diffs", new_path)

    try:
        check_output(command, stderr=getNullOutput())

    except subprocess.CalledProcessError:
        if os.name == "nt":
            raise

        command[0:3] = ["2to3"]

        check_output(command, stderr=getNullOutput())

    data = getFileContents(new_path)

    with openTextFile(new_path, "w") as result_file:
        result_file.write("__file__ = %r\n" % os.path.abspath(path))
        result_file.write(data)

    return new_path, True


def decideFilenameVersionSkip(filename):
    """Make decision whether to skip based on filename and Python version.

    This codifies certain rules that files can have as suffixes or prefixes
    to make them be part of the set of tests executed for a version or not.

    Generally, an ening of "<major><minor>.py" indicates that it must be that
    Python version or higher. There is no need for ending in "26.py" as this
    is the minimum version anyway.

    The "_2.py" indicates a maxmimum version of 2.7, i.e. not Python 3.x, for
    language syntax no more supported.
    """

    # This will make many decisions with immediate returns.
    # pylint: disable=too-many-branches,too-many-return-statements

    assert type(filename) is str, repr(filename)

    # Skip runner scripts by default.
    if filename.startswith("run_"):
        return False

    if filename.endswith(".j2"):
        filename = filename[:-3]

    # Skip tests that require Python 2.7 at least.
    if filename.endswith("27.py") and _python_version < (2, 7):
        return False

    # Skip tests that require Python 2 at maximum.
    if filename.endswith("_2.py") and _python_version >= (3,):
        return False

    # Skip tests that require Python 3.7 at maximum.
    if filename.endswith("_37.py") and _python_version >= (3, 8):
        return False

    # Skip tests that require Python 3.2 at least.
    if filename.endswith("32.py") and _python_version < (3, 2):
        return False

    # Skip tests that require Python 3.3 at least.
    if filename.endswith("33.py") and _python_version < (3, 3):
        return False

    # Skip tests that require Python 3.4 at least.
    if filename.endswith("34.py") and _python_version < (3, 4):
        return False

    # Skip tests that require Python 3.5 at least.
    if filename.endswith("35.py") and _python_version < (3, 5):
        return False

    # Skip tests that require Python 3.6 at least.
    if filename.endswith("36.py") and _python_version < (3, 6):
        return False

    # Skip tests that require Python 3.7 at least.
    if filename.endswith("37.py") and _python_version < (3, 7):
        return False

    # Skip tests that require Python 3.8 at least.
    if filename.endswith("38.py") and _python_version < (3, 8):
        return False

    # Skip tests that require Python 3.9 at least.
    if filename.endswith("39.py") and _python_version < (3, 9):
        return False

    # Skip tests that require Python 3.10 at least.
    if filename.endswith("310.py") and _python_version < (3, 10):
        return False

    return True


def decideNeeds2to3(filename):
    return _python_version >= (3,) and not filename.endswith(
        (
            "32.py",
            "33.py",
            "34.py",
            "35.py",
            "36.py",
            "37.py",
            "38.py",
            "39.py",
            "310.py",
        )
    )


def _removeCPythonTestSuiteDir():
    # Cleanup, some tests apparently forget that.
    try:
        if os.path.isdir("@test"):
            removeDirectory("@test", ignore_errors=False)
        elif os.path.isfile("@test"):
            os.unlink("@test")
    except OSError:
        # TODO: Move this into removeDirectory maybe. Doing an external
        # call as last resort could be a good idea.

        # This seems to work for broken "lnk" files.
        if os.name == "nt":
            os.system("rmdir /S /Q @test")

        if os.path.exists("@test"):
            raise


def compareWithCPython(
    dirname, filename, extra_flags, search_mode, needs_2to3, on_error=None
):
    """Call the comparison tool. For a given directory filename.

    The search mode decides if the test case aborts on error or gets extra
    flags that are exceptions.

    """

    # Many cases to consider here, pylint: disable=too-many-branches

    if dirname is None:
        path = filename
    else:
        path = os.path.join(dirname, filename)

    # Apply 2to3 conversion if necessary.
    if needs_2to3:
        path, converted = convertUsing2to3(path)
    else:
        converted = False

    if os.getenv("NUITKA_TEST_INSTALLED", "") == "1":
        command = [
            sys.executable,
            "-m",
            "nuitka.tools.testing.compare_with_cpython",
            path,
            "silent",
        ]
    else:
        compare_with_cpython = os.path.join("..", "..", "bin", "compare_with_cpython")
        if os.path.exists(compare_with_cpython):
            command = [sys.executable, compare_with_cpython, path, "silent"]
        else:
            test_logger.sysexit("Error, cannot locate Nuitka comparison runner.")

    if extra_flags is not None:
        command += extra_flags

    command += search_mode.getExtraFlags(dirname, filename)

    # Cleanup before and after test stage directory.
    _removeCPythonTestSuiteDir()

    try:
        result = subprocess.call(command)
    except KeyboardInterrupt:
        result = 2

    # Cleanup before and after test stage directory.
    _removeCPythonTestSuiteDir()

    if result != 0 and result != 2 and search_mode.abortOnFinding(dirname, filename):
        if on_error is not None:
            on_error(dirname, filename)

        search_mode.onErrorDetected("Error exit! %s" % result)

    if converted:
        os.unlink(path)

    if result == 2:
        test_logger.sysexit("Interrupted, with CTRL-C\n", exit_code=2)


def checkCompilesNotWithCPython(dirname, filename, search_mode):
    if dirname is None:
        path = filename
    else:
        path = os.path.join(dirname, filename)

    command = [_python_executable, "-mcompileall", path]

    try:
        result = subprocess.call(command)
    except KeyboardInterrupt:
        result = 2

    if result != 1 and result != 2 and search_mode.abortOnFinding(dirname, filename):
        search_mode.onErrorDetected("Error exit! %s" % result)


def checkSucceedsWithCPython(filename):
    command = [_python_executable, filename]

    result = subprocess.call(command, stdout=getNullOutput(), stderr=subprocess.STDOUT)

    return result == 0


def hasDebugPython():
    # On Debian systems, these work.
    debug_python = os.path.join("/usr/bin/", os.environ["PYTHON"] + "-dbg")
    if os.path.exists(debug_python):
        return True

    # On Windows systems, these work.
    debug_python = os.environ["PYTHON"]
    if debug_python.lower().endswith(".exe"):
        debug_python = debug_python[:-4]
    debug_python = debug_python + "_d.exe"
    if os.path.exists(debug_python):
        return True

    # For other Python, if it's the one also executing the runner, which is
    # very probably the case, we check that. We don't check the provided
    # binary here, this could be done as well.
    if sys.executable == os.environ["PYTHON"] and hasattr(sys, "gettotalrefcount"):
        return True

    # Otherwise no.
    return False


def displayRuntimeTraces(logger, path):
    if not os.path.exists(path):
        # TODO: Have a logger package passed.
        logger.sysexit("Error, cannot find %r (%r)." % (path, os.path.abspath(path)))

    path = os.path.abspath(path)

    # TODO: Merge code for building command with below function, this is otherwise
    # horribly bad.

    if os.name == "posix":
        # Run with traces to help debugging, specifically in CI environment.
        if getOS() in ("Darwin", "FreeBSD"):
            test_logger.info("dtruss:")
            os.system("sudo dtruss %s" % path)
        else:
            test_logger.info("strace:")
            os.system("strace -s4096 -e file %s" % path)


def hasModule(module_name):
    result = subprocess.call(
        (os.environ["PYTHON"], "-c", "import %s" % module_name),
        stdout=getNullOutput(),
        stderr=subprocess.STDOUT,
    )

    return result == 0


m1 = {}
m2 = {}


def cleanObjRefCntMaps():
    m1.clear()
    m2.clear()

    # Warm out repr
    for x in gc.get_objects():
        try:
            str(x)
        except Exception:  # Catch all the things, pylint: disable=broad-except
            pass


def snapObjRefCntMap(before):
    # Inherently complex, pylint: disable=too-many-branches

    if before:
        m = m1
    else:
        m = m2

    m.clear()
    gc.collect()

    for x in gc.get_objects():
        # The dictionary is cyclic, and contains itself, avoid that.
        if x is m1 or x is m2:
            continue

        if type(x) is str and (x in m1 or x in m2):
            continue

        if type(x) is not str and isinstance(x, str):
            k = "str_overload_" + x.__class__.__name__ + str(x)
        elif type(x) is dict:
            if "__builtins__" in x:
                k = "<module dict %s>" % x["__name__"]
            elif "__spec__" in x and "__name__" in x:
                k = "<module dict %s>" % x["__name__"]
            else:
                k = str(x)
        elif x.__class__.__name__ == "compiled_frame":
            k = "<compiled_frame at xxx, line %d code %s" % (x.f_lineno, x.f_code)
        else:
            k = str(x)

        c = sys.getrefcount(x)

        if k in m:
            m[k] += c
        else:
            m[k] = c


orig_print = None


def disablePrinting():
    # Singleton, pylint: disable=global-statement
    global orig_print

    if orig_print is None:
        orig_print = __builtins__["print"]
        __builtins__["print"] = lambda *args, **kwargs: None


def reenablePrinting():
    # Singleton, pylint: disable=global-statement
    global orig_print

    if orig_print is not None:
        __builtins__["print"] = orig_print
        orig_print = None


_debug_python = hasattr(sys, "gettotalrefcount")


def getTotalReferenceCount():
    if _debug_python:
        gc.collect()
        return sys.gettotalrefcount()
    else:
        gc.collect()
        all_objects = gc.get_objects()

        # Sum object reference twice, once without the sum value type, then switch
        # the type, and use the type used to avoid the integers before that.
        result = 0.0
        for obj in all_objects:
            if type(obj) is float:
                continue

            result += sys.getrefcount(obj)

        result = int(result)

        for obj in all_objects:
            if type(obj) is not float:
                continue

            result += sys.getrefcount(obj)

        return result


def checkReferenceCount(checked_function, max_rounds=20, explain=False):
    # This is obviously going to be complex, pylint: disable=too-many-branches

    # Clean start conditions.
    assert sys.exc_info() == (None, None, None), sys.exc_info()

    my_print(checked_function.__name__ + ": ", end="")
    sys.stdout.flush()

    disablePrinting()

    # Make sure reference for these are already taken at the start.
    ref_count1 = 17
    ref_count2 = 17

    if explain:
        cleanObjRefCntMaps()

    assert max_rounds > 0

    result = False

    for count in range(max_rounds):
        if explain and count == max_rounds - 1:
            snapObjRefCntMap(before=True)

        ref_count1 = getTotalReferenceCount()

        checked_function()

        ref_count2 = getTotalReferenceCount()

        # Not allowed, but happens when bugs occur.
        assert sys.exc_info() == (None, None, None), sys.exc_info()

        if ref_count1 == ref_count2:
            result = True
            break

        if explain and count == max_rounds - 1:
            snapObjRefCntMap(before=False)

    reenablePrinting()

    if result:
        my_print("PASSED")
    else:
        my_print(
            "FAILED %d %d leaked %d" % (ref_count1, ref_count2, ref_count2 - ref_count1)
        )

        if explain:
            print("REPORT of differences:")
            assert m1
            assert m2

            # Using items will unwanted usages, pylint: disable=consider-using-dict-items
            for key in m1:
                if key not in m2:
                    my_print("*" * 80)
                    my_print("extra:", m1[key], key)
                elif m1[key] != m2[key]:
                    my_print("*" * 80)
                    my_print(m1[key], "->", m2[key], key)
                else:
                    pass

            for key in m2:
                if key not in m1:
                    my_print("*" * 80)
                    my_print("missing:", m2[key], key)

                    # print m1[key]

    assert sys.exc_info() == (None, None, None), sys.exc_info()

    gc.collect()
    sys.stdout.flush()

    return result


def createSearchMode():
    # Dealing with many options, pylint: disable=too-many-branches

    parser = OptionParser()

    select_group = OptionGroup(parser, "Select Tests")

    select_group.add_option(
        "--pattern",
        action="store",
        dest="pattern",
        default="",
        help="""\
Execute only tests matching the pattern. Defaults to all tests.""",
    )
    select_group.add_option(
        "--all",
        action="store_true",
        dest="all",
        default=False,
        help="""\
Execute all tests, continue execution even after failure of one.""",
    )

    parser.add_option_group(select_group)

    debug_group = OptionGroup(parser, "Test features")

    debug_group.add_option(
        "--debug",
        action="store_true",
        dest="debug",
        default=False,
        help="""\
Executing all self checks possible to find errors in Nuitka, good for test coverage.
Defaults to off.""",
    )

    debug_group.add_option(
        "--commands",
        action="store_true",
        dest="show_commands",
        default=False,
        help="""Output commands being done in output comparison.
Defaults to off.""",
    )

    parser.add_option_group(debug_group)

    options, positional_args = parser.parse_args()

    if options.debug:
        addExtendedExtraOptions("--debug")

    if options.show_commands:
        os.environ["NUITKA_TRACE_COMMANDS"] = "1"

    # Default to searching.
    mode = positional_args[0] if positional_args else "search"

    # Avoid having to use options style.
    if mode in ("search", "only"):
        if len(positional_args) >= 2 and not options.pattern:
            options.pattern = positional_args[1]

    if mode == "search":
        if options.all:
            return SearchModeAll()
        elif options.pattern:
            pattern = options.pattern.replace("/", os.path.sep)
            return SearchModeByPattern(pattern)
        else:
            return SearchModeImmediate()
    elif mode == "resume":
        return SearchModeResume(sys.modules["__main__"].__file__)
    elif mode == "only":
        if options.pattern:
            pattern = options.pattern.replace("/", os.path.sep)
            return SearchModeOnly(pattern)
        else:
            assert False
    elif mode == "coverage":
        return SearchModeCoverage()
    else:
        test_logger.sysexit("Error, using unknown search mode %r" % mode)


def reportSkip(reason, dirname, filename):
    case = os.path.join(dirname, filename)
    case = os.path.normpath(case)

    my_print("Skipped, %s (%s)." % (case, reason))


def executeReferenceChecked(prefix, names, tests_skipped, tests_stderr, explain=False):
    gc.disable()

    extract_number = lambda name: int(name.replace(prefix, ""))

    # Find the function names.
    matching_names = tuple(
        name for name in names if name.startswith(prefix) and name[-1].isdigit()
    )

    old_stderr = sys.stderr

    # Everything passed
    result = True

    for name in sorted(matching_names, key=extract_number):
        number = extract_number(name)

        # print(tests_skipped)
        if number in tests_skipped:
            my_print(name + ": SKIPPED (%s)" % tests_skipped[number])
            continue

        # Avoid unraisable output.
        try:
            if number in tests_stderr:
                sys.stderr = getNullOutput()
        except OSError:  # Windows
            if not checkReferenceCount(names[name], explain=explain):
                result = False
        else:
            if not checkReferenceCount(names[name], explain=explain):
                result = False

            if number in tests_stderr:
                new_stderr = sys.stderr
                sys.stderr = old_stderr
                new_stderr.close()

    gc.enable()
    return result


def addToPythonPath(python_path, in_front=False):
    if type(python_path) in (tuple, list):
        python_path = os.pathsep.join(python_path)

    if python_path:
        if "PYTHONPATH" in os.environ:
            if in_front:
                os.environ["PYTHONPATH"] = (
                    python_path + os.pathsep + os.environ["PYTHONPATH"]
                )
            else:
                os.environ["PYTHONPATH"] += os.pathsep + python_path
        else:
            os.environ["PYTHONPATH"] = python_path


@contextmanager
def withPythonPathChange(python_path):
    if python_path:
        if type(python_path) not in (tuple, list):
            python_path = python_path.split(os.pathsep)

        python_path = [
            os.path.normpath(os.path.abspath(element)) for element in python_path
        ]

        python_path = os.pathsep.join(python_path)

        if "PYTHONPATH" in os.environ:
            old_path = os.environ["PYTHONPATH"]
            os.environ["PYTHONPATH"] += os.pathsep + python_path
        else:
            old_path = None
            os.environ["PYTHONPATH"] = python_path

    yield

    if python_path:
        if old_path is None:
            del os.environ["PYTHONPATH"]
        else:
            os.environ["PYTHONPATH"] = old_path


def addExtendedExtraOptions(*args):
    old_value = os.environ.get("NUITKA_EXTRA_OPTIONS")

    value = old_value

    for arg in args:
        if value is None:
            value = arg
        else:
            value += " " + arg

    os.environ["NUITKA_EXTRA_OPTIONS"] = value

    return old_value


@contextmanager
def withExtendedExtraOptions(*args):
    assert args

    old_value = addExtendedExtraOptions(*args)

    yield

    if old_value is None:
        del os.environ["NUITKA_EXTRA_OPTIONS"]
    else:
        os.environ["NUITKA_EXTRA_OPTIONS"] = old_value


def indentedCode(codes, count):
    """Indent code, used for generating test codes."""
    return "\n".join(" " * count + line if line else "" for line in codes)


def convertToPython(doctests, line_filter=None):
    """Convert give doctest string to static Python code."""
    # This is convoluted, but it just needs to work, pylint: disable=too-many-branches

    import doctest

    code = doctest.script_from_examples(doctests)

    if code.endswith("\n"):
        code += "#\n"
    else:
        assert False

    output = []
    inside = False

    def getPrintPrefixed(evaluated, line_number):
        try:
            node = ast.parse(evaluated.lstrip(), "eval")
        except SyntaxError:
            return evaluated

        if node.body[0].__class__.__name__ == "Expr":
            count = 0

            while evaluated.startswith(" " * count):
                count += 1

            if sys.version_info < (3,):
                modified = (count - 1) * " " + "print " + evaluated
                return (
                    (count - 1) * " "
                    + ("print 'Line %d'" % line_number)
                    + "\n"
                    + modified
                )
            else:
                modified = (count - 1) * " " + "print(" + evaluated + "\n)\n"
                return (
                    (count - 1) * " "
                    + ("print('Line %d'" % line_number)
                    + ")\n"
                    + modified
                )
        else:
            return evaluated

    def getTried(evaluated, line_number):
        if sys.version_info < (3,):
            return """
try:
%(evaluated)s
except Exception as __e:
    print "Occurred", type(__e), __e
""" % {
                "evaluated": indentedCode(
                    getPrintPrefixed(evaluated, line_number).split("\n"), 4
                )
            }
        else:
            return """
try:
%(evaluated)s
except Exception as __e:
    print("Occurred", type(__e), __e)
""" % {
                "evaluated": indentedCode(
                    getPrintPrefixed(evaluated, line_number).split("\n"), 4
                )
            }

    def isOpener(evaluated):
        evaluated = evaluated.lstrip()

        if evaluated == "":
            return False

        return evaluated.split()[0] in (
            "def",
            "with",
            "class",
            "for",
            "while",
            "try:",
            "except",
            "except:",
            "finally:",
            "else:",
        )

    chunk = None
    for line_number, line in enumerate(code.split("\n")):
        # print "->", inside, line

        if line_filter is not None and line_filter(line):
            continue

        if inside and line and line[0].isalnum() and not isOpener(line):
            output.append(getTried("\n".join(chunk), line_number))

            chunk = []
            inside = False

        if inside and not (line.startswith("#") and line.find("SyntaxError:") != -1):
            chunk.append(line)
        elif line.startswith("#"):
            if line.find("SyntaxError:") != -1:
                # print "Syntax error detected"

                if inside:
                    # print "Dropping chunk", chunk

                    chunk = []
                    inside = False
                else:
                    del output[-1]
        elif isOpener(line):
            inside = True
            chunk = [line]
        elif line.strip() == "":
            output.append(line)
        else:
            output.append(getTried(line, line_number))

    return "\n".join(output).rstrip() + "\n"


def compileLibraryPath(search_mode, path, stage_dir, decide, action):
    my_print("Checking standard library path:", path)

    for root, dirnames, filenames in os.walk(path):
        dirnames_to_remove = [dirname for dirname in dirnames if "-" in dirname]

        for dirname in dirnames_to_remove:
            dirnames.remove(dirname)

        dirnames.sort()

        filenames = [filename for filename in filenames if decide(root, filename)]

        for filename in sorted(filenames):
            if not search_mode.consider(root, filename):
                continue

            full_path = os.path.join(root, filename)

            my_print(full_path, ":", end=" ")
            sys.stdout.flush()

            action(stage_dir, path, full_path)


def compileLibraryTest(search_mode, stage_dir, decide, action):
    if not os.path.exists(stage_dir):
        os.makedirs(stage_dir)

    my_dirname = os.path.join(os.path.dirname(__file__), "../../..")
    my_dirname = os.path.normpath(my_dirname)

    paths = [path for path in sys.path if not path.startswith(my_dirname)]

    my_print("Using standard library paths:")
    for path in paths:
        my_print(path)

    for path in paths:
        print("Checking path:", path)
        compileLibraryPath(
            search_mode=search_mode,
            path=path,
            stage_dir=stage_dir,
            decide=decide,
            action=action,
        )

    search_mode.finish()


def run_async(coro):
    """Execute a coroutine until it's done."""

    values = []
    result = None
    while True:
        try:
            values.append(coro.send(None))
        except StopIteration as ex:
            result = ex.args[0] if ex.args else None
            break
    return values, result


def async_iterate(g):
    """Execute async generator until it's done."""

    # Test code for Python3, catches all kinds of exceptions.
    # pylint: disable=broad-except

    # Also Python3 only, pylint: disable=I0021,undefined-variable

    res = []
    while True:
        try:
            g.__anext__().__next__()
        except StopAsyncIteration:
            res.append("STOP")
            break
        except StopIteration as ex:
            if ex.args:
                res.append("ex arg %s" % ex.args[0])
            else:
                res.append("EMPTY StopIteration")
                break
        except Exception as ex:
            res.append(str(type(ex)))

    return res


def getTestingCacheDir():
    cache_dir = getCacheDir()

    result = os.path.join(cache_dir, "tests_state")
    makePath(result)
    return result


def getTestingCPythonOutputsCacheDir():
    cache_dir = getCacheDir()

    result = os.path.join(
        cache_dir, "cpython_outputs", os.environ.get("NUITKA_TEST_SUITE", "")
    )

    makePath(result)
    return result


def scanDirectoryForTestCases(dirname, template_context=None):
    filenames = os.listdir(dirname)

    filenames = [
        filename
        for filename in filenames
        if (filename.endswith(".py") and not filename + ".j2" in filenames)
        or filename.endswith(".j2")
    ]

    for filename in sorted(filenames):
        if not decideFilenameVersionSkip(filename):
            continue

        if filename.endswith(".j2"):
            # Needs to be a dictionary with template arguments.
            assert template_context is not None

            template = getTemplate(
                package_name=None, template_name=filename, template_subdir=dirname
            )

            code = template.render(name=template.name, **template_context)

            filename = filename[:-3]
            with openTextFile(filename, "w") as output:
                output.write(
                    "'''Automatically generated test, not part of releases or git.\n\n'''\n"
                )

                output.write(code)

        yield filename


def scanDirectoryForTestCaseFolders(dirname):
    filenames = os.listdir(dirname)

    for filename in sorted(filenames):
        filename = os.path.join(dirname, filename)
        filename = os.path.relpath(filename)

        if (
            not os.path.isdir(filename)
            or filename.endswith(".build")
            or filename.endswith(".dist")
        ):
            continue

        filename_main = getMainProgramFilename(filename)

        yield filename, filename_main


def setupCacheHashSalt(test_code_path):
    assert os.path.exists(test_code_path)

    if os.path.exists(os.path.join(test_code_path, ".git")):
        git_cmd = ["git", "ls-tree", "-r", "HEAD", test_code_path]

        process = subprocess.Popen(
            args=git_cmd,
            stdin=getNullInput(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout_git, stderr_git = process.communicate()
        assert process.returncode == 0, stderr_git

        salt_value = hashlib.md5(stdout_git)
    else:
        salt_value = hashlib.md5()

        for filename in getFileList(test_code_path):
            if filename.endswith(".py"):
                salt_value.update(getFileContents(filename, mode="rb"))

    os.environ["NUITKA_HASH_SALT"] = salt_value.hexdigest()


def displayFolderContents(name, path):
    test_logger.info("Listing of %s %r:" % (name, path))

    if os.path.exists(path):
        if os.name == "nt":
            command = "dir /b /s /a:-D %s" % path
        else:
            command = "ls -Rla %s" % path

        os.system(command)
    else:
        test_logger.info("Does not exist.")


def displayFileContents(name, path):
    test_logger.info("Contents of %s %r:" % (name, path))

    if os.path.exists(path):
        for line in getFileContentByLine(path):
            my_print(line)
    else:
        test_logger.info("Does not exist.")


def someGenerator():
    yield 1
    yield 2
    yield 3


def someGeneratorRaising():
    yield 1
    raise TypeError(2)


# checks requirements needed to run each test module, according to the specified special comment
# special comments are in the following formats:
#     "# nuitka-skip-unless-expression: expression to be evaluated"
#       OR
#     "# nuitka-skip-unless-imports: module1,module2,..."
def checkRequirements(filename):
    for line in readSourceCodeFromFilename(None, filename).splitlines():
        if line.startswith("# nuitka-skip-unless-"):
            if line[21:33] == "expression: ":
                expression = line[33:]
                result = subprocess.call(
                    (
                        os.environ["PYTHON"],
                        "-c",
                        "import sys, os; sys.exit(not bool(%s))" % expression,
                    ),
                    stdout=getNullOutput(),
                    stderr=subprocess.STDOUT,
                )
                if result != 0:
                    return (False, "Expression '%s' evaluated to false" % expression)

            elif line[21:30] == "imports: ":
                imports_needed = line[30:].rstrip().split(",")
                for i in imports_needed:
                    if not hasModule(i):
                        return (
                            False,
                            i
                            + " not installed for this Python version, but test needs it",
                        )
    # default return value
    return (True, "")


class DelayedExecutionThread(threading.Thread):
    def __init__(self, timeout, func):
        threading.Thread.__init__(self)
        self.timeout = timeout

        self.func = func

    def run(self):
        time.sleep(self.timeout)
        self.func()


def executeAfterTimePassed(timeout, func):
    alarm = DelayedExecutionThread(timeout=timeout, func=func)
    alarm.start()


def killProcess(name, pid):
    """Kill a process in a portable way.

    Right now SIGINT is used, unclear what to do on Windows
    with Python2 or non-related processes.
    """

    if str is bytes and os.name == "nt":
        test_logger.info("Using taskkill on test process %r." % name)
        os.system("taskkill.exe /PID %d" % pid)
    else:
        test_logger.info("Killing test process %r." % name)
        os.kill(pid, signal.SIGINT)


def checkLoadedFileAccesses(loaded_filenames, current_dir):
    # Many details to consider, pylint: disable=too-many-branches,too-many-statements

    current_dir = os.path.normpath(current_dir)
    current_dir = os.path.normcase(current_dir)
    current_dir_ext = os.path.normcase(getExternalUsePath(current_dir))

    illegal_accesses = []

    for loaded_filename in loaded_filenames:
        orig_loaded_filename = loaded_filename

        loaded_filename = os.path.normpath(loaded_filename)
        loaded_filename = os.path.normcase(loaded_filename)
        loaded_basename = os.path.basename(loaded_filename)

        if os.name == "nt":
            if areSamePaths(
                os.path.dirname(loaded_filename),
                os.path.normpath(os.path.join(os.environ["SYSTEMROOT"], "System32")),
            ):
                continue
            if areSamePaths(
                os.path.dirname(loaded_filename),
                os.path.normpath(os.path.join(os.environ["SYSTEMROOT"], "SysWOW64")),
            ):
                continue

            if r"windows\winsxs" in loaded_filename:
                continue

            # Github actions have these in PATH overriding SYSTEMROOT
            if r"windows performance toolkit" in loaded_filename:
                continue
            if r"powershell" in loaded_filename:
                continue
            if r"azure dev spaces cli" in loaded_filename:
                continue
            if r"tortoisesvn" in loaded_filename:
                continue

        if loaded_filename.startswith(current_dir):
            continue

        if loaded_filename.startswith(os.path.abspath(current_dir)):
            continue

        if loaded_filename.startswith(current_dir_ext):
            continue

        ignore = True
        for ignored_dir in (
            # System configuration is OK
            "/etc",
            "/usr/etc",
            "/usr/local/etc",
            # Runtime user state and kernel information is OK.
            "/proc",
            "/dev",
            "/run",
            "/sys",
            "/tmp",
            "/var",
            # Locals may of course be loaded.
            "/usr/lib/locale",
            "/usr/share/locale",
            "/usr/share/X11/locale",
            # Themes may of course be loaded.
            "/usr/share/themes",
            # Terminal info files are OK too.
            "/lib/terminfo",
        ):
            if isPathBelowOrSameAs(ignored_dir, loaded_filename):
                ignore = False
                break
        if not ignore:
            continue

        # Themes may of course be loaded.
        if loaded_filename.startswith("/usr/share/themes"):
            continue
        if "gtk" in loaded_filename and "/engines/" in loaded_filename:
            continue

        if loaded_filename in (
            "/usr",
            "/usr/local",
            "/usr/local/lib",
            "/usr/share",
            "/usr/local/share",
            "/usr/lib64",
        ):
            continue

        # TCL/tk for tkinter for non-Windows is OK.
        if loaded_filename.startswith(
            (
                "/usr/lib/tcltk/",
                "/usr/share/tcltk/",
                "/usr/lib/tcl/",
                "/usr/lib64/tcl/",
            )
        ):
            continue
        if loaded_filename in (
            "/usr/lib/tcltk",
            "/usr/share/tcltk",
            "/usr/lib/tcl",
            "/usr/lib64/tcl",
        ):
            continue

        if loaded_filename in (
            "/lib",
            "/lib64",
            "/lib/sse2",
            "/lib/tls",
            "/lib64/tls",
            "/usr/lib/sse2",
            "/usr/lib/tls",
            "/usr/lib64/tls",
        ):
            continue

        if loaded_filename in ("/usr/share/tcl8.6", "/usr/share/tcl8.5"):
            continue
        if loaded_filename in (
            "/usr/share/tcl8.6/init.tcl",
            "/usr/share/tcl8.5/init.tcl",
        ):
            continue
        if loaded_filename in (
            "/usr/share/tcl8.6/encoding",
            "/usr/share/tcl8.5/encoding",
        ):
            continue

        # System SSL config on Linux. TODO: Should this not be included and
        # read from dist folder.
        if loaded_basename == "openssl.cnf":
            continue

        # Taking these from system is harmless and desirable
        if loaded_basename.startswith(("libz.so", "libgcc_s.so")):
            continue

        # System C libraries are to be expected.
        if loaded_basename.startswith(
            (
                "ld-linux-x86-64.so",
                "libc.so.",
                "libpthread.so.",
                "libm.so.",
                "libdl.so.",
                "libBrokenLocale.so.",
                "libSegFault.so",
                "libanl.so.",
                "libcidn.so.",
                "libcrypt.so.",
                "libmemusage.so",
                "libmvec.so.",
                "libnsl.so.",
                "libnss_compat.so.",
                "libnss_db.so.",
                "libnss_dns.so.",
                "libnss_files.so.",
                "libnss_hesiod.so.",
                "libnss_nis.so.",
                "libnss_nisplus.so.",
                "libpcprofile.so",
                "libresolv.so.",
                "librt.so.",
                "libthread_db-1.0.so",
                "libthread_db.so.",
                "libutil.so.",
            )
        ):
            continue

        # System C++ standard library is also OK.
        if loaded_basename.startswith("libstdc++."):
            continue

        # Curses library is OK from system too.
        if loaded_basename.startswith("libtinfo.so."):
            continue

        # Loaded by C library potentially for DNS lookups.
        if loaded_basename.startswith(
            (
                "libnss_",
                "libnsl",
                # Some systems load a lot more, this is CentOS 7 on OBS
                "libattr.so.",
                "libbz2.so.",
                "libcap.so.",
                "libdw.so.",
                "libelf.so.",
                "liblzma.so.",
                # Some systems load a lot more, this is Fedora 26 on OBS
                "libselinux.so.",
                "libpcre.so.",
                # And this is Fedora 29 on OBS
                "libblkid.so.",
                "libmount.so.",
                "libpcre2-8.so.",
                # CentOS 8 on OBS
                "libuuid.so.",
            )
        ):
            continue

        # Loaded by dtruss on macOS X.
        if loaded_filename.startswith("/usr/lib/dtrace/"):
            continue

        # Loaded by cowbuilder and pbuilder on Debian
        if loaded_basename == ".ilist":
            continue
        if "cowdancer" in loaded_filename:
            continue
        if "eatmydata" in loaded_filename:
            continue

        # Loading from home directories is OK too.
        if (
            loaded_filename.startswith("/home/")
            or loaded_filename.startswith("/data/")
            or loaded_filename.startswith("/root/")
            or loaded_filename in ("/home", "/data", "/root")
        ):
            continue

        # For Debian builders, /build is OK too.
        if loaded_filename.startswith("/build/") or loaded_filename == "/build":
            continue

        # TODO: Unclear, loading gconv from filesystem of installed system
        # may be OK or not. I think it should be.
        if loaded_basename == "gconv-modules.cache":
            continue
        if "/gconv/" in loaded_filename:
            continue
        if loaded_basename.startswith("libicu"):
            continue
        if loaded_filename.startswith("/usr/share/icu/"):
            continue

        # Loading from caches is OK.
        if loaded_filename.startswith("/var/cache/"):
            continue

        # At least Python3.7 considers the default Python3 path and checks it.
        if loaded_filename == "/usr/bin/python3":
            continue

        # Accessing the versioned Python3.x binary is also happening.
        if loaded_filename in (
            "/usr/bin/python3." + version for version in ("5", "6", "7", "8", "9", "10")
        ):
            continue

        binary_path = _python_executable

        found = False
        while binary_path:
            if loaded_filename == binary_path:
                found = True
                break

            if binary_path == os.path.dirname(binary_path):
                break

            binary_path = os.path.dirname(binary_path)

            if loaded_filename == os.path.join(
                binary_path,
                "python" + ("%d%d" % (_python_version[0], _python_version[1])),
            ):
                found = True
                break

        if found:
            continue

        lib_prefix_dir = "/usr/lib/python%d.%s" % (
            _python_version[0],
            _python_version[1],
        )

        # PySide accesses its directory.
        if loaded_filename == os.path.join(lib_prefix_dir, "dist-packages/PySide"):
            continue

        # GTK accesses package directories only.
        if loaded_filename == os.path.join(lib_prefix_dir, "dist-packages/gtk-2.0/gtk"):
            continue
        if loaded_filename == os.path.join(lib_prefix_dir, "dist-packages/glib"):
            continue
        if loaded_filename == os.path.join(lib_prefix_dir, "dist-packages/gtk-2.0/gio"):
            continue
        if loaded_filename == os.path.join(lib_prefix_dir, "dist-packages/gobject"):
            continue

        # PyQt5 and PySide6 seems to do this, but won't use contents then.
        if loaded_filename in (
            "/usr/lib/qt6/plugins",
            "/usr/lib/qt6",
            "/usr/lib64/qt6/plugins",
            "/usr/lib64/qt6",
            "/usr/lib/qt5/plugins",
            "/usr/lib/qt5",
            "/usr/lib64/qt5/plugins",
            "/usr/lib64/qt5",
            "/usr/lib/x86_64-linux-gnu/qt5/plugins",
            "/usr/lib/x86_64-linux-gnu/qt5",
            "/usr/lib/x86_64-linux-gnu",
            "/usr/lib",
        ):
            continue

        # Can look at the interpreters of the system.
        if loaded_basename in "python3":
            continue
        if loaded_basename in (
            "python%s" + supported_version
            for supported_version in (
                getSupportedPythonVersions() + getPartiallySupportedPythonVersions()
            )
        ):
            continue

        # Current Python executable can actually be a symlink and
        # the real executable which it points to will be on the
        # loaded_filenames list. This is all fine, let's ignore it.
        # Also, because the loaded_filename can be yet another symlink
        # (this is weird, but it's true), let's better resolve its real
        # path too.
        if os.path.realpath(loaded_filename) == os.path.realpath(sys.executable):
            continue

        # Accessing SE-Linux is OK.
        if loaded_filename in ("/sys/fs/selinux", "/selinux"):
            continue

        # Looking at device is OK.
        if loaded_filename.startswith("/sys/devices/"):
            continue

        # Allow reading time zone info of local system.
        if loaded_filename.startswith("/usr/share/zoneinfo/"):
            continue

        # The access to .pth files has no effect.
        if loaded_filename.endswith(".pth"):
            continue

        # Looking at site-package dir alone is alone.
        if loaded_filename.endswith(("site-packages", "dist-packages")):
            continue

        # QtNetwork insist on doing this it seems.
        if loaded_basename.startswith(("libcrypto.so", "libssl.so")):
            continue

        # macOS uses these:
        if loaded_basename in (
            "libcrypto.1.0.0.dylib",
            "libssl.1.0.0.dylib",
            "libcrypto.1.1.dylib",
        ):
            continue

        # Linux onefile uses this
        if loaded_basename.startswith("libfuse.so."):
            continue

        # MSVC run time DLLs, due to SxS come from system.
        if loaded_basename.upper() in ("MSVCRT.DLL", "MSVCR90.DLL"):
            continue

        illegal_accesses.append(orig_loaded_filename)

    return illegal_accesses


def getMainProgramFilename(filename):
    for filename_main in os.listdir(filename):
        if filename_main.endswith(("Main.py", "Main")):
            return filename_main

    test_logger.sysexit(
        """\
Error, no file ends with 'Main.py' or 'Main' in '%s', incomplete test case."""
        % (filename)
    )
