#!/usr/bin/env python
#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Runner for DLL mode tests and C host examples of Nuitka.

Each test subdirectory provides a Python entry point compiled with '--mode=dll'
and a standalone C host program that loads the produced shared library using the
generated '.h' header without CPython headers or APIs.
"""

import os
import sys

_suite_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(
    0,
    os.path.normpath(os.path.join(_suite_dir, "..", "..")),
)

# isort:start

import nuitka
from nuitka.build.SconsInterface import getCommonSconsOptions, runScons
from nuitka.build.SconsSourceIndex import getSourceFilesIndexFilename
from nuitka.options import Options
from nuitka.plugins.Plugins import setupHooks
from nuitka.reports.CompilationReportReader import (
    getCompilationOutputBinary,
    getCompilationOutputMode,
    parseCompilationReport,
)
from nuitka.tools.testing.Common import (
    checkTestRequirements,
    createSearchMode,
    displayFolderContents,
    getTempDir,
    my_print,
    reportSkip,
    scanDirectoryForTestCaseFolders,
    setup,
    test_logger,
)
from nuitka.tools.testing.OutputComparison import compareOutput
from nuitka.utils.Execution import executeProcess, getExecutablePath
from nuitka.utils.FileOperations import (
    copyFile,
    deleteFile,
    getExternalUsePath,
    getFileContents,
    makePath,
    putTextFileContents,
    removeDirectory,
    withDirectoryChange,
)

_CASE_RUNTIME_SETTINGS = {
    "basic_dll": {
        "host_source": "BasicDllHost.c",
        "cpython_args": ["first-arg", "second arg"],
        "host_args": ["first-arg", "second arg"],
        "cpython_env": {},
        "expected_headers": ("BasicDllMain.h", "BasicDllMain.rs"),
        "unexpected_headers": (),
    },
    "host_thread": {
        "host_source": "HostThreadHost.c",
        "cpython_args": [],
        "host_args": [],
        "cpython_env": {
            "NUITKA_DLL_HOST_MOCK": "1",
        },
        "expected_headers": ("custom_host_dll.h",),
        "unexpected_headers": ("custom_host_dll.rs",),
    },
    "multiprocessing_dll": {
        "host_source": "MultiprocessingDllHost.c",
        "cpython_args": ["--worker-arg=ok"],
        "host_args": ["--host-config", "host_cfg_value", "--worker-arg=ok"],
        "cpython_env": {
            "NUITKA_DLL_PARENT_MOCK": "1",
        },
        "expected_headers": ("MultiprocessingDllMain.h",),
        "unexpected_headers": ("MultiprocessingDllMain.rs",),
    },
}


def _getExtraNuitkaOptions():
    extra_options = os.getenv("NUITKA_EXTRA_OPTIONS", "").split()

    return [
        option for option in extra_options if not option.startswith("--output-dir=")
    ]


def _buildHostExecutableHelper(host_source_path, host_exe_path, host_build_dir):
    makePath(host_build_dir)
    host_basename = os.path.basename(host_source_path)
    copyFile(
        source_path=host_source_path,
        dest_path=os.path.join(host_build_dir, host_basename),
    )
    putTextFileContents(
        filename=getSourceFilesIndexFilename(host_build_dir),
        contents=[host_basename],
        encoding="utf8",
    )

    compiler_flags = [
        option
        for option in _getExtraNuitkaOptions()
        if option in ("--zig", "--mingw64", "--clang", "--assume-yes-for-downloads")
        or option.startswith(("--jobs=", "--msvc="))
    ]

    nuitka.getLaunchingNuitkaProcessEnvironmentValue = os.getenv

    sys.argv = [sys.argv[0], "--no-progressbar"] + compiler_flags + [__file__]
    setupHooks()
    Options.parseArgs()

    scons_options, env_values = getCommonSconsOptions()
    scons_options["result_exe"] = host_exe_path
    scons_options["header_dir"] = os.path.dirname(host_exe_path)
    scons_options["dll_mode"] = "false"
    scons_options["exe_mode"] = "true"

    scons_script_path = os.path.join(_suite_dir, "BuildHost.scons")

    ok = runScons(
        scons_options=scons_options,
        env_values=env_values,
        scons_filename=scons_script_path,
        source_dir=host_build_dir,
        source_dir_external=getExternalUsePath(host_build_dir),
    )

    if not ok:
        sys.exit("Error, failed to compile DLL C host executable '%s'." % host_exe_path)


def _compileHostExecutable(host_source_path, host_exe_path, host_build_dir):
    command = [
        os.environ["PYTHON"],
        os.path.join(_suite_dir, "run_all.py"),
        "--build-host",
        os.path.abspath(host_source_path),
        os.path.abspath(host_exe_path),
        os.path.abspath(host_build_dir),
    ]

    result = executeProcess(command)
    if result.exit_code != 0:
        if result.stdout:
            my_print(result.stdout.decode("utf8", "replace"))
        if result.stderr:
            my_print(result.stderr.decode("utf8", "replace"))
        test_logger.sysexit(
            "Error, failed to build C host '%s' (exit code %d)."
            % (host_source_path, result.exit_code)
        )


def _compileDllTarget(dirname, filename_main, case_output_dir, report_filename):
    nuitka_script = os.path.abspath(os.path.join("..", "..", "bin", "nuitka"))
    main_path = os.path.join(dirname, filename_main)

    command = (
        [
            os.environ["PYTHON"],
            nuitka_script,
            "--no-progressbar",
            "--output-dir=%s" % case_output_dir,
            "--report=%s" % report_filename,
        ]
        + _getExtraNuitkaOptions()
        + [main_path]
    )

    result = executeProcess(command)
    if result.exit_code != 0:
        if result.stdout:
            my_print(result.stdout.decode("utf8", "replace"))
        if result.stderr:
            my_print(result.stderr.decode("utf8", "replace"))
        test_logger.sysexit(
            "Error, failed to compile '%s' in '--mode=dll' (exit code %d)."
            % (main_path, result.exit_code)
        )

    compilation_report = parseCompilationReport(report_filename)
    assert getCompilationOutputMode(compilation_report) == "dll", (
        getCompilationOutputMode(compilation_report),
    )

    dll_filename = getCompilationOutputBinary(
        compilation_report=compilation_report,
        prefixes=(
            ("~", os.path.expanduser("~")),
            ("${cwd}", os.getcwd()),
        ),
    )

    if not os.path.isfile(dll_filename):
        displayFolderContents("case output dir", case_output_dir)
        test_logger.sysexit(
            "Error, expected shared library '%s' does not exist." % dll_filename
        )

    return dll_filename


def _verifyGeneratedHeaders(case_output_dir, settings):
    for header_name in settings["expected_headers"]:
        header_path = os.path.join(case_output_dir, header_name)
        if not os.path.isfile(header_path):
            displayFolderContents("case output dir", case_output_dir)
            test_logger.sysexit(
                "Error, expected generated DLL binding '%s' does not exist."
                % header_path
            )

        contents = getFileContents(header_path, encoding="utf-8")
        if (
            "Other host binding languages available via '--dll-header-language':"
            not in contents
        ):
            test_logger.sysexit(
                "Error, generated DLL binding '%s' is missing the other-languages comment."
                % header_path
            )

        if header_name.endswith(".rs"):
            rustc_exe = getExecutablePath("rustc")
            if rustc_exe is not None:
                rlib_path = os.path.join(case_output_dir, "libcheck_binding.rlib")
                result = executeProcess(
                    [
                        rustc_exe,
                        "--crate-type=lib",
                        "--crate-name=check_binding",
                        "-D",
                        "warnings",
                        "-o",
                        rlib_path,
                        header_path,
                    ]
                )
                if result.exit_code != 0:
                    test_logger.sysexit(
                        "Error, generated Rust binding '%s' failed 'rustc' check: %s"
                        % (
                            header_path,
                            (result.stdout + result.stderr).decode("utf8", "replace"),
                        )
                    )

    for header_name in settings["unexpected_headers"]:
        header_path = os.path.join(case_output_dir, header_name)
        if os.path.exists(header_path):
            test_logger.sysexit(
                "Error, unexpected DLL binding '%s' was generated." % header_path
            )


def _checkOptionRejections():
    nuitka_script = os.path.abspath(os.path.join("..", "..", "bin", "nuitka"))
    main_path = os.path.join("basic_dll", "BasicDllMain.py")

    for extra_args, expected_substring in (
        (["--mode=dll", "--run"], "cannot use '--run' with '--mode=dll'"),
        (["--mode=dll", "--pgo-c"], "using PGO with 'dll' mode is not supported"),
        (
            ["--mode=dll", "--dll-header-language=invalid"],
            "unsupported '--dll-header-language' value 'invalid'",
        ),
        (
            ["--mode=dll", "--windows-create-installer"],
            "Windows installer creation requires standalone or onefile mode, not 'dll' mode",
        ),
        (
            ["--mode=dll", "--linux-create-installer"],
            "Linux installer creation requires standalone or onefile mode, not 'dll' mode",
        ),
    ):
        result = executeProcess(
            [os.environ["PYTHON"], nuitka_script] + extra_args + [main_path]
        )

        combined_output = (result.stdout + result.stderr).decode("utf8", "replace")
        if result.exit_code == 0 or expected_substring not in combined_output:
            test_logger.sysexit(
                "Error, '%s' was not rejected as expected (exit %d): %s"
                % (" ".join(extra_args), result.exit_code, combined_output)
            )


def _compareCaseResults(cpython_result, dll_result, search_mode):
    exit_code_stdout = compareOutput(
        kind="stdout",
        out_cpython=cpython_result.stdout,
        out_nuitka=dll_result.stdout,
        ignore_warnings=True,
        syntax_errors=False,
    )
    exit_code_stderr = compareOutput(
        kind="stderr",
        out_cpython=cpython_result.stderr,
        out_nuitka=dll_result.stderr,
        ignore_warnings=True,
        syntax_errors=False,
    )

    exit_code_return = cpython_result.exit_code != dll_result.exit_code
    if exit_code_return:
        my_print(
            "Exit codes %d (CPython) != %d (Nuitka DLL)"
            % (cpython_result.exit_code, dll_result.exit_code)
        )

    if exit_code_stdout or exit_code_stderr or exit_code_return:
        search_mode.onErrorDetected(1)


def _runExtraCaseChecks(case_name, case_output_dir, host_exe_path, host_env):
    if case_name == "basic_dll":
        exit_code_result = executeProcess(
            [host_exe_path, "--exit-code=37"],
            env=host_env,
        )
        if exit_code_result.exit_code != 37 or exit_code_result.stderr:
            test_logger.sysexit(
                "Error, 'sys.exit(37)' in DLL mode returned %d with stderr %r."
                % (exit_code_result.exit_code, exit_code_result.stderr)
            )

        exit_msg_result = executeProcess(
            [host_exe_path, "--exit-message=custom dll exit error"],
            env=host_env,
        )
        exit_msg_stderr = exit_msg_result.stderr.decode("utf8", "replace").strip()
        if exit_msg_result.exit_code != 1 or exit_msg_stderr != "custom dll exit error":
            test_logger.sysexit(
                "Error, 'sys.exit(message)' in DLL mode returned %d with stderr %r."
                % (exit_msg_result.exit_code, exit_msg_stderr)
            )

    if case_name == "host_thread":
        for temp_name in ("handshake.ping", "handshake.pong"):
            deleteFile(
                path=os.path.join(case_output_dir, temp_name),
                must_exist=False,
            )

        reentry_result = executeProcess(
            [host_exe_path, "--verify-reentry-rejected"],
            env=host_env,
        )
        reentry_stderr = reentry_result.stderr.decode("utf8", "replace")
        if (
            reentry_result.exit_code != 0
            or "Nuitka: Error, 'run_code' cannot be called more than once."
            not in reentry_stderr
        ):
            test_logger.sysexit(
                "Error, repeated 'run_code' call was not rejected as expected (exit %d): %r"
                % (reentry_result.exit_code, reentry_stderr)
            )


def _executeHostAndPython(dirname, main_path, case_output_dir, settings):
    cpython_env = os.environ.copy()
    cpython_env["PYTHONHASHSEED"] = "0"
    cpython_env["PYTHONIOENCODING"] = "utf-8"
    cpython_env.update(settings["cpython_env"])

    with withDirectoryChange(os.path.abspath(dirname)):
        cpython_result = executeProcess(
            [os.environ["PYTHON"], main_path] + settings["cpython_args"],
            env=cpython_env,
        )

    host_source_path = os.path.join(dirname, settings["host_source"])
    host_exe_name = os.path.splitext(settings["host_source"])[0] + (
        ".exe" if os.name == "nt" else ".bin"
    )
    host_exe_path = os.path.join(case_output_dir, host_exe_name)

    _compileHostExecutable(
        host_source_path=host_source_path,
        host_exe_path=host_exe_path,
        host_build_dir=os.path.join(case_output_dir, "host.build"),
    )

    host_env = os.environ.copy()
    host_env["PYTHONHASHSEED"] = "0"
    host_env["PYTHONIOENCODING"] = "utf-8"

    with withDirectoryChange(case_output_dir):
        dll_result = executeProcess(
            [host_exe_path] + settings["host_args"],
            env=host_env,
        )

        _runExtraCaseChecks(
            case_name=os.path.basename(dirname),
            case_output_dir=case_output_dir,
            host_exe_path=host_exe_path,
            host_env=host_env,
        )

    return cpython_result, dll_result


def _runTestCase(dirname, filename_main, search_mode):
    case_name = os.path.basename(dirname)
    settings = _CASE_RUNTIME_SETTINGS[case_name]

    main_path = os.path.abspath(os.path.join(dirname, filename_main))
    requirements_met, error_message = checkTestRequirements(main_path)
    if not requirements_met:
        reportSkip(error_message, dirname, filename_main)
        return

    test_logger.info(
        "Consider output of DLL mode compiled program: %s"
        % os.path.join(dirname, filename_main)
    )

    case_output_dir = os.path.join(getTempDir(), case_name)
    removeDirectory(
        path=case_output_dir,
        logger=test_logger,
        ignore_errors=True,
        extra_recommendation=None,
    )
    makePath(case_output_dir)

    try:
        _compileDllTarget(
            dirname=dirname,
            filename_main=filename_main,
            case_output_dir=case_output_dir,
            report_filename=os.path.join(case_output_dir, "compilation-report.xml"),
        )

        _verifyGeneratedHeaders(
            case_output_dir=case_output_dir,
            settings=settings,
        )

        cpython_result, dll_result = _executeHostAndPython(
            dirname=dirname,
            main_path=main_path,
            case_output_dir=case_output_dir,
            settings=settings,
        )

        _compareCaseResults(
            cpython_result=cpython_result,
            dll_result=dll_result,
            search_mode=search_mode,
        )
    finally:
        removeDirectory(
            path=case_output_dir,
            logger=test_logger,
            ignore_errors=True,
            extra_recommendation=None,
        )


def main():
    if len(sys.argv) == 5 and sys.argv[1] == "--build-host":
        _buildHostExecutableHelper(
            host_source_path=sys.argv[2],
            host_exe_path=sys.argv[3],
            host_build_dir=sys.argv[4],
        )
        return

    setup(suite="dll", needs_io_encoding=True)

    _checkOptionRejections()

    search_mode = createSearchMode()

    for dirname, filename_main in scanDirectoryForTestCaseFolders("."):
        active = search_mode.consider(dirname=dirname, filename=filename_main)

        if active:
            _runTestCase(
                dirname=dirname,
                filename_main=filename_main,
                search_mode=search_mode,
            )

    search_mode.finish()


if __name__ == "__main__":
    main()

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
