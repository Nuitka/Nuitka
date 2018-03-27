#!/usr/bin/env python
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

""" Tool to compare output of CPython and Nuitka.

"""

from __future__ import print_function

import difflib
import os
import re
import subprocess
import sys
import tempfile
import time

from nuitka.tools.testing.Common import addToPythonPath, withPythonPathChange

ran_tests_re                 = re.compile(r"^(Ran \d+ tests? in )\-?\d+\.\d+s$")
instance_re                  = re.compile(r"at (?:0x)?[0-9a-fA-F]+(;?\s|\>)")
thread_re                    = re.compile(r"Thread 0x[0-9a-fA-F]+")
compiled_types_re            = re.compile(r"compiled_(module|function|generator|method|frame|coroutine)")
module_repr_re               = re.compile(r"(\<module '.*?' from ').*?('\>)")

global_name_error_re         = re.compile(
    r"global (name ')(.*?)(' is not defined)"
)
non_ascii_error_rt           = re.compile(
    r"(SyntaxError: Non-ASCII character.*? on line) \d+"
)
python_win_lib_re            = re.compile(
    r"[a-zA-Z]:\\\\?[Pp]ython(.*?\\\\?)[Ll]ib"
)
local_port_re = re.compile(
    r"(127\.0\.0\.1):\d{2,5}"
)


traceback_re                 = re.compile(
    r'(F|f)ile "(.*?)", line (\d+)'
)

tempfile_re                  = re.compile(
    r'/tmp/tmp[a-z0-9_]*'
)

def traceback_re_callback(match):
    return r'%sile "%s", line %s' % (
        match.group(1),
        os.path.realpath(os.path.abspath(match.group(2))),
        match.group(3)
    )


# Make sure we flush after every print, the "-u" option does more than that
# and this is easy enough.
def my_print(*args, **kwargs):
    print(*args, **kwargs)

    sys.stdout.flush()


def displayOutput(stdout, stderr):
    if type(stdout) is not str:
        stdout = stdout.decode("utf-8" if os.name != "nt" else "cp850")
        stderr = stderr.decode("utf-8" if os.name != "nt" else "cp850")

    my_print(stdout, end = ' ')
    if stderr:
        my_print(stderr)


def compareOutput(kind, out_cpython, out_nuitka, ignore_warnings, ignore_infos,
                  syntax_errors):
    fromdate = ""
    todate = ""

    diff = difflib.unified_diff(
        makeDiffable(out_cpython, ignore_warnings, ignore_infos, syntax_errors),
        makeDiffable(out_nuitka, ignore_warnings, ignore_infos, syntax_errors),
        "{program} ({detail})".format(
            program = os.environ["PYTHON"],
            detail  = kind
        ),
        "{program} ({detail})".format(
            program = "nuitka",
            detail  = kind
        ),
        fromdate,
        todate,
        n = 3
    )

    result = list(diff)

    if result:
        for line in result:
            my_print(line, end = '\n' if not line.startswith("---") else "")

        return 1
    else:
        return 0


def makeDiffable(output, ignore_warnings, ignore_infos, syntax_errors):
    # Of course many cases to deal with, pylint: disable=too-many-branches

    result = []

    # Fix import "readline" because output sometimes starts with "\x1b[?1034h"
    m = re.match(b'\\x1b\\[[^h]+h', output)
    if m:
        output = output[len(m.group()):]

    lines = output.split(b"\n")
    if syntax_errors:

        for line in lines:
            if line.startswith(b"SyntaxError:"):
                lines = [line]
                break

    for line in lines:
        if type(line) is not str:
            line = line.decode("utf-8" if os.name != "nt" else "cp850")

        if line.endswith('\r'):
            line = line[:-1]

        if line.startswith("REFCOUNTS"):
            first_value = line[line.find('[')+1:line.find(',')]
            last_value = line[line.rfind(' ')+1:line.rfind(']')]
            line = line.\
              replace(first_value, "xxxxx").\
              replace(last_value, "xxxxx")

        if line.startswith('[') and line.endswith("refs]"):
            continue

        if ignore_warnings and line.startswith("Nuitka:WARNING"):
            continue

        if ignore_infos and line.startswith("Nuitka:INFO"):
            continue

        if line.startswith("Nuitka:WARNING:Cannot recurse to import"):
            continue

        line = instance_re.sub(r"at 0xxxxxxxxx\1", line)
        line = thread_re.sub(r"Thread 0xXXXXXXXX", line)
        line = compiled_types_re.sub(r"\1", line)
        line = global_name_error_re.sub(r"\1\2\3", line)
        line = module_repr_re.sub(r"\1xxxxx\2", line)
        line = non_ascii_error_rt.sub(r"\1 xxxx", line)

        # Windows has a different "os.path", update according to it.
        line = line.replace("ntpath", "posixpath")

        # This URL is updated, and Nuitka outputs the new one, but we test
        # against versions that don't have that.
        line = line.replace(
            "http://www.python.org/peps/pep-0263.html",
            "http://python.org/dev/peps/pep-0263/",
        )

        line = ran_tests_re.sub(r"\1x.xxxs", line)

        line = traceback_re.sub(traceback_re_callback, line)

        line = tempfile_re.sub(r"/tmp/tmpxxxxxxx", line)

        # This is a bug potentially, occurs only for CPython when re-directed,
        # we are going to ignore the issue as Nuitka is fine.
        if line == """\
Exception RuntimeError: 'maximum recursion depth \
exceeded while calling a Python object' in \
<type 'exceptions.AttributeError'> ignored""":
            continue

        # This is also a bug potentially, but only visible under
        # CPython
        line = python_win_lib_re.sub(r"C:\\Python\1Lib", line)

        # Port numbers can be random, lets ignore them
        line = local_port_re.sub(r"\1:xxxxx", line)

        # This is a bug with clang potentially, can't find out why it says that.
        if line == "/usr/bin/ld: warning: .init_array section has zero size":
            continue

        # This is for NetBSD and OpenBSD, which seems to build "libpython" so
        # that it gives such warnings.
        if "() possibly used unsafely" in line or \
           "() is almost always misused" in line:
            continue

        # This is for CentOS5, where the linker says this, and it's hard to
        # disable
        if "skipping incompatible /usr/lib/libpython2.6.so" in line:
            continue

        # This is for self compiled Python with default options, gives this
        # harmless option for every time we link to "libpython".
        if "is dangerous, better use `mkstemp'" in line or \
           "In function `posix_tempnam'" in line or \
           "In function `posix_tmpnam'" in line:
            continue

        result.append(line)

    return result


def checkNoPermissionError(output):
    for candidate in (b"Permission denied:", b"PermissionError:"):
        if candidate in output:
            return False

    return True


def main():
    # Of course many cases to deal with, pylint: disable=too-many-branches,too-many-locals,too-many-statements
    from nuitka.utils.Execution import check_output

    filename = sys.argv[1]
    args     = sys.argv[2:]

    def hasArg(arg):
        if arg in args:
            args.remove(arg)
            return True
        else:
            return False

    # For output keep it
    arguments = list(args)

    silent_mode        = hasArg("silent")
    ignore_stderr      = hasArg("ignore_stderr")
    ignore_warnings    = hasArg("ignore_warnings")
    ignore_infos       = hasArg("ignore_infos")
    expect_success     = hasArg("expect_success")
    expect_failure     = hasArg("expect_failure")
    python_debug       = hasArg("python_debug")
    module_mode        = hasArg("module_mode")
    two_step_execution = hasArg("two_step_execution")
    binary_python_path = hasArg("binary_python_path")
    keep_python_path   = hasArg("keep_python_path")
    trace_command      = hasArg("trace_command")
    remove_output      = hasArg("remove_output")
    standalone_mode    = hasArg("standalone")
    no_site            = hasArg("no_site")
    recurse_none       = hasArg("recurse_none")
    recurse_all        = hasArg("recurse_all")
    timing             = hasArg("timing")
    coverage_mode      = hasArg("coverage")
    original_file      = hasArg("original_file")
    no_warnings        = not hasArg("warnings")
    full_compat        = not hasArg("improved")

    syntax_errors      = hasArg("syntax_errors")

    plugins_enabled = []

    for count, arg in reversed(tuple(enumerate(args))):
        if arg.startswith("plugin_enable:"):
            plugins_enabled.append(arg[len("plugin_enable:"):])
            del args[count]

    plugins_disabled = []

    for count, arg in reversed(tuple(enumerate(args))):
        if arg.startswith("plugin_disable:"):
            plugins_disabled.append(arg[len("plugin_disable:"):])
            del args[count]

    recurse_not = []

    for count, arg in reversed(tuple(enumerate(args))):
        if arg.startswith("recurse_not:"):
            recurse_not.append(arg[len("recurse_not:"):])
            del args[count]

    if args:
        sys.exit("Error, non understood mode(s) '%s'," % ','.join(args))

    # In coverage mode, we don't want to execute, and to do this only in one mode,
    # we enable two step execution, which splits running the binary from the actual
    # compilation:
    if coverage_mode:
        two_step_execution = True

    # The coverage mode doesn't work with debug mode.
    if coverage_mode:
        python_debug = False

    comparison_mode = not coverage_mode

    assert not standalone_mode or not module_mode
    assert not recurse_all or not recurse_none

    if "PYTHONHASHSEED" not in os.environ:
        os.environ["PYTHONHASHSEED"] = '0'

    os.environ["PYTHONWARNINGS"] = "ignore"

    if "PYTHON" not in os.environ:
        os.environ["PYTHON"] = sys.executable

    extra_options = os.environ.get("NUITKA_EXTRA_OPTIONS", "").split()

    if "--python-debug" in extra_options or "--python-dbg" in extra_options:
        python_debug = True

    if python_debug:
        if os.path.exists(os.path.join("/usr/bin/", os.environ["PYTHON"] + "-dbg")):
            os.environ["PYTHON"] += "-dbg"

        if os.name == "nt":
            if os.path.exists(os.environ["PYTHON"][:-4]+"_d.exe"):
                os.environ["PYTHON"] = os.environ["PYTHON"][:-4]+"_d.exe"

    if os.environ["PYTHON"].endswith("-dbg"):
        python_debug = True

    if os.environ["PYTHON"].lower().endswith("_d.exe"):
        python_debug = True


    if comparison_mode:
        my_print(
            """\
Comparing output of '{filename}' using '{python}' with flags {args} ...""".
            format(
                filename = filename,
                python   = os.environ["PYTHON"],
                args     = ", ".join(arguments)
            )
        )
    else:
        my_print(
            """\
Taking coverage of '{filename}' using '{python}' with flags {args} ...""".
            format(
                filename = filename,
                python   = os.environ["PYTHON"],
                args     = ", ".join(arguments)
            )
        )


    if comparison_mode and not silent_mode:
        my_print('*' * 80)
        my_print("CPython:")
        my_print('*' * 80)

    if two_step_execution:
        filename = os.path.abspath(filename)

    if module_mode:
        if no_warnings:
            cpython_cmd = [
                os.environ["PYTHON"],
                "-W", "ignore",
                "-c", "import sys; sys.path.append(%s); import %s" % (
                    repr(os.path.dirname(filename)),
                    os.path.basename(filename)
                )
            ]
        else:
            cpython_cmd = [
                os.environ["PYTHON"],
                "-c", "import sys; sys.path.append(%s); import %s" % (
                    repr(os.path.dirname(filename)),
                    os.path.basename(filename)
                )
            ]

    else:
        if no_warnings:
            cpython_cmd = [
                os.environ["PYTHON"],
                "-W", "ignore",
                filename
            ]
        else:
            cpython_cmd = [
                os.environ["PYTHON"],
                filename
            ]

    if no_site:
        cpython_cmd.insert(1, "-S")

    if "NUITKA" in os.environ:
        # Would need to extract which "python" this is going to use.
        assert not coverage_mode, "Not implemented for binaries."

        nuitka_call = [os.environ["NUITKA"]]
    else:
        if comparison_mode:
            nuitka_call = [
                os.environ["PYTHON"],
                "-m",
                "nuitka.__main__", # Note: Needed for Python2.6
            ]
        else:
            assert coverage_mode

            nuitka_call = [
                os.environ["PYTHON"],
                "-S",
                "-m",
                "coverage",
                "run",
                "--rcfile",
                os.devnull,
                "-a",
                "-m",
                "nuitka.__main__" # Note: Needed for Python2.6
            ]

    if python_debug:
        extra_options.append("--python-debug")

    if no_warnings:
        extra_options.append("--python-flag=no_warnings")

    if remove_output:
        extra_options.append("--remove-output")

    if original_file:
        extra_options.append("--file-reference-choice=original")

    if full_compat:
        extra_options.append("--full-compat")

    if coverage_mode:
        # Coverage modules hates Nuitka to re-execute, and so we must avoid
        # that.
        python_path = check_output(
            [
                os.environ["PYTHON"],
                "-c"
                "import sys, os; print(os.pathsep.join(sys.path))"
            ]
        )

        if sys.version_info >= (3,):
            python_path = python_path.decode("utf8")

        os.environ["PYTHONPATH"] = python_path.strip()

    if binary_python_path:
        addToPythonPath(os.path.dirname(os.path.abspath(filename)))

    if keep_python_path or binary_python_path:
        extra_options.append("--keep-pythonpath")

    if recurse_none:
        extra_options.append("--recurse-none")

    if recurse_all:
        extra_options.append("--recurse-all")

    if recurse_not:
        extra_options.extend("--recurse-not-to=" + v for v in recurse_not)

    if coverage_mode:
        extra_options.append("--must-not-re-execute")
        extra_options.append("--generate-c-only")

    for plugin_enabled in plugins_enabled:
        extra_options.append("--plugin-enable=" + plugin_enabled)

    for plugin_disabled in plugins_disabled:
        extra_options.append("--plugin-disable=" + plugin_disabled)

    # Now build the command to run Nuitka.
    if not two_step_execution:
        if module_mode:
            nuitka_cmd = nuitka_call + extra_options + \
              ["--execute", "--module", filename]
        elif standalone_mode:
            nuitka_cmd = nuitka_call + extra_options + \
              ["--execute", "--standalone", filename]
        else:
            nuitka_cmd = nuitka_call + extra_options + \
              ["--execute", filename]

        if no_site:
            nuitka_cmd.insert(len(nuitka_cmd) - 1, "--python-flag=-S")

    else:
        if module_mode:
            nuitka_cmd1 = nuitka_call + extra_options + \
              ["--module", os.path.abspath(filename)]
        elif standalone_mode:
            nuitka_cmd1 = nuitka_call + extra_options + \
              ["--standalone", filename]
        else:
            nuitka_cmd1 = nuitka_call + extra_options + \
              [filename]

        if no_site:
            nuitka_cmd1.insert(len(nuitka_cmd1) - 1, "--python-flag=-S")


    for extra_option in extra_options:
        dir_match = re.search(r"--output-dir=(.*?)(\s|$)", extra_option)

        if dir_match:
            output_dir = dir_match.group(1)
            break
    else:
        # The default.
        output_dir = '.'

    if module_mode:
        nuitka_cmd2 = [
            os.environ["PYTHON"],
            "-W", "ignore",
            "-c", "import %s" % os.path.basename(filename)
        ]
    else:
        exe_filename = os.path.basename(filename)

        if filename.endswith(".py"):
            exe_filename = exe_filename[:-3]

        exe_filename = exe_filename.replace(')', "").replace('(', "")
        exe_filename += ".exe"

        nuitka_cmd2 = [
            os.path.join(output_dir, exe_filename)
        ]

        pdb_filename = exe_filename[:-4] + ".pdb"

    if trace_command:
        my_print("CPython command:", *cpython_cmd)

    if comparison_mode:
        start_time = time.time()

        # Try a coupile of times for permission denied, on Windows it can
        # be transient.
        for _i in range(3):
            with withPythonPathChange(os.getcwd()):
                process = subprocess.Popen(
                    args   = cpython_cmd,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE
                )

            stdout_cpython, stderr_cpython = process.communicate()
            exit_cpython = process.returncode

            if checkNoPermissionError(stdout_cpython) and \
               checkNoPermissionError(stderr_cpython):
                break

            my_print("Retrying CPython due to permission problems after delay.")
            time.sleep(2)

        cpython_time = time.time() - start_time

    if comparison_mode and not silent_mode:
        displayOutput(stdout_cpython, stderr_cpython)

    if comparison_mode and not silent_mode:
        my_print('*' * 80)
        my_print("Nuitka:")
        my_print('*' * 80)

    if two_step_execution:
        if output_dir:
            os.chdir(output_dir)
        else:
            tmp_dir = tempfile.gettempdir()

            # Try to avoid RAM disk /tmp and use the disk one instead.
            if tmp_dir == "/tmp" and os.path.exists("/var/tmp"):
                tmp_dir = "/var/tmp"

            os.chdir(tmp_dir)

        if trace_command:
            my_print("Going to output directory", os.getcwd())

    start_time = time.time()

    if not two_step_execution:
        if trace_command:
            my_print("Nuitka command:", nuitka_cmd)

        # Try a couple of times for permission denied, on Windows it can
        # be transient.
        for _i in range(3):
            with withPythonPathChange(nuitka_package_dir):
                process = subprocess.Popen(
                    args   = nuitka_cmd,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE
                )

            stdout_nuitka, stderr_nuitka = process.communicate()
            exit_nuitka = process.returncode

            if checkNoPermissionError(stdout_nuitka) and \
               checkNoPermissionError(stderr_nuitka):
                break

            my_print("Retrying nuitka exe due to permission problems after delay.")
            time.sleep(2)

    else:
        if trace_command:
            my_print("Nuitka command 1:", nuitka_cmd1)

        with withPythonPathChange(nuitka_package_dir):
            process = subprocess.Popen(
                args   = nuitka_cmd1,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
            )

        stdout_nuitka1, stderr_nuitka1 = process.communicate()
        exit_nuitka1 = process.returncode

        if exit_nuitka1 != 0:
            if not expect_failure and \
               not comparison_mode and \
               not os.path.exists(".coverage"):
                sys.exit(
                    """\
Error, failed to take coverage with '%s'.

Stderr was:
%s
""" % (
    os.environ["PYTHON"],
    stderr_nuitka1
)
                )

            exit_nuitka = exit_nuitka1
            stdout_nuitka, stderr_nuitka = stdout_nuitka1, stderr_nuitka1
        else:
            # No execution second step for coverage mode.
            if comparison_mode:
                if trace_command:
                    my_print("Nuitka command 2:", nuitka_cmd2)

                process = subprocess.Popen(
                    args   = nuitka_cmd2,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE
                )

                stdout_nuitka2, stderr_nuitka2 = process.communicate()
                stdout_nuitka = stdout_nuitka1 + stdout_nuitka2
                stderr_nuitka = stderr_nuitka1 + stderr_nuitka2
                exit_nuitka = process.returncode
            else:
                exit_nuitka = exit_nuitka1
                stdout_nuitka, stderr_nuitka = stdout_nuitka1, stderr_nuitka1


    nuitka_time = time.time() - start_time

    if not silent_mode:
        displayOutput(stdout_nuitka, stderr_nuitka)

        if coverage_mode:
            assert not stdout_nuitka
            assert not stderr_nuitka

    if comparison_mode:
        exit_code_stdout = compareOutput(
            "stdout",
            stdout_cpython,
            stdout_nuitka,
            ignore_warnings,
            ignore_infos,
            syntax_errors
        )

        if ignore_stderr:
            exit_code_stderr = 0
        else:
            exit_code_stderr = compareOutput(
                "stderr",
                stderr_cpython,
                stderr_nuitka,
                ignore_warnings,
                ignore_infos,
                syntax_errors
            )

        exit_code_return = exit_cpython != exit_nuitka

        if exit_code_return:
            my_print(
                """\
Exit codes {exit_cpython:d} (CPython) != {exit_nuitka:d} (Nuitka)""".format(
                    exit_cpython = exit_cpython,
                    exit_nuitka  = exit_nuitka
                )
            )

        # In case of segfault, also output the call stack by entering debugger
        # without stdin forwarded.
        if exit_code_return and exit_nuitka == -11 and sys.platform != "nt" and not module_mode:
            nuitka_cmd.insert(len(nuitka_cmd) - 1, "--debugger")

            process = subprocess.Popen(
                args  = nuitka_cmd,
                stdin = subprocess.PIPE
            )

            process.communicate()

        exit_code = exit_code_stdout or exit_code_stderr or exit_code_return

        if exit_code:
            sys.exit("Error, outputs differed.")

        if expect_success and exit_cpython != 0:
            if silent_mode:
                displayOutput(stdout_cpython, stderr_cpython)

            sys.exit("Unexpected error exit from CPython.")

        if expect_failure and exit_cpython == 0:
            sys.exit("Unexpected success exit from CPython.")

    if remove_output:
        if not module_mode:
            if os.path.exists(nuitka_cmd2[0]):
                if os.name == "nt":
                    # It appears there is a tiny lock race that we randomly cause,
                    # likely because --run spawns a subprocess that might still
                    # be doing the cleanup work.
                    for _i in range(10):
                        try:
                            os.rename(nuitka_cmd2[0], nuitka_cmd2[0]+".away")
                        except OSError:
                            time.sleep(0.1)
                            continue

                    for _i in range(10):
                        try:
                            os.unlink(nuitka_cmd2[0]+".away")
                        except OSError:
                            time.sleep(2)
                            continue
                        else:
                            break

                    assert not os.path.exists(nuitka_cmd2[0]+".away")

                    if os.path.exists(pdb_filename):
                        os.unlink(pdb_filename)
                else:
                    os.unlink(nuitka_cmd2[0])
        else:
            if os.name == "nt":
                module_filename = os.path.basename(filename) + ".pyd"
            else:
                module_filename = os.path.basename(filename) + ".so"

            if os.path.exists(module_filename):
                os.unlink(module_filename)


    if comparison_mode and timing:
        my_print(
            "CPython took %.2fs vs %0.2fs Nuitka." % (
                cpython_time,
                nuitka_time
            )
        )

    if comparison_mode and not silent_mode:
        my_print("OK, same outputs.")


nuitka_package_dir = os.path.normpath(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "..",
        )
    )
)


if __name__ == "__main__":
    # Unchanged, running from checkout, use the parent directory, the nuitka
    # package ought be there.
    sys.path.insert(
        0,
        nuitka_package_dir
    )

    main()
