#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nuitka watch main part.

This tool is used to monitor effect of PyPI changes on Nuitka and effect
of Nuitka changes on PyPI packages.
"""

import os
import sys
from optparse import OptionParser

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.PythonFlavors import isAnacondaPython, isMSYS2MingwPython
from nuitka.PythonVersions import getTestExecutionPythonVersions
from nuitka.tools.testing.Common import extractNuitkaVersionFromFilePath
from nuitka.Tracing import OurLogger
from nuitka.TreeXML import fromFile
from nuitka.utils.Execution import (
    check_call,
    executeProcess,
    withEnvironmentVarsOverridden,
)
from nuitka.utils.FileOperations import (
    deleteFile,
    getFileContents,
    getFileList,
    getNormalizedPath,
    listDir,
    makePath,
    putTextFileContents,
    relpath,
    withDirectoryChange,
)
from nuitka.utils.Hashing import getFileContentsHash
from nuitka.utils.InstalledPythons import findPythons
from nuitka.utils.Utils import isLinux, isMacOS, isWin32Windows
from nuitka.utils.Yaml import parseYaml
from nuitka.Version import parseNuitkaVersionToTuple

from .Conda import (
    getCondaRunCommand,
    updateCondaEnvironmentFile,
    updateCondaEnvironmentLockFile,
)
from .GitHub import createNuitkaWatchPR
from .Pacman import updatePacmanFile, updatePacmanLockFile
from .Pipenv import (
    deletePipenvEnvironment,
    updatePipenvFile,
    updatePipenvLockFile,
)

watch_logger = OurLogger("", base_style="blue")


def _compareNuitkaVersions(version_a, version_b, consider_rc):
    if not consider_rc:
        version_a = version_a.split("rc")[0]
        version_b = version_b.split("rc")[0]

    return parseNuitkaVersionToTuple(version_a) < parseNuitkaVersionToTuple(version_b)


def scanCases(path):
    candidate = os.path.join(path, "case.yml")

    if os.path.exists(candidate):
        yield candidate

    for case_dir_full, _case_name in listDir(path):
        if os.path.isdir(case_dir_full):
            for case in scanCases(case_dir_full):
                yield case


def selectPythons(python_version_req, anaconda, msys2_mingw64):
    for _python_version_str, installed_python_for_version in installed_pythons.items():
        for installed_python in installed_python_for_version:
            if anaconda and not installed_python.isAnacondaPython():
                continue

            if msys2_mingw64 and not installed_python.isMSYS2MingwPython():
                continue

            if python_version_req is not None:
                # We trust the case yaml files, pylint: disable=eval-used
                if not eval(
                    python_version_req,
                    None,
                    {"python_version": installed_python.getHexVersion()},
                ):
                    continue

            yield installed_python
            break


def selectOS(os_values):
    # Need to move the Anaconda/MSYS2 handling into options of installed Pythons
    # return driven, pylint: disable=too-many-branches,too-many-return-statements

    for value in os_values:
        if value not in (
            "Linux",
            "Win32",
            "macOS",
            "Win32-MSYS2",
            "Win32-Anaconda",
            "Linux-Anaconda",
            "macOS-Anaconda",
        ):
            watch_logger.sysexit("Illegal value for OS: %s" % value)

    # TODO: Once installed python detects MSYS2 and Anaconda, we should remove
    # this in favor of passed options that allow flavors or not.
    if isLinux():
        if isAnacondaPython():
            if "Linux-Anaconda" in os_values:
                return "Linux-Anaconda"

            return None
        elif "Linux" in os_values:
            return "Linux"
    if isWin32Windows():
        if isMSYS2MingwPython():
            if "Win32-MSYS2" in os_values:
                return "Win32-MSYS2"

            return None
        elif isAnacondaPython():
            if "Win32-Anaconda" in os_values:
                return "Win32-Anaconda"
        elif "Win32" in os_values:
            return "Win32"
    if isMacOS():
        if isAnacondaPython():
            if "macOS-Anaconda" in os_values:
                return "macOS-Anaconda"
        elif "macOS" in os_values:
            return "macOS"

    return None


def _compileCase(case_data, case_dir, installed_python, lock_filename, jobs):
    preferred_package_type = installed_python.getPreferredPackageType()

    extra_options = []

    if preferred_package_type == "pip":
        run_command = [
            installed_python.getPythonExe(),
            "-m",
            "pipenv",
            "run",
            "--python",
            installed_python.getPythonExe(),
            "python",
        ]
    elif preferred_package_type == "pacman":
        run_command = ["python"]

        extra_options.append("--disable-ccache")
    elif preferred_package_type == "conda":
        run_command = getCondaRunCommand(
            installed_python=installed_python, case_data=case_data
        )
    else:
        assert False, preferred_package_type

    if jobs is not None:
        extra_options.append("--jobs=%s" % jobs)

    nuitka_extra_options = os.getenv("NUITKA_EXTRA_OPTIONS")

    if nuitka_extra_options:
        extra_options.extend(nuitka_extra_options.split())

    check_call(
        run_command
        + [
            nuitka_binary,
            os.path.join(case_dir, case_data["filename"]),
            "--assume-yes-for-downloads",
            "--report=compilation-report.xml",
            "--report-diffable",
            "--report-user-provided=pipenv_hash=%s"
            % getFileContentsHash(lock_filename),
        ]
        + extra_options,
        logger=watch_logger,
    )

    if case_data["interactive"] == "no":
        binaries = getFileList(
            ".",
            ignore_filenames=("__constants.bin",),
            only_suffixes=(".exe" if os.name == "nt" else ".bin"),
        )

        if len(binaries) != 1:
            sys.exit("Error, failed to identify created binary.")

        env = {
            "NUITKA_LAUNCH_TOKEN": "1",
            "NUITKA_TEST_INTERACTIVE": "0",
        }

        with withEnvironmentVarsOverridden(env):
            stdout, stderr, exit_nuitka = executeProcess([binaries[0]], timeout=5 * 60)

        with open("compiled-stdout.txt", "wb") as output:
            output.write(stdout)
        with open("compiled-stderr.txt", "wb") as output:
            output.write(stderr)

        if exit_nuitka == 0:
            deleteFile("compiled-exit.txt", must_exist=False)
        else:
            putTextFileContents(
                filename="compiled-exit.txt",
                contents=str(exit_nuitka),
            )

        if exit_nuitka != 0:
            sys.exit(
                "Error, failed to execute %s with code %d." % (binaries[0], exit_nuitka)
            )


def _updateCaseLock(
    installed_python,
    case_data,
    case_dir,
    reset_pipenv,
    no_pipenv_update,
    result_path,
):
    # Update the pipenv file in any case, ought to be stable but we follow
    # global changes this way.
    preferred_package_type = installed_python.getPreferredPackageType()

    # Not good for actual dry run, but tough life.
    makePath(result_path)

    with withDirectoryChange(result_path):
        if reset_pipenv:
            deletePipenvEnvironment(
                logger=watch_logger, installed_python=installed_python
            )

        if preferred_package_type == "pip":
            pipenv_filename = updatePipenvFile(
                installed_python=installed_python,
                case_data=case_data,
            )

            pipenv_filename_full = os.path.join(case_dir, pipenv_filename)

            # Update or create lockfile of pipenv.
            lock_filename = updatePipenvLockFile(
                logger=watch_logger,
                installed_python=installed_python,
                pipenv_filename_full=pipenv_filename_full,
                no_pipenv_update=no_pipenv_update,
            )
        elif preferred_package_type == "pacman":
            updatePacmanFile(
                installed_python=installed_python,
                case_data=case_data,
            )

            # Update or create lockfile of pipenv.
            lock_filename = updatePacmanLockFile(logger=watch_logger)
        elif preferred_package_type == "conda":
            updateCondaEnvironmentFile(
                installed_python=installed_python,
                case_data=case_data,
            )

            # Update or create lockfile of pipenv.
            lock_filename = updateCondaEnvironmentLockFile(
                logger=watch_logger,
                installed_python=installed_python,
                case_data=case_data,
            )

        lock_filename = os.path.abspath(lock_filename)

    return lock_filename


def _updateCase(
    case_dir,
    case_data,
    reset_pipenv,
    no_pipenv_update,
    nuitka_update_mode,
    installed_python,
    result_path,
    jobs,
):
    # Many details and cases due to package method being handled here.
    # pylint: disable=too-many-branches

    lock_filename = _updateCaseLock(
        installed_python=installed_python,
        case_data=case_data,
        case_dir=case_dir,
        reset_pipenv=reset_pipenv,
        no_pipenv_update=no_pipenv_update,
        result_path=result_path,
    )

    # Check if compilation is required.
    with withDirectoryChange(result_path):
        if os.path.exists("compilation-report.xml"):
            old_report_root = fromFile("compilation-report.xml")

            existing_hash = getFileContentsHash(lock_filename)
            old_report_root_hash = (
                old_report_root.find("user-data").find("pipenv_hash").text
            )

            old_nuitka_version = old_report_root.attrib["nuitka_version"]

            if nuitka_update_mode == "force":
                need_compile = True
            elif nuitka_update_mode == "newer":
                if _compareNuitkaVersions(
                    old_nuitka_version, nuitka_version, consider_rc=True
                ):
                    need_compile = True
                else:
                    if existing_hash != old_report_root_hash:
                        watch_logger.info(
                            "Recompilation with identical Nuitka for '%s' due to changed pipfile."
                            % lock_filename
                        )

                        need_compile = True
                    elif old_nuitka_version == nuitka_version:
                        if old_report_root.attrib["completion"] != "yes":
                            need_compile = True
                        else:
                            watch_logger.info(
                                "Skipping compilation with identical Nuitka for '%s'."
                                % lock_filename
                            )

                            need_compile = False
                    else:
                        watch_logger.info(
                            "Skipping compilation of old Nuitka %s result with Nuitka %s for '%s'."
                            % (
                                old_nuitka_version,
                                nuitka_version,
                                lock_filename,
                            )
                        )

                        need_compile = False
            else:
                need_compile = False
        else:
            need_compile = True

        if not need_compile:
            if os.path.exists("compiled-exit.txt"):
                watch_logger.info(
                    "Enforcing compilation of compiled program that failed to run."
                )
                need_compile = True

        if need_compile:
            _compileCase(
                case_data=case_data,
                case_dir=case_dir,
                installed_python=installed_python,
                lock_filename=lock_filename,
                jobs=jobs,
            )


def updateCase(
    case_dir, case_data, reset_pipenv, no_pipenv_update, nuitka_update_mode, jobs
):
    case_name = case_data["case"]

    watch_logger.info("Consider '%s' ... " % case_name)

    # Wrong OS maybe.
    os_name = selectOS(case_data["os"])
    if os_name is None:
        watch_logger.info("  ... not on this OS")
        return

    nuitka_min_version = case_data.get("nuitka")

    # Too old Nuitka version maybe.
    if nuitka_min_version is not None and _compareNuitkaVersions(
        nuitka_version, nuitka_min_version, consider_rc=False
    ):
        watch_logger.info("  ... not for this Nuitka version")
        return

    selected_pythons = tuple(
        selectPythons(
            anaconda="Anaconda" in os_name,
            msys2_mingw64="MSYS2" in os_name,
            python_version_req=case_data.get("python_version_req"),
        )
    )

    if not selected_pythons:
        watch_logger.info("  ... no suitable Python installations")
        return

    # For all relevant Pythons applicable to this case.
    for installed_python in selectPythons(
        anaconda="Anaconda" in os_name,
        msys2_mingw64="MSYS2" in os_name,
        python_version_req=case_data.get("python_version_req"),
    ):
        watch_logger.info("Consider with Python %s." % installed_python)

        result_path = getNormalizedPath(
            "result/%(case_name)s/%(python_version)s-%(os_name)s"
            % {
                "case_name": case_name,
                "os_name": os_name,
                "python_version": installed_python.getPythonVersion(),
            }
        )

        _updateCase(
            case_dir=case_dir,
            case_data=case_data,
            reset_pipenv=reset_pipenv,
            no_pipenv_update=no_pipenv_update,
            nuitka_update_mode=nuitka_update_mode,
            installed_python=installed_python,
            result_path=result_path,
            jobs=jobs,
        )


def updateCases(case_dir, reset_pipenv, no_pipenv_update, nuitka_update_mode, jobs):
    for case_data in parseYaml(getFileContents("case.yml", mode="rb")):
        updateCase(
            case_dir=case_dir,
            case_data=case_data,
            reset_pipenv=reset_pipenv,
            no_pipenv_update=no_pipenv_update,
            nuitka_update_mode=nuitka_update_mode,
            jobs=jobs,
        )


installed_pythons = OrderedDict()

nuitka_binary = None
nuitka_version = None


def main():
    global nuitka_binary  # shared for all run, pylint: disable=global-statement
    nuitka_binary = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "bin", "nuitka")
    )

    parser = OptionParser()

    parser.add_option(
        "--python-version",
        action="append",
        dest="python_versions",
        default=[],
        help="""\
Python versions to consider, by default all supported versions in descending order or in given order.""",
    )

    parser.add_option(
        "--nuitka-binary",
        action="store",
        dest="nuitka_binary",
        default=nuitka_binary,
        help="""\
Nuitka binary to compile with. Defaults to one near the nuitka-watch usage.""",
    )

    parser.add_option(
        "--reset-pipenv",
        action="store_true",
        dest="reset_pipenv",
        default=False,
        help="""\
Remove existing virtualenv and make sure to start from scratch.Default %default.""",
    )

    parser.add_option(
        "--no-pipenv-update",
        action="store_true",
        dest="no_pipenv_update",
        default=False,
        help="""\
Do not update the pipenv environment. Best to see only effect of Nuitka update. Default %default.""",
    )

    parser.add_option(
        "--nuitka-update-mode",
        action="store",
        choices=("newer", "force", "never"),
        dest="nuitka_update_mode",
        default="newer",
        help="""\
Recompile even if the versions seems not changed. Default %default.""",
    )

    parser.add_option(
        "--pr",
        action="store",
        dest="nuitka_pr_mode",
        default=None,
        help="""\
PR to create. Default not making a PR.""",
    )

    parser.add_option(
        "--jobs",
        action="store",
        dest="jobs",
        default=None,
        help="""\
Argument for jobs, in order to be nice use negative values
to reserve cores.""",
    )

    options, positional_args = parser.parse_args()

    assert len(positional_args) <= 1, positional_args

    if positional_args:
        base_dir = positional_args[0]

        if not os.path.isdir(base_dir):
            watch_logger.sysexit("Error, '%s' is not a directory" % base_dir)

    else:
        base_dir = os.getcwd()

    for python_version in options.python_versions or reversed(
        getTestExecutionPythonVersions()
    ):
        installed_pythons[python_version] = findPythons(
            python_version, module_name=None if isAnacondaPython() else "pipenv"
        )

    nuitka_binary = os.path.abspath(os.path.expanduser(options.nuitka_binary))
    assert os.path.exists(nuitka_binary)

    global nuitka_version  # singleton, pylint: disable=global-statement
    nuitka_version = extractNuitkaVersionFromFilePath(
        os.path.join(os.path.dirname(nuitka_binary), "..", "nuitka", "Version.py")
    )

    watch_logger.info("Working with Nuitka %s." % nuitka_version)

    base_dir = os.path.abspath(base_dir)

    if options.nuitka_pr_mode is not None:
        pr_category, pr_description = options.nuitka_pr_mode.split(",")
    else:
        pr_category = pr_description = None

    with withDirectoryChange(base_dir):
        for case_filename in scanCases(base_dir):
            case_relpath = relpath(case_filename, start=base_dir)

            watch_logger.info(
                "Consider watch cases from Yaml file '%s'." % case_relpath
            )

            with withDirectoryChange(os.path.dirname(case_filename)):
                updateCases(
                    case_dir=os.path.dirname(case_filename),
                    reset_pipenv=options.reset_pipenv,
                    no_pipenv_update=options.no_pipenv_update,
                    nuitka_update_mode=options.nuitka_update_mode,
                    jobs=options.jobs,
                )

        if pr_category is not None:
            createNuitkaWatchPR(category=pr_category, description=pr_description)


if __name__ == "__main__":
    main()

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
