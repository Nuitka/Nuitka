#!/usr/bin/env python
#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

import hashlib
import os
import pickle
import re
import sys
import time

from nuitka.OptionParsing import getNuitkaProjectOptions
from nuitka.PythonVersions import python_version
from nuitka.tools.testing.Common import (
    addToPythonPath,
    executeAfterTimePassed,
    getDebugPython,
    getTempDir,
    getTestingCPythonOutputsCacheDir,
    killProcessGroup,
    test_logger,
    traceExecutedCommand,
    withPythonPathChange,
)
from nuitka.tools.testing.OutputComparison import compareOutput
from nuitka.Tracing import my_print
from nuitka.utils.Execution import (
    callProcess,
    check_output,
    createProcess,
    executeProcess,
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

    # These are localized it seems, spell-checker: ignore totest
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


def _getCPythonResults(cpython_cmd, send_kill):
    stop_watch = StopWatch()

    # Try a compile of times for permission denied, on Windows it can
    # be transient.
    for _i in range(5):
        stop_watch.start()

        with withPythonPathChange(os.getcwd()):
            process = createProcess(command=cpython_cmd, new_group=send_kill)

        if send_kill:
            # Doing it per loop iteration hopefully, pylint: disable=cell-var-from-loop
            executeAfterTimePassed(
                message="Scheduling process kill in %.02fs",
                timeout=2.0,
                func=lambda: killProcessGroup("Uncompiled Python program", process.pid),
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


def getCPythonResults(cpython_cmd, cpython_cached, force_update, send_kill):
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
            curdir = os.getcwdu()  # spell-checker: ignore getcwdu
        else:
            curdir = os.getcwd()

        command_hash.update(curdir.encode("utf8"))

        cache_filename = os.path.join(
            getTestingCPythonOutputsCacheDir(), command_hash.hexdigest()
        )

        if os.path.exists(cache_filename) and not force_update:
            try:
                with open(cache_filename, "rb") as cache_file:
                    (
                        cpython_time,
                        stdout_cpython,
                        stderr_cpython,
                        exit_cpython,
                    ) = pickle.load(cache_file)
            except (IOError, EOFError, ValueError):
                # Broken cache content.
                pass
            else:
                cached = True

    if not cached:
        cpython_time, stdout_cpython, stderr_cpython, exit_cpython = _getCPythonResults(
            cpython_cmd=cpython_cmd, send_kill=send_kill
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

    def hasArgValue(arg_option, default=None):
        for arg in args:
            if arg.startswith(arg_option + "="):
                args.remove(arg)
                return arg[len(arg_option) + 1 :]
        return default

    def hasArgValues(arg_option):
        result = []

        for arg in tuple(args):
            if arg.startswith(arg_option + "="):
                args.remove(arg)
                result.append(arg[len(arg_option) + 1 :])

        return result

    # For output keep it
    arguments = list(args)

    silent_mode = hasArg("silent")
    ignore_stderr = hasArg("ignore_stderr")
    ignore_warnings = hasArg("ignore_warnings")
    expect_success = hasArg("expect_success")
    expect_failure = hasArg("expect_failure")
    python_debug = hasArg("python_debug") or hasArg("--python-debug")
    module_mode = hasArg("--module")
    module_entry_point = hasArgValue("--module-entry-point")
    coverage_mode = hasArg("coverage")
    two_step_execution = hasArg("two_step_execution")
    binary_python_path = hasArg("binary_python_path")
    keep_python_path = hasArg("keep_python_path")
    trace_command = (
        hasArg("trace_command") or os.environ.get("NUITKA_TRACE_COMMANDS", "0") != "0"
    )
    remove_output = hasArg("remove_output")
    remove_binary = not hasArg("--keep-binary")
    standalone_mode = hasArg("--standalone")
    onefile_mode = hasArg("--onefile")
    no_site = hasArg("no_site") or coverage_mode
    report = hasArgValue("--report")
    nofollow_imports = hasArg("recurse_none") or hasArg("--nofollow-imports")
    follow_imports = hasArg("recurse_all") or hasArg("--follow-imports")
    timing = hasArg("timing")
    original_file = hasArg("original_file") or hasArg(
        "--file-reference-choice=original"
    )
    runtime_file = hasArg("runtime_file") or hasArg("--file-reference-choice=runtime")
    no_warnings = not hasArg("warnings")
    full_compat = not hasArg("improved")
    cpython_cached = hasArg("cpython_cache")
    syntax_errors = hasArg("syntax_errors")
    no_prefer_source = hasArg("--no-prefer-source")
    no_verbose_log = hasArg("no_verbose_log")
    no_inclusion_log = hasArg("no_inclusion_log")
    send_kill = hasArg("--send-ctrl-c")
    output_dir = hasArgValue("--output-dir", None)
    include_packages = hasArgValues("--include-package")
    include_modules = hasArgValues("--include-module")
    python_flag_m = hasArg("--python-flag=-m")

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

    nowarn_mnemonics = []

    for count, arg in reversed(tuple(enumerate(args))):
        if arg.startswith("--nowarn-mnemonic="):
            nowarn_mnemonics.append(arg[len("--nowarn-mnemonic=") :])
            del args[count]

    if args:
        sys.exit("Error, non understood mode(s) '%s'," % ",".join(args))

    project_options = tuple(
        getNuitkaProjectOptions(
            logger=test_logger, filename_arg=filename, module_mode=module_mode
        )
    )

    if "--standalone" in project_options:
        standalone_mode = True
    if "--onefile" in project_options:
        standalone_mode = True
        onefile_mode = True

    # In coverage mode, we don't want to execute, and to do this only in one mode,
    # we enable two step execution, which splits running the binary from the actual
    # compilation:
    if coverage_mode:
        two_step_execution = True

    # The coverage mode doesn't work with debug mode.
    if coverage_mode:
        python_debug = False

    comparison_mode = not coverage_mode

    # We need to split it, so we know when to kill.
    if send_kill:
        two_step_execution = True

    assert not standalone_mode or not module_mode
    assert not follow_imports or not nofollow_imports

    if "PYTHONHASHSEED" not in os.environ:
        os.environ["PYTHONHASHSEED"] = "0"

    os.environ["PYTHONWARNINGS"] = "ignore"

    if "PYTHON" not in os.environ:
        os.environ["PYTHON"] = sys.executable

    extra_options = os.environ.get("NUITKA_EXTRA_OPTIONS", "").split()

    if os.path.normcase(os.environ["PYTHON"]).endswith(("-dbg", "-debug", "_d.exe")):
        python_debug = True
    elif "--python-debug" in extra_options or "--python-dbg" in extra_options:
        python_debug = True

    if python_debug:
        os.environ["PYTHON"] = getDebugPython() or os.environ["PYTHON"]

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
        module_name = os.path.basename(filename)

        if module_name.endswith(".py"):
            module_name = module_name[:-3]

        mini_script = "import %s" % module_name
        if module_entry_point:
            mini_script += "; %s.%s()" % (module_name, module_entry_point)

        cpython_cmd = [
            os.environ["PYTHON"],
            "-c",
            "import sys; sys.path.append(%s); %s"
            % (repr(os.path.dirname(filename)), mini_script),
        ]

        if no_warnings:
            cpython_cmd[1:1] = [
                "-W",
                "ignore",
            ]
    else:
        cpython_cmd = [os.environ["PYTHON"]]

        if no_warnings:
            cpython_cmd[1:1] = [
                "-W",
                "ignore",
            ]

        if python_flag_m:
            cpython_cmd += ["-m", os.path.basename(filename)]
            os.chdir(os.path.dirname(filename))
        else:
            cpython_cmd.append(filename)

    if no_site:
        cpython_cmd.insert(1, "-S")

    if "NUITKA" in os.environ:
        # Would need to extract which "python" this is going to use.
        assert not coverage_mode, "Not implemented for binaries."

        nuitka_call = [os.environ["PYTHON"], os.environ["NUITKA"]]
    else:
        if comparison_mode:
            nuitka_call = [
                os.environ["PYTHON"],
                "-m",
                "nuitka.__main__",  # Note: Needed for Python2.6
            ]
        else:
            assert coverage_mode

            # spell-checker: ignore rcfile

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

    if no_prefer_source:
        extra_options.append("--no-prefer-source")

    if python_flag_m:
        extra_options.append("--python-flag=-m")

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

    if (keep_python_path or binary_python_path) and not coverage_mode:
        extra_options.append("--execute-with-pythonpath")

    if report:
        extra_options.append("--report=%s" % report)

    if nofollow_imports or (not follow_imports and not standalone_mode):
        extra_options.append("--nofollow-imports")

    if follow_imports:
        extra_options.append("--follow-imports")

    if nowarn_mnemonics:
        extra_options.extend("--nowarn-mnemonic=" + v for v in nowarn_mnemonics)

    if coverage_mode:
        extra_options.append("--must-not-re-execute")
        extra_options.append("--generate-c-only")

    for plugin_enabled in plugins_enabled:
        extra_options.append("--enable-plugin=" + plugin_enabled)

    for plugin_disabled in plugins_disabled:
        extra_options.append("--disable-plugin=" + plugin_disabled)

    for user_plugin in user_plugins:
        extra_options.append("--user-plugin=" + user_plugin)

    if not no_verbose_log:
        extra_options.append("--verbose-output=%s.optimization.log" % filename)

    if not no_inclusion_log:
        extra_options.append("--show-modules-output=%s.inclusion.log" % filename)

    if output_dir is not None:
        extra_options.append("--output-dir=%s" % output_dir)
    else:
        # TODO: The run-tests uses NUITKA_EXTRA_OPTIONS still.
        for extra_option in extra_options:
            dir_match = re.search(r"--output-dir=(.*?)(\s|$)", extra_option)

            if dir_match:
                output_dir = dir_match.group(1)
                break
        else:
            # The default.
            output_dir = "."

    for include_package in include_packages:
        extra_options.append("--include-package=%s" % include_package)

    for include_module in include_modules:
        extra_options.append("--include-module=%s" % include_module)

    # Progress bar is not used.
    extra_options.append("--no-progressbar")

    # Now build the command to run Nuitka.
    if not two_step_execution:
        if module_mode:
            extra_options.append("--module")
        elif onefile_mode:
            extra_options.append("--onefile")
        elif standalone_mode:
            extra_options.append("--standalone")

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

    if module_mode:
        module_name = os.path.basename(filename)

        if module_name.endswith(".py"):
            module_name = module_name[:-3]

        nuitka_cmd2 = [os.environ["PYTHON"], "-W", "ignore", "-c", mini_script]
    else:
        exe_filename = os.path.basename(filename)

        if filename.endswith(".py"):
            exe_filename = exe_filename[:-3]

        exe_filename = exe_filename.replace(")", "").replace("(", "")

        if os.name == "nt":
            exe_filename += ".exe"
        else:
            exe_filename += ".bin"

        nuitka_cmd2 = [os.path.join(output_dir, exe_filename)]

        pdb_filename = exe_filename[:-4] + ".pdb"

    if trace_command:
        traceExecutedCommand("CPython command", cpython_cmd)

    if comparison_mode:
        cpython_time, stdout_cpython, stderr_cpython, exit_cpython = getCPythonResults(
            cpython_cmd=cpython_cmd,
            cpython_cached=cpython_cached,
            force_update=False,
            send_kill=send_kill,
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
            tmp_dir = getTempDir()
            os.chdir(tmp_dir)

        if trace_command:
            my_print("Going to output directory", os.getcwd())

    stop_watch = StopWatch()
    stop_watch.start()

    if not two_step_execution:
        if trace_command:
            traceExecutedCommand("Nuitka command", nuitka_cmd)

        # Try a couple of times for permission denied, on Windows it can
        # be transient.
        for _i in range(5):
            with withPythonPathChange(nuitka_package_dir):
                process = createProcess(command=nuitka_cmd)

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
                stdout_nuitka1, stderr_nuitka1, exit_nuitka1 = executeProcess(
                    nuitka_cmd1
                )

                python_path_used = os.environ["PYTHONPATH"]

            if exit_nuitka1 != 0:
                if (
                    not expect_failure
                    and not comparison_mode
                    and not os.path.exists(".coverage")
                ):
                    sys.exit(
                        """\
Error, failed to take coverage with '%s' (PYTHONPATH was '%s').

Stderr was:
%s
"""
                        % (nuitka_cmd1, python_path_used, stderr_nuitka1)
                    )

                exit_nuitka = exit_nuitka1
                stdout_nuitka, stderr_nuitka = stdout_nuitka1, stderr_nuitka1
                stdout_nuitka2 = b"not run due to compilation error:\n" + stdout_nuitka1
                stderr_nuitka2 = stderr_nuitka1
            else:
                # No execution second step for coverage mode.
                if comparison_mode:
                    if os.path.exists(nuitka_cmd2[0][:-4] + ".cmd"):
                        nuitka_cmd2[0] = nuitka_cmd2[0][:-4] + ".cmd"

                    if trace_command:
                        my_print("Nuitka command 2:", nuitka_cmd2)

                    # Need full manual control
                    process = createProcess(command=nuitka_cmd2, new_group=send_kill)

                    if send_kill:
                        # Lambda is used immediately in same loop, pylint: disable=cell-var-from-loop
                        executeAfterTimePassed(
                            message="Scheduling process kill in %.02fs",
                            timeout=2.0,
                            func=lambda: killProcessGroup(
                                "Nuitka compiled program", process.pid
                            ),
                        )

                    stdout_nuitka2, stderr_nuitka2 = process.communicate()
                    stdout_nuitka = stdout_nuitka1 + stdout_nuitka2
                    stderr_nuitka = stderr_nuitka1 + stderr_nuitka2
                    exit_nuitka = process.returncode

                    # In case of segfault or assertion triggered, run in debugger.
                    if exit_nuitka in (-11, -6) and sys.platform != "nt":
                        nuitka_cmd2 = wrapCommandForDebuggerForSubprocess(*nuitka_cmd2)

                        callProcess(nuitka_cmd2, shell=False)
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
                "stdout",
                stdout_cpython,
                stdout_nuitka2 if two_step_execution else stdout_nuitka,
                ignore_warnings,
                syntax_errors,
            )

            if ignore_stderr:
                exit_code_stderr = 0
            else:
                exit_code_stderr = compareOutput(
                    "stderr",
                    stderr_cpython,
                    stderr_nuitka2 if two_step_execution else stderr_nuitka,
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

            if not int(os.environ.get("NUITKA_CPYTHON_NO_CACHE_UPDATE", "0")):
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
                        send_kill=send_kill,
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
                callProcess(nuitka_cmd, shell=False)

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
            if os.path.exists(nuitka_cmd2[0]) and remove_binary:
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

            if os.path.exists(module_filename) and remove_binary:
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
