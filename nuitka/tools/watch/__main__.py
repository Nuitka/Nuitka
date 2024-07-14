#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nuitka watch main part.

This tool is used to monitor effect of PyPI changes on Nuitka and effect
of Nuitka changes on PyPI packages.
"""

import os
import subprocess
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
    executeToolChecked,
    withEnvironmentVarOverridden,
)
from nuitka.utils.FileOperations import (
    changeTextFileContents,
    deleteFile,
    getFileContents,
    getFileList,
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

from .GitHub import createNuitkaWatchPR

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
    # return driven, pylint: disable=too-many-return-statements

    for value in os_values:
        if value not in ("Linux", "Win32", "macOS", "Win32-MSYS2", "Win32-Anaconda"):
            watch_logger.sysexit("Illegal value for OS: %s" % value)

    if isLinux() and "Linux" in os_values:
        return "Linux"
    if isWin32Windows():
        if isMSYS2MingwPython():
            if "Win32-MSYS2" in os_values:
                return "Win32-MSYS2"

            return None
        if isAnacondaPython():
            if "Win32-Anaconda" in os_values:
                return "Win32-Anaconda"

            return None
        if "Win32" in os_values:
            return "Win32"
    if isMacOS() and "macOS" in os_values:
        return "macOS"

    return None


def getPlatformRequirements(installed_python, case_data):
    requirements = list(case_data["requirements"])

    # Nuitka house keeping, these are from setup.py but we ignore onefile needs
    # as that is not currently covered in watches.
    # spell-checker: ignore orderedset,imageio
    needs_onefile = False

    if installed_python.getHexVersion() >= 0x370:
        requirements.append("ordered-set >= 4.1.0")
    if installed_python.getHexVersion() < 0x300:
        requirements.append("subprocess32")
    if needs_onefile and installed_python.getHexVersion() >= 0x370:
        requirements.append("zstandard >= 0.15")
    if (
        os.name != "nt"
        and sys.platform != "darwin"
        and installed_python.getHexVersion() < 0x370
    ):
        requirements.append("orderedset >= 2.0.3")
    if sys.platform == "darwin" and installed_python.getHexVersion() < 0x370:
        requirements.append("orderedset >= 2.0.3")

    # For icon conversion.
    if case_data.get("icons", "no") == "yes":
        requirements.append("imageio")

    return requirements


def _updatePipenvFile(installed_python, case_data, dry_run, result_path):
    pipenv_filename = os.path.join(result_path, "Pipfile")
    pipenv_package_requirements = []

    for requirement in getPlatformRequirements(
        installed_python=installed_python, case_data=case_data
    ):
        # Ignore spaces in requirements.
        requirement = requirement.replace(" ", "")

        if all(char not in requirement for char in "=><"):
            pipenv_package_requirements.append('"%s" = "*"' % requirement)
        else:
            operator_index = min(
                requirement.find(char) for char in "=><" if char in requirement
            )

            pipenv_package_requirements.append(
                '"%s" = "%s"'
                % (requirement[:operator_index], requirement[operator_index:])
            )

    # TODO: Other indexes, e.g. nvidia might be needed too
    changed_pipenv_file = changeTextFileContents(
        pipenv_filename,
        """\
[[source]]
name = "pypi"
url = "https://pypi.org/simple"
verify_ssl = true

[requires]
python_version = "%(python_version)s"

[packages]
%(pipenv_package_requirements)s
"""
        % {
            "pipenv_package_requirements": "\n".join(pipenv_package_requirements),
            "python_version": installed_python.getPythonVersion(),
        },
        compare_only=dry_run,
    )

    return changed_pipenv_file, pipenv_filename


def _updatePacmanFile(installed_python, case_data, dry_run, result_path):
    pipenv_filename = os.path.join(result_path, "Pacman.txt")
    pipenv_package_requirements = []

    for requirement in getPlatformRequirements(
        installed_python=installed_python, case_data=case_data
    ):
        # Ignore spaces in requirements.
        requirement = requirement.replace(" ", "")

    # TODO: Other indexes, e.g. nvidia might be needed too
    changed_pipenv_file = changeTextFileContents(
        pipenv_filename,
        """\
[python]
%(python_version)s
[packages]
%(pipenv_package_requirements)s
"""
        % {
            "pipenv_package_requirements": "\n".join(pipenv_package_requirements),
            "python_version": installed_python.getPythonVersion(),
        },
        compare_only=dry_run,
    )

    return changed_pipenv_file, pipenv_filename


def _execPipenvCommand(installed_python, command, retry=False):
    try:
        check_call(
            [
                installed_python.getPythonExe(),
                "-m",
                "pipenv",
                command,
                "--python",
                installed_python.getPythonExe(),
            ],
            logger=watch_logger,
        )
    except subprocess.CalledProcessError:
        if command in ("install", "update") and not retry:
            _execPipenvCommand(installed_python, "--rm")
            _execPipenvCommand(installed_python, command)

        else:
            raise


def _updatePipenvLockFile(
    installed_python, dry_run, pipenv_filename_full, no_pipenv_update
):
    if os.path.exists("Pipfile.lock"):
        if no_pipenv_update:
            watch_logger.info(
                "Keeping existing lock file with pipenv file '%s'."
                % pipenv_filename_full
            )

            _execPipenvCommand(installed_python, "install")

        elif not dry_run:
            watch_logger.info(
                "Working with pipenv file '%s' to update virtualenv, may take a while."
                % pipenv_filename_full
            )

            _execPipenvCommand(installed_python, "update")
    else:
        watch_logger.info(
            "Working with pipenv file '%s' to install virtualenv, may take a while."
            % pipenv_filename_full
        )

        check_call(
            [
                installed_python.getPythonExe(),
                "-m",
                "pipenv",
                "install",
                "--python",
                installed_python.getPythonExe(),
            ]
        )

    return "Pipfile.lock"


def _updatePacmanLockFile():
    pacman_lock_filename = "Pacman.lock"

    pacman_output = executeToolChecked(
        logger=watch_logger,
        command=["pacman", "-Q"],
        absence_message="needs pacman to query package status on MSYS2",
    )

    if str is not bytes:
        pacman_output = pacman_output.decode("utf8")

    changeTextFileContents(filename=pacman_lock_filename, contents=pacman_output)

    return pacman_lock_filename


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
    else:
        assert False

    if jobs is not None:
        extra_options.append("--jobs=%s" % jobs)

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
        + extra_options
    )

    if case_data["interactive"] == "no":
        binaries = getFileList(
            ".",
            ignore_filenames=("__constants.bin",),
            only_suffixes=(".exe" if os.name == "nt" else ".bin"),
        )

        if len(binaries) != 1:
            sys.exit("Error, failed to identify created binary.")

        with withEnvironmentVarOverridden("NUITKA_LAUNCH_TOKEN", "1"):
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


def _updateCase(
    case_dir,
    case_data,
    dry_run,
    no_pipenv_update,
    nuitka_update_mode,
    installed_python,
    result_path,
    jobs,
):
    # Many details and cases due to package method being handled here.
    # pylint: disable=too-many-branches,too-many-locals

    # Not good for dry run, but tough life.
    makePath(result_path)

    # Update the pipenv file in any case, ought to be stable but we follow
    # global changes this way.
    preferred_package_type = installed_python.getPreferredPackageType()
    if preferred_package_type == "pip":
        changed_pipenv_file, pipenv_filename = _updatePipenvFile(
            installed_python=installed_python,
            case_data=case_data,
            dry_run=dry_run,
            result_path=result_path,
        )

        pipenv_filename_full = os.path.join(case_dir, pipenv_filename)

        if dry_run and changed_pipenv_file:
            watch_logger.info("Would create pipenv file '%s'." % pipenv_filename_full)
            return

        with withDirectoryChange(result_path):
            # Update or create lockfile of pipenv.
            lock_filename = _updatePipenvLockFile(
                installed_python=installed_python,
                dry_run=dry_run,
                pipenv_filename_full=pipenv_filename_full,
                no_pipenv_update=no_pipenv_update,
            )
    elif preferred_package_type == "pacman":
        changed_pipenv_file, pipenv_filename = _updatePacmanFile(
            installed_python=installed_python,
            case_data=case_data,
            dry_run=dry_run,
            result_path=result_path,
        )

        with withDirectoryChange(result_path):
            # Update or create lockfile of pipenv.
            lock_filename = _updatePacmanLockFile()
    else:
        assert False, preferred_package_type

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
                            % pipenv_filename_full
                        )

                        need_compile = True
                    elif old_nuitka_version == nuitka_version:
                        if old_report_root.attrib["completion"] != "yes":
                            need_compile = True
                        else:
                            watch_logger.info(
                                "Skipping compilation with identical Nuitka for '%s'."
                                % pipenv_filename_full
                            )

                            need_compile = False
                    else:
                        watch_logger.info(
                            "Skipping compilation of old Nuitka %s result with Nuitka %s for '%s'."
                            % (
                                old_nuitka_version,
                                nuitka_version,
                                pipenv_filename_full,
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
    case_dir, case_data, dry_run, no_pipenv_update, nuitka_update_mode, jobs
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
            # TODO: Enable Anaconda support through options/detection.
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
        # TODO: Enable Anaconda support through options/detection.
        anaconda="Anaconda" in os_name,
        msys2_mingw64="MSYS2" in os_name,
        python_version_req=case_data.get("python_version_req"),
    ):
        watch_logger.info("Consider with Python %s." % installed_python)

        result_path = "result/%(case_name)s/%(python_version)s-%(os_name)s" % {
            "case_name": case_name,
            "os_name": os_name,
            "python_version": installed_python.getPythonVersion(),
        }

        _updateCase(
            case_dir=case_dir,
            case_data=case_data,
            dry_run=dry_run,
            no_pipenv_update=no_pipenv_update,
            nuitka_update_mode=nuitka_update_mode,
            installed_python=installed_python,
            result_path=result_path,
            jobs=jobs,
        )


def updateCases(case_dir, dry_run, no_pipenv_update, nuitka_update_mode, jobs):
    for case_data in parseYaml(getFileContents("case.yml", mode="rb")):
        updateCase(
            case_dir=case_dir,
            case_data=case_data,
            dry_run=dry_run,
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
        "--no-pipenv-update",
        action="store_true",
        dest="no_pipenv_update",
        default=False,
        help="""\
Do not update the pipenv environment. Best to see only effect of Nuitka update. Default %default.""",
    )

    parser.add_option(
        "--dry-run",
        action="store_false",
        dest="dry_run",
        default=False,
        help="""\
Do not change anything, just report what would be done. Not yet perfectly true. Default %default.""",
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
            python_version, module_name="pipenv"
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
                    dry_run=options.dry_run,
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
