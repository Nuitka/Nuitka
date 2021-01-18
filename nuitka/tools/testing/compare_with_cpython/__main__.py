#!/usr/bin/env python
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

""" Tool to compare output of CPython and Nuitka.

"""

from __future__ import print_function

import hashlib
import os
import pickle
import re
import subprocess
import sys
import tempfile
import time

from nuitka.PythonVersions import python_version
from nuitka.tools.testing.Common import (
    addToPythonPath,
    getTestingCPythonOutputsCacheDir,
    withPythonPathChange,
)
from nuitka.tools.testing.OutputComparison import compareOutput
from nuitka.Tracing import my_print
from nuitka.utils.Execution import (
    check_output,
    wrapCommandForDebuggerForSubprocess,
)
from nuitka.utils.Importing import getSharedLibrarySuffix
from nuitka.utils.Timing import StopWatch


def displayOutput(stdout, stderr):
    if type(stdout) is not str:
        stdout = stdout.decode("utf-8" if os.name != "nt" else "cp850")
        stderr = stderr.decode("utf-8" if os.name != "nt" else "cp850")

    my_print(stdout, end=" ")
    if stderr:
        my_print(stderr)


def checkNoPermissionError(output):
    # Forms of permission errors.
    for candidate in (
        b"Permission denied:",
        b"PermissionError:",
        b"DBPermissionsError:",
    ):
        if candidate in output:
            return False

    # These are localized it seems.
    if re.search(
        b"(WindowsError|FileNotFoundError|FileExistsError|WinError 145):"
        b".*(@test|totest|xx|Error 145)",
        output,
    ):
        return False

    # Give those a retry as well.
    if b"clcache.__main__.CacheLockException" in output:
        return False

    return True


def _getCPythonResults(cpython_cmd):
    stop_watch = StopWatch()

    # Try a coupile of times for permission denied, on Windows it can
    # be transient.
    for _i in range(5):
        stop_watch.start()

        with withPythonPathChange(os.getcwd()):
            process = subprocess.Popen(
                args=cpython_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

        stdout_cpython, stderr_cpython = process.communicate()
        exit_cpython = process.returncode

        stop_watch.stop()

        if checkNoPermissionError(stdout_cpython) and checkNoPermissionError(
            stderr_cpython
        ):
            break

        my_print("Retrying CPython due to permission problems after delay.")
        time.sleep(2)

    cpython_time = stop_watch.getDelta()

    return cpython_time, stdout_cpython, stderr_cpython, exit_cpython


def getCPythonResults(cpython_cmd, cpython_cached, force_update):
    # Many details, pylint: disable=too-many-locals

    cached = False
    if cpython_cached:
        # TODO: Hashing stuff and creating cache filename is duplicate code
        # and should be shared.
        hash_input = " -- ".join(cpython_cmd)
        if str is not bytes:
            hash_input = hash_input.encode("utf8")

        command_hash = hashlib.md5(hash_input)

        for element in cpython_cmd:
            if os.path.exists(element):
                with open(element, "rb") as element_file:
                    command_hash.update(element_file.read())

        hash_salt = os.environ.get("NUITKA_HASH_SALT", "")

        if str is not bytes:
            hash_salt = hash_salt.encode("utf8")
        command_hash.update(hash_salt)

        if os.name == "nt" and python_version < 0x300:
            curdir = os.getcwdu()
        else:
            curdir = os.getcwd()

        command_hash.update(curdir.encode("utf8"))

        cache_filename = os.path.join(
            getTestingCPythonOutputsCacheDir(), command_hash.hexdigest()
        )

        if os.path.exists(cache_filename) and not force_update:
            with open(cache_filename, "rb") as cache_file:
                (
                    cpython_time,
                    stdout_cpython,
                    stderr_cpython,
                    exit_cpython,
                ) = pickle.load(cache_file)
                cached = True

    if not cached:
        cpython_time, stdout_cpython, stderr_cpython, exit_cpython = _getCPythonResults(
            cpython_cmd
        )

        if cpython_cached:
            with open(cache_filename, "wb") as cache_file:
                pickle.dump(
                    (cpython_time, stdout_cpython, stderr_cpython, exit_cpython),
                    cache_file,
                )

    return cpython_time, stdout_cpython, stderr_cpython, exit_cpython


def main():
    # Of course many cases to deal with, pylint: disable=too-many-branches,too-many-locals,too-many-statements

    filename = sys.argv[1]
    args = sys.argv[2:]

    def hasArg(arg):
        if arg in args:
            args.remove(arg)
            return True
        else:
            return False

    # For output keep it
    arguments = list(args)

    silent_mode = hasArg("silent")
    ignore_stderr = hasArg("ignore_stderr")
    ignore_warnings = hasArg("ignore_warnings")
    expect_success = hasArg("expect_success")
    expect_failure = hasArg("expect_failure")
    python_debug = hasArg("python_debug")
    module_mode = hasArg("module_mode")
    two_step_execution = hasArg("two_step_execution")
    binary_python_path = hasArg("binary_python_path")
    keep_python_path = hasArg("keep_python_path")
    trace_command = (
        hasArg("trace_command") or os.environ.get("NUITKA_TRACE_COMMANDS", "0") != "0"
    )
    remove_output = hasArg("remove_output")
    standalone_mode = hasArg("--standalone")
    onefile_mode = hasArg("--onefile")
    no_site = hasArg("no_site")
    recurse_none = hasArg("recurse_none")
    recurse_all = hasArg("recurse_all")
    timing = hasArg("timing")
    coverage_mode = hasArg("coverage")
    original_file = hasArg("original_file")
    runtime_file = hasArg("runtime_file")
    no_warnings = not hasArg("warnings")
    full_compat = not hasArg("improved")
    cpython_cached = hasArg("cpython_cache")
    syntax_errors = hasArg("syntax_errors")
    noprefer_source = hasArg("noprefer_source")
    noverbose_log = hasArg("noverbose_log")
    noinclusion_log = hasArg("noinclusion_log")

    plugins_enabled = []
    for count, arg in reversed(tuple(enumerate(args))):
        if arg.startswith("plugin_enable:"):
            plugins_enabled.append(arg[len("plugin_enable:") :])
            del args[count]

    plugins_disabled = []
    for count, arg in reversed(tuple(enumerate(args))):
        if arg.startswith("plugin_disable:"):
            plugins_disabled.append(arg[len("plugin_disable:") :])
            del args[count]

    user_plugins = []
    for count, arg in reversed(tuple(enumerate(args))):
        if arg.startswith("user_plugin:"):
            user_plugins.append(arg[len("user_plugin:") :])
            del args[count]

    recurse_not = []

    for count, arg in reversed(tuple(enumerate(args))):
        if arg.startswith("recurse_not:"):
            recurse_not.append(arg[len("recurse_not:") :])
            del args[count]

    recurse_to = []

    for count, arg in reversed(tuple(enumerate(args))):
        if arg.startswith("recurse_to:"):
            recurse_to.append(arg[len("recurse_to:") :])
            del args[count]

    if args:
        sys.exit("Error, non understood mode(s) '%s'," % ",".join(args))

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
        os.environ["PYTHONHASHSEED"] = "0"

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
            if os.path.exists(os.environ["PYTHON"][:-4] + "_d.exe"):
                os.environ["PYTHON"] = os.environ["PYTHON"][:-4] + "_d.exe"

    if os.environ["PYTHON"].endswith("-dbg"):
        python_debug = True

    if os.environ["PYTHON"].lower().endswith("_d.exe"):
        python_debug = True

    if comparison_mode:
        my_print(
            """\
Comparing output of '{filename}' using '{python}' with flags {args} ...""".format(
                filename=filename,
                python=os.environ["PYTHON"],
                args=", ".join(arguments),
            )
        )
    else:
        my_print(
            """\
Taking coverage of '{filename}' using '{python}' with flags {args} ...""".format(
                filename=filename,
                python=os.environ["PYTHON"],
                args=", ".join(arguments),
            )
        )

    if comparison_mode and not silent_mode:
        my_print("*" * 80)
        my_print("CPython:")
        my_print("*" * 80)

    if two_step_execution:
        filename = os.path.abspath(filename)

    if module_mode:
        if no_warnings:
            cpython_cmd = [
                os.environ["PYTHON"],
                "-W",
                "ignore",
                "-c",
                "import sys; sys.path.append(%s); import %s"
                % (repr(os.path.dirname(filename)), os.path.basename(filename)),
            ]
        else:
            cpython_cmd = [
                os.environ["PYTHON"],
                "-c",
                "import sys; sys.path.append(%s); import %s"
                % (repr(os.path.dirname(filename)), os.path.basename(filename)),
            ]

    else:
        if no_warnings:
            cpython_cmd = [os.environ["PYTHON"], "-W", "ignore", filename]
        else:
            cpython_cmd = [os.environ["PYTHON"], filename]

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
                "nuitka.__main__",  # Note: Needed for Python2.6
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
                "nuitka.__main__",  # Note: Needed for Python2.6
            ]

    if python_debug:
        extra_options.append("--python-debug")

    if no_warnings:
        extra_options.append("--python-flag=no_warnings")

    if remove_output:
        extra_options.append("--remove-output")

    if original_file:
        extra_options.append("--file-reference-choice=original")

    if runtime_file:
        extra_options.append("--file-reference-choice=runtime")

    if full_compat:
        extra_options.append("--full-compat")

    if noprefer_source:
        extra_options.append("--no-prefer-source")

    if coverage_mode:
        # Coverage modules hates Nuitka to re-execute, and so we must avoid
        # that.
        python_path = check_output(
            [
                os.environ["PYTHON"],
                "-c",
                "import sys, os; print(os.pathsep.join(sys.path))",
            ]
        )

        if sys.version_info >= (3,):
            python_path = python_path.decode("utf8")

        os.environ["PYTHONPATH"] = python_path.strip()

    if binary_python_path:
        addToPythonPath(os.path.dirname(os.path.abspath(filename)))

    if keep_python_path or binary_python_path:
        extra_options.append("--execute-with-pythonpath")

    if recurse_none:
        extra_options.append("--nofollow-imports")

    if recurse_all:
        extra_options.append("--follow-imports")

    if recurse_not:
        extra_options.extend("--nofollow-import-to=" + v for v in recurse_not)

    if coverage_mode:
        extra_options.append("--must-not-re-execute")
        extra_options.append("--generate-c-only")

    for plugin_enabled in plugins_enabled:
        extra_options.append("--plugin-enable=" + plugin_enabled)

    for plugin_disabled in plugins_disabled:
        extra_options.append("--plugin-disable=" + plugin_disabled)

    for user_plugin in user_plugins:
        extra_options.append("--user-plugin=" + user_plugin)

    if not noverbose_log:
        extra_options.append("--verbose-output=%s.optimization.log" % filename)

    if not noinclusion_log:
        extra_options.append("--show-modules-output=%s.inclusion.log" % filename)

    # Now build the command to run Nuitka.
    if not two_step_execution:
        if module_mode:
            nuitka_cmd = nuitka_call + extra_options + ["--run", "--module", filename]
        elif onefile_mode:
            nuitka_cmd = nuitka_call + extra_options + ["--run", "--onefile", filename]
        elif standalone_mode:
            nuitka_cmd = (
                nuitka_call + extra_options + ["--run", "--standalone", filename]
            )
        else:
            nuitka_cmd = nuitka_call + extra_options + ["--run", filename]

        if no_site:
            nuitka_cmd.insert(len(nuitka_cmd) - 1, "--python-flag=-S")

    else:
        if module_mode:
            nuitka_cmd1 = (
                nuitka_call + extra_options + ["--module", os.path.abspath(filename)]
            )
        elif standalone_mode:
            nuitka_cmd1 = nuitka_call + extra_options + ["--standalone", filename]
        else:
            nuitka_cmd1 = nuitka_call + extra_options + [filename]

        if no_site:
            nuitka_cmd1.insert(len(nuitka_cmd1) - 1, "--python-flag=-S")

    for extra_option in extra_options:
        dir_match = re.search(r"--output-dir=(.*?)(\s|$)", extra_option)

        if dir_match:
            output_dir = dir_match.group(1)
            break
    else:
        # The default.
        output_dir = "."

    if module_mode:
        nuitka_cmd2 = [
            os.environ["PYTHON"],
            "-W",
            "ignore",
            "-c",
            "import %s" % os.path.basename(filename),
        ]
    else:
        exe_filename = os.path.basename(filename)

        if filename.endswith(".py"):
            exe_filename = exe_filename[:-3]

        exe_filename = exe_filename.replace(")", "").replace("(", "")
        exe_filename += ".exe" if os.name == "nt" else ".bin"

        nuitka_cmd2 = [os.path.join(output_dir, exe_filename)]

        pdb_filename = exe_filename[:-4] + ".pdb"

    if trace_command:
        my_print("CPython command:", *cpython_cmd)

    if comparison_mode:
        cpython_time, stdout_cpython, stderr_cpython, exit_cpython = getCPythonResults(
            cpython_cmd=cpython_cmd, cpython_cached=cpython_cached, force_update=False
        )

        if not silent_mode:
            displayOutput(stdout_cpython, stderr_cpython)

    if comparison_mode and not silent_mode:
        my_print("*" * 80)
        my_print("Nuitka:")
        my_print("*" * 80)

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

    stop_watch = StopWatch()
    stop_watch.start()

    if not two_step_execution:
        if trace_command:
            my_print("Nuitka command:", nuitka_cmd)

        # Try a couple of times for permission denied, on Windows it can
        # be transient.
        for _i in range(5):
            with withPythonPathChange(nuitka_package_dir):
                process = subprocess.Popen(
                    args=nuitka_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )

            stdout_nuitka, stderr_nuitka = process.communicate()
            exit_nuitka = process.returncode

            if checkNoPermissionError(stdout_nuitka) and checkNoPermissionError(
                stderr_nuitka
            ):
                break

            my_print("Retrying nuitka exe due to permission problems after delay.")
            time.sleep(2)

    else:
        if trace_command:
            my_print("Nuitka command 1:", nuitka_cmd1)

        for _i in range(5):
            with withPythonPathChange(nuitka_package_dir):
                process = subprocess.Popen(
                    args=nuitka_cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )

            stdout_nuitka1, stderr_nuitka1 = process.communicate()
            exit_nuitka1 = process.returncode

            if exit_nuitka1 != 0:
                if (
                    not expect_failure
                    and not comparison_mode
                    and not os.path.exists(".coverage")
                ):
                    sys.exit(
                        """\
Error, failed to take coverage with '%s'.

Stderr was:
%s
"""
                        % (os.environ["PYTHON"], stderr_nuitka1)
                    )

                exit_nuitka = exit_nuitka1
                stdout_nuitka, stderr_nuitka = stdout_nuitka1, stderr_nuitka1
            else:
                # No execution second step for coverage mode.
                if comparison_mode:
                    if trace_command:
                        my_print("Nuitka command 2:", nuitka_cmd2)

                    process = subprocess.Popen(
                        args=nuitka_cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )

                    stdout_nuitka2, stderr_nuitka2 = process.communicate()
                    stdout_nuitka = stdout_nuitka1 + stdout_nuitka2
                    stderr_nuitka = stderr_nuitka1 + stderr_nuitka2
                    exit_nuitka = process.returncode

                    # In case of segfault or assertion triggered, run in debugger.
                    if exit_nuitka in (-11, -6) and sys.platform != "nt":
                        nuitka_cmd2 = wrapCommandForDebuggerForSubprocess(*nuitka_cmd2)

                        process = subprocess.Popen(
                            args=nuitka_cmd2, stdin=subprocess.PIPE
                        )
                        process.communicate()
                else:
                    exit_nuitka = exit_nuitka1
                    stdout_nuitka, stderr_nuitka = stdout_nuitka1, stderr_nuitka1

            if checkNoPermissionError(stdout_nuitka) and checkNoPermissionError(
                stderr_nuitka
            ):
                break

            my_print("Retrying nuitka exe due to permission problems after delay.")
            time.sleep(2)

    stop_watch.stop()
    nuitka_time = stop_watch.getDelta()

    if not silent_mode:
        displayOutput(stdout_nuitka, stderr_nuitka)

        if coverage_mode:
            assert not stdout_nuitka
            assert not stderr_nuitka

    if comparison_mode:

        def makeComparisons(trace_result):
            exit_code_stdout = compareOutput(
                "stdout", stdout_cpython, stdout_nuitka, ignore_warnings, syntax_errors
            )

            if ignore_stderr:
                exit_code_stderr = 0
            else:
                exit_code_stderr = compareOutput(
                    "stderr",
                    stderr_cpython,
                    stderr_nuitka,
                    ignore_warnings,
                    syntax_errors,
                )

            exit_code_return = exit_cpython != exit_nuitka

            if exit_code_return and trace_result:
                my_print(
                    """Exit codes {exit_cpython:d} (CPython) != {exit_nuitka:d} (Nuitka)""".format(
                        exit_cpython=exit_cpython, exit_nuitka=exit_nuitka
                    )
                )

            return exit_code_stdout, exit_code_stderr, exit_code_return

        if cpython_cached:
            exit_code_stdout, exit_code_stderr, exit_code_return = makeComparisons(
                trace_result=False
            )

            if exit_code_stdout or exit_code_stderr or exit_code_return:
                old_stdout_cpython = stdout_cpython
                old_stderr_cpython = stderr_cpython
                old_exit_cpython = exit_cpython

                my_print(
                    "Updating CPython cache by force due to non-matching comparison results.",
                    style="yellow",
                )

                (
                    cpython_time,
                    stdout_cpython,
                    stderr_cpython,
                    exit_cpython,
                ) = getCPythonResults(
                    cpython_cmd=cpython_cmd,
                    cpython_cached=cpython_cached,
                    force_update=True,
                )

                if not silent_mode:
                    if (
                        old_stdout_cpython != stdout_cpython
                        or old_stderr_cpython != stderr_cpython
                        or old_exit_cpython != exit_cpython
                    ):
                        displayOutput(stdout_cpython, stderr_cpython)

        exit_code_stdout, exit_code_stderr, exit_code_return = makeComparisons(
            trace_result=True
        )

        # In case of segfault, also output the call stack by entering debugger
        # without stdin forwarded.
        if (
            exit_code_return
            and exit_nuitka in (-11, -6)
            and sys.platform != "nt"
            and not module_mode
            and not two_step_execution
        ):
            nuitka_cmd.insert(len(nuitka_cmd) - 1, "--debugger")

            with withPythonPathChange(nuitka_package_dir):
                process = subprocess.Popen(args=nuitka_cmd, stdin=subprocess.PIPE)

            process.communicate()

        exit_code = exit_code_stdout or exit_code_stderr or exit_code_return

        if exit_code:
            problems = []
            if exit_code_stdout:
                problems.append("stdout")
            if exit_code_stderr:
                problems.append("stderr")
            if exit_code_return:
                problems.append("exit_code")

            sys.exit("Error, results differed (%s)." % ",".join(problems))

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
                    if os.path.exists(nuitka_cmd2[0] + ".away"):
                        os.unlink(nuitka_cmd2[0] + ".away")

                    for _i in range(10):
                        try:
                            os.rename(nuitka_cmd2[0], nuitka_cmd2[0] + ".away")
                        except OSError:
                            time.sleep(0.1)
                            continue

                    for _i in range(10):
                        try:
                            os.unlink(nuitka_cmd2[0] + ".away")
                        except OSError:
                            time.sleep(2)
                            continue
                        else:
                            break

                    if os.path.exists(pdb_filename):
                        os.unlink(pdb_filename)
                else:
                    os.unlink(nuitka_cmd2[0])
        else:
            module_filename = os.path.basename(filename) + getSharedLibrarySuffix(
                preferred=True
            )

            if os.path.exists(module_filename):
                os.unlink(module_filename)

    if comparison_mode and timing:
        my_print("CPython took %.2fs vs %0.2fs Nuitka." % (cpython_time, nuitka_time))

    if comparison_mode and not silent_mode:
        my_print("OK, same outputs.")


nuitka_package_dir = os.path.normpath(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
)


if __name__ == "__main__":
    # Unchanged, running from checkout, use the parent directory, the nuitka
    # package ought be there.
    sys.path.insert(0, nuitka_package_dir)

    main()
