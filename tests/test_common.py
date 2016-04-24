#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from __future__ import print_function

import os, sys, subprocess, tempfile, atexit, shutil, re, ast

# Make sure we flush after every print, the "-u" option does more than that
# and this is easy enough.
def my_print(*args, **kwargs):
    print(*args, **kwargs)

    sys.stdout.flush()


def check_output(*popenargs, **kwargs):
    if "stdout" in kwargs:
        raise ValueError("stdout argument not allowed, it will be overridden.")

    process = subprocess.Popen(
        stdout = subprocess.PIPE,
        *popenargs,
        **kwargs
    )
    output, _unused_err = process.communicate()
    retcode = process.poll()

    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, output = output)

    return output

def check_result(*popenargs, **kwargs):
    if "stdout" in kwargs:
        raise ValueError("stdout argument not allowed, it will be overridden.")

    process = subprocess.Popen(
        stdout = subprocess.PIPE,
        *popenargs,
        **kwargs
    )
    _unused_output, _unused_err = process.communicate()
    retcode = process.poll()

    if retcode:
        return False
    else:
        return True


def setup(needs_io_encoding = False, silent = False):
    # Go its own directory, to have it easy with path knowledge.
    os.chdir(
        os.path.dirname(
            os.path.abspath(sys.modules[ "__main__" ].__file__)
        )
    )

    if "PYTHON" not in os.environ:
        os.environ["PYTHON"] = sys.executable

    # Allow providing 33, 27, and expand that to python2.7
    if len(os.environ["PYTHON"]) == 2 and \
       os.environ["PYTHON"].isdigit() and \
       os.name != "nt":

        os.environ["PYTHON"] = "python%s.%s" % (
            os.environ["PYTHON"][0],
            os.environ["PYTHON"][1]
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
""",
        ),
        stderr = subprocess.STDOUT
    )

    global python_version, python_arch
    python_version = version_output.split(b"\n")[0].strip()
    python_arch = version_output.split(b"\n")[1].strip()

    if sys.version.startswith('3'):
        python_arch = python_arch.decode()
        python_version = python_version.decode()

    os.environ["PYTHON_VERSION"] = python_version

    if not silent:
        my_print("Using concrete python", python_version, "on", python_arch)

    assert type(python_version) is str, repr(python_version)
    assert type(python_arch) is str, repr(python_arch)

    if "COVERAGE_FILE" not in os.environ:
        os.environ["COVERAGE_FILE"] = os.path.join(
            os.path.dirname(__file__),
            "..",
            ".coverage"
        )

    return python_version


tmp_dir = None

def getTempDir():
    # Create a temporary directory to work in, automatically remove it in case
    # it is empty in the end.
    global tmp_dir

    if tmp_dir is None:
        tmp_dir = tempfile.mkdtemp(
            prefix = os.path.basename(
                os.path.dirname(
                    os.path.abspath(sys.modules[ "__main__" ].__file__)
                )
            ) + '-',
            dir    = tempfile.gettempdir() if
                         not os.path.exists("/var/tmp") else
                    "/var/tmp"
        )

        def removeTempDir():
            try:
                shutil.rmtree(tmp_dir)
            except OSError:
                pass

        atexit.register(removeTempDir)

    return tmp_dir


def convertUsing2to3(path, force = False):
    command = [
        os.environ["PYTHON"],
        "-m",
        "py_compile",
        path
    ]

    if not force:
        with open(path) as source_file:
            if "xrange" not in source_file.read():
                with open(os.devnull, 'w') as stderr:
                    if check_result(command, stderr = stderr):
                        return path, False

    filename = os.path.basename(path)

    new_path = os.path.join(getTempDir(), filename)
    shutil.copy(path, new_path)

    # On Windows, we cannot rely on 2to3 to be in the path.
    if os.name == "nt":
        command = [
            sys.executable,
            os.path.join(
                os.path.dirname(sys.executable),
                "Tools/Scripts/2to3.py"
            )
        ]
    else:
        command = [
            "2to3"
        ]

    command += [
        "-w",
        "-n",
        "--no-diffs",
        new_path
    ]

    with open(os.devnull, 'w') as devnull:
        check_output(
            command,
            stderr = devnull
        )

    return new_path, True


def decideFilenameVersionSkip(filename):
    assert type(filename) is str
    assert type(python_version) is str

    # Skip runner scripts by default.
    if filename.startswith("run_"):
        return False

    # Skip tests that require Python 2.7 at least.
    if filename.endswith("27.py") and python_version.startswith("2.6"):
        return False

    if filename.endswith("_2.py") and python_version.startswith('3'):
        return False

    # Skip tests that require Python 3.2 at least.
    if filename.endswith("32.py") and python_version < "3.2":
        return False

    # Skip tests that require Python 3.3 at least.
    if filename.endswith("33.py") and python_version < "3.3":
        return False

    # Skip tests that require Python 3.4 at least.
    if filename.endswith("34.py") and python_version < "3.4":
        return False

    # Skip tests that require Python 3.5 at least.
    if filename.endswith("35.py") and python_version < "3.5":
        return False

    return True


def compareWithCPython(dirname, filename, extra_flags, search_mode, needs_2to3):
    if dirname is None:
        path = filename
    else:
        path = os.path.join(dirname, filename)

    # Apply 2to3 conversion if necessary.
    if needs_2to3:
        path, converted = convertUsing2to3(path)
    else:
        converted = False

    command = [
        sys.executable,
        os.path.join("..", "..", "bin", "compare_with_cpython"),
        path,
        "silent"
    ]

    if extra_flags is not None:
        command += extra_flags

    command += search_mode.getExtraFlags(dirname, filename)

    try:
        result = subprocess.call(
            command
        )
    except KeyboardInterrupt:
        result = 2

    # Cleanup, some tests apparently forget that.
    try:
        if os.path.isdir("@test"):
            shutil.rmtree("@test")
        elif os.path.isfile("@test"):
            os.unlink("@test")
    except OSError:
        # This seems to work for broken "lnk" files.
        if os.name == "nt":
            os.system("rmdir /S /Q @test")

        if os.path.exists("@test"):
            raise

    if result != 0 and \
       result != 2 and \
       search_mode.abortOnFinding(dirname, filename):
        my_print("Error exit!", result)
        sys.exit(result)

    if converted:
        os.unlink(path)

    if result == 2:
        sys.stderr.write("Interrupted, with CTRL-C\n")
        sys.exit(2)


def hasDebugPython():
    global python_version

    # On Debian systems, these work.
    debug_python = os.path.join("/usr/bin/", os.environ["PYTHON"] + "-dbg")
    if os.path.exists(debug_python):
        return True

    # For other Python, if it's the one also executing the runner, which is
    # very probably the case, we check that. We don't check the provided
    # binary here, this could be done as well.
    if sys.executable == os.environ["PYTHON"] and \
       hasattr(sys, "gettotalrefcount"):
        return True

    # Otherwise no.
    return False


def getArchitecture():
    if os.name == "nt":
        if "AMD64" in sys.version:
            return "x86_64"
        else:
            return "x86"
    else:
        return os.uname()[4]


def getDependsExePath():
    if "APPDATA" not in os.environ:
        sys.exit("Error, standalone mode cannot find 'APPDATA' environment.")

    nuitka_app_dir = os.path.join(os.environ["APPDATA"],"nuitka")

    depends_dir = os.path.join(
        nuitka_app_dir,
        python_arch,
    )
    depends_exe = os.path.join(
        depends_dir,
        "depends.exe"
    )

    assert os.path.exists(depends_exe), depends_exe

    return depends_exe

def isExecutableCommand(command):
    path = os.environ["PATH"]

    suffixes = (".exe",) if os.name == "nt" else ("",)

    for part in path.split(os.pathsep):
        if not part:
            continue

        for suffix in suffixes:
            if os.path.isfile(os.path.join(part, command + suffix)):
                return True

    return False


def getRuntimeTraceOfLoadedFiles(path, trace_error = True):
    """ Returns the files loaded when executing a binary. """

    result = []

    if os.name == "posix":
        if sys.platform == "darwin" or \
           sys.platform.startswith("freebsd"):
            if not isExecutableCommand("dtruss"):
                sys.exit(
                    """\
Error, needs 'dtruss' on your system to scan used libraries."""
                )

            if not isExecutableCommand("sudo"):
                sys.exit(
                    """\
Error, needs 'sudo' on your system to scan used libraries."""
                )

            args = (
                "sudo",
                "dtruss",
                "-t",
                "open",
                path
            )
        else:
            if not isExecutableCommand("strace"):
                sys.exit(
                    """\
Error, needs 'strace' on your system to scan used libraries."""
                )

            args = (
                "strace",
                "-e", "file",
                "-s4096", # Some paths are truncated otherwise.
                path
            )

        process = subprocess.Popen(
            args   = args,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        _stdout_strace, stderr_strace = process.communicate()

        open(path+".strace","wb").write(stderr_strace)

        for line in stderr_strace.split(b"\n"):
            if process.returncode != 0 and trace_error:
                my_print(line)

            if not line:
                continue

            # Don't consider files not found. The "site" module checks lots
            # of things.
            if b"ENOENT" in line:
                continue

            if line.startswith(b"stat(") and b"S_IFDIR" in line:
                continue

            # Allow stats on the python binary, and stuff pointing to the
            # standard library, just not uses of it. It will search there
            # for stuff.
            if line.startswith(b"lstat(") or \
               line.startswith(b"stat(") or \
               line.startswith(b"readlink("):
                filename = line[line.find(b"(")+2:line.find(b", ")-1]

                if filename in (b"/usr", b"/usr/bin"):
                    continue

                if filename == b"/usr/bin/python" + python_version[:3].encode("utf8"):
                    continue

                if filename in (b"/usr/bin/python", b"/usr/bin/python2",
                                b"/usr/bin/python3"):
                    continue

            result.extend(
                os.path.abspath(match)
                for match in
                re.findall(b'"(.*?)(?:\\\\0)?"', line)
            )

        if sys.version.startswith('3'):
            result = [s.decode("utf-8") for s in result]
    elif os.name == "nt":
        subprocess.call(
            (
                getDependsExePath(),
                "-c",
                "-ot%s" % path + ".depends",
                "-f1",
                "-pa1",
                "-ps1",
                "-pp0",
                "-pl1",
                path
            )
        )

        inside = False
        for line in open(path + ".depends"):
            if "| Module Dependency Tree |" in line:
                inside = True
                continue

            if not inside:
                continue

            if "| Module List |" in line:
                break

            if ']' not in line:
                continue

            # Skip missing DLLs, apparently not needed anyway.
            if '?' in line[:line.find(']')]:
                continue

            dll_filename = line[line.find(']')+2:-1]
            assert os.path.isfile(dll_filename), dll_filename

            # The executable itself is of course exempted.
            if os.path.normcase(dll_filename) == \
                os.path.normcase(os.path.abspath(path)):
                continue

            dll_filename = os.path.normcase(dll_filename)

            result.append(dll_filename)

        os.unlink(path + ".depends")

    result = list(sorted(set(result)))

    return result


def hasModule(module_name):
    result = subprocess.call(
        (
            os.environ["PYTHON"],
            "-c"
            "import %s" % module_name
        ),
        stdout = open(os.devnull,'w'),
        stderr = subprocess.STDOUT
    )

    return result == 0


m1 = {}
m2 = {}

def snapObjRefCntMap(before):
    import gc

    if before:
        global m1
        m = m1
    else:
        global m2
        m = m2

    for x in gc.get_objects():
        if x is m1:
            continue

        if x is m2:
            continue

        m[ str(x) ] = sys.getrefcount(x)


def checkReferenceCount(checked_function, max_rounds = 10):
    assert sys.exc_info() == (None, None, None), sys.exc_info()

    print(checked_function.__name__ + ": ", end = "")
    sys.stdout.flush()

    ref_count1 = 17
    ref_count2 = 17

    explain = False

    import gc

    assert max_rounds > 0
    for count in range(max_rounds):
        gc.collect()
        ref_count1 = sys.gettotalrefcount()  # @UndefinedVariable

        if explain and count == max_rounds - 1:
            snapObjRefCntMap(True)

        checked_function()

        # Not allowed, but happens when bugs occur.
        assert sys.exc_info() == (None, None, None), sys.exc_info()

        gc.collect()

        if explain and count == max_rounds - 1:
            snapObjRefCntMap(False)

        ref_count2 = sys.gettotalrefcount()  # @UndefinedVariable

        if ref_count1 == ref_count2:
            result = True
            print("PASSED")
            break

        # print count, ref_count1, ref_count2
    else:
        result = False
        print("FAILED", ref_count1, ref_count2, "leaked", ref_count2 - ref_count1)

        if explain:
            assert m1
            assert m2

            for key in m1.keys():
                if key not in m2:
                    print('*' * 80)
                    print(key)
                elif m1[key] != m2[key]:
                    print('*' * 80)
                    print(key)
                else:
                    pass
                    # print m1[key]

    assert sys.exc_info() == (None, None, None), sys.exc_info()

    gc.collect()
    sys.stdout.flush()

    return result


def createSearchMode():
    search_mode = len(sys.argv) > 1 and sys.argv[1] == "search"
    start_at = sys.argv[2] if len(sys.argv) > 2 else None
    coverage_mode = len(sys.argv) > 1 and sys.argv[1] == "coverage"

    class SearchModeBase:
        def __init__(self):
            self.may_fail = []

        def consider(self, dirname, filename):
            return True

        def finish(self):
            pass

        def abortOnFinding(self, dirname, filename):
            for candidate in self.may_fail:
                if self._match(dirname, filename, candidate):
                    return False

            return True

        def getExtraFlags(self, dirname, filename):
            return []

        def mayFailFor(self, *names):
            self.may_fail += names

        def _match(self, dirname, filename, candidate):
            parts = [dirname, filename]

            while None in parts:
                parts.remove(None)
            assert parts

            path = os.path.join(*parts)

            return candidate in (
                dirname,
                filename,
                filename.replace(".py", ""),
                filename.split(".")[0],
                path,
                path.replace(".py", ""),

            )

        def isCoverage(self):
            return False

    if coverage_mode:
        class SearchModeCoverage(SearchModeBase):
            def getExtraFlags(self, dirname, filename):
                return ["coverage"]

            def isCoverage(self):
                return True

        return SearchModeCoverage()
    elif search_mode and start_at:
        start_at = start_at.replace('/', os.path.sep)

        class SearchModeByPattern(SearchModeBase):
            def __init__(self):
                SearchModeBase.__init__(self)

                self.active = False

            def consider(self, dirname, filename):
                if self.active:
                    return True

                self.active = self._match(dirname, filename, start_at)
                return self.active

            def finish(self):
                if not self.active:
                    sys.exit("Error, became never active.")


        return SearchModeByPattern()
    else:
        class SearchModeImmediate(SearchModeBase):
            def abortOnFinding(self, dirname, filename):
                return search_mode and \
                       SearchModeBase.abortOnFinding(self, dirname, filename)

        return SearchModeImmediate()

def reportSkip(reason, dirname, filename):
    my_print("Skipped, %s (%s)." % (os.path.join(dirname, filename), reason))

def executeReferenceChecked(prefix, names, tests_skipped, tests_stderr):
    import gc
    gc.disable()

    extract_number = lambda name: int(name.replace(prefix, ""))

    # Find the function names.
    matching_names = tuple(
        name
        for name in names
        if name.startswith(prefix) and name[-1].isdigit()
    )

    old_stderr = sys.stderr

    # Everything passed
    result = True

    for name in sorted(matching_names, key = extract_number):
        number = extract_number(name)

        # print(tests_skipped)
        if number in tests_skipped:
            my_print(name + ": SKIPPED (%s)" % tests_skipped[number])
            continue

        # Avoid unraisable output.
        try:
            if number in tests_stderr:
                sys.stderr = open(os.devnull, "wb")
        except Exception: # Windows
            if not checkReferenceCount(names[name]):
                result = False
        else:
            if not checkReferenceCount(names[name]):
                result = False

            if number in tests_stderr:
                new_stderr = sys.stderr
                sys.stderr = old_stderr
                new_stderr.close()

    gc.enable()
    return result

from contextlib import contextmanager

@contextmanager
def withPythonPathChange(python_path):
    if type(python_path) in (tuple, list):
        python_path = os.pathsep.join(python_path)

    if python_path:
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

@contextmanager
def withExtendedExtraOptions(*args):
    assert args
    old_value = os.environ.get("NUITKA_EXTRA_OPTIONS", None)

    value = old_value

    for arg in args:
        if value is None:
            value = arg
        else:
            value += ' ' + arg

    os.environ[ "NUITKA_EXTRA_OPTIONS" ] = value

    yield

    if old_value is None:
        del os.environ[ "NUITKA_EXTRA_OPTIONS" ]
    else:
        os.environ[ "NUITKA_EXTRA_OPTIONS" ] = old_value


def indentedCode(codes, count):
    """ Indent code, used for generating test codes.

    """
    return '\n'.join( ' ' * count + line if line else "" for line in codes )


def convertToPython(doctests, line_filter = None):
    """ Convert give doctest string to static Python code.

    """
    import doctest
    code = doctest.script_from_examples(doctests)

    if code.endswith('\n'):
        code += "#\n"
    else:
        assert False

    output = []
    inside = False

    def getPrintPrefixed(evaluated):
        try:
            node = ast.parse(evaluated.lstrip(), "eval")
        except SyntaxError:
            return evaluated

        if node.body[0].__class__.__name__ == "Expr":
            count = 0

            while evaluated.startswith(' ' * count):
                count += 1

            if sys.version_info < (3,):
                modified = (count-1) * ' ' + "print " + evaluated
                return (count-1) * ' ' + ("print 'Line %d'" % line_number) + "\n" + modified
            else:
                modified = (count-1) * ' ' + "print(" + evaluated + "\n)\n"
                return (count-1) * ' ' + ("print('Line %d'" % line_number) + ")\n" + modified
        else:
            return evaluated

    def getTried(evaluated):
        if sys.version_info < (3,):
            return """
try:
%(evaluated)s
except Exception as __e:
    print "Occurred", type(__e), __e
""" % { "evaluated" : indentedCode(getPrintPrefixed(evaluated).split('\n'), 4) }
        else:
            return """
try:
%(evaluated)s
except Exception as __e:
    print("Occurred", type(__e), __e)
""" % { "evaluated" : indentedCode(getPrintPrefixed(evaluated).split('\n'), 4) }

    def isOpener(evaluated):
        evaluated = evaluated.lstrip()

        if evaluated == "":
            return False

        if evaluated.split()[0] in ("def", "class", "for", "while", "try:", "except", "except:", "finally:", "else:"):
            return True
        else:
            return False

    for line_number, line in enumerate(code.split('\n')):
        # print "->", inside, line

        if line_filter is not None and line_filter(line):
            continue

        if inside and len(line) > 0 and line[0].isalnum() and not isOpener(line):
            output.append(getTried('\n'.join(chunk)))  # @UndefinedVariable

            chunk = []
            inside = False

        if inside and not (line.startswith('#') and line.find("SyntaxError:") != -1):
            chunk.append(line)
        elif line.startswith('#'):
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
            output.append(getTried(line))

    return '\n'.join(output).rstrip() + '\n'


def compileLibraryPath(search_mode, path, stage_dir, decide, action):
    my_print("Checking standard library path:", path)
    global active

    for root, dirnames, filenames in os.walk(path):
        dirnames_to_remove = [
            dirname
            for dirname in dirnames
            if "-" in dirname
        ]

        for dirname in dirnames_to_remove:
            dirnames.remove(dirname)

        dirnames.sort()

        filenames = [
            filename
            for filename in filenames
            if decide(root, filename)
        ]

        for filename in sorted(filenames):
            if not search_mode.consider(root, filename):
                continue

            full_path = os.path.join(root, filename)

            my_print(full_path, ':', end = ' ')
            sys.stdout.flush()

            action(stage_dir, path, full_path)


def compileLibraryTest(search_mode, stage_dir, decide, action):
    my_dirname = os.path.dirname(__file__)

    paths = [
        path
        for path in
        sys.path
        if not path.startswith(my_dirname)
    ]

    my_print("Using standard library paths:")
    for path in paths:
        my_print(path)


    for path in paths:
        compileLibraryPath(
            search_mode = search_mode,
            path        = path,
            stage_dir   = stage_dir,
            decide      = decide,
            action      = action
        )
