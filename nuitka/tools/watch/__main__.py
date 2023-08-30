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
""" Nuitka watch main part.

This tool is used to monitor effect of PyPI changes on Nuitka and effect
of Nuitka changes on PyPI packages.
"""

import os
import sys
from optparse import OptionParser

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.PythonVersions import getTestExecutionPythonVersions
from nuitka.tools.testing.Common import extractNuitkaVersionFromFilePath
from nuitka.Tracing import OurLogger
from nuitka.TreeXML import fromFile
from nuitka.utils.Execution import check_call, executeProcess
from nuitka.utils.FileOperations import (
    changeTextFileContents,
    getFileContents,
    getFileList,
    listDir,
    makePath,
    relpath,
    withDirectoryChange,
)
from nuitka.utils.Hashing import getFileContentsHash
from nuitka.utils.InstalledPythons import findPythons
from nuitka.utils.Utils import isLinux, isMacOS, isWin32Windows
from nuitka.utils.Yaml import parseYaml

# TODO: Command line interface
nuitka_update_mode = "newer"

watch_logger = OurLogger("", base_style="blue")


def _compareNuitkaVersions(version_a, version_b):
    def _numberize(version):
        return tuple(int(d) for d in version.split("rc")[0].split("."))

    return _numberize(version_a) < _numberize(version_b)


def scanCases(path):
    candidate = os.path.join(path, "case.yml")

    if os.path.exists(candidate):
        yield candidate

    for case_dir_full, _case_name in listDir(path):
        if os.path.isdir(case_dir_full):
            for case in scanCases(case_dir_full):
                yield case


def selectPythons(python_version_req, anaconda):
    for _python_version_str, installed_python_for_version in installed_pythons.items():
        for installed_python in installed_python_for_version:
            if not anaconda and installed_python.isAnacondaPython():
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
    for value in os_values:
        if value not in ("Linux", "Win32", "macOS"):
            watch_logger.sysexit("Illegal value for OS: %s" % value)

    if isLinux() and "Linux" in os_values:
        return "Linux"
    if isWin32Windows() and "Win32" in os_values:
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
            pipenv_package_requirements.append('%s = "*"' % requirement)
        else:
            operator_index = min(
                requirement.find(char) for char in "=><" if char in requirement
            )

            pipenv_package_requirements.append(
                '%s = "%s"'
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


def _updatePipenvLockFile(
    installed_python, dry_run, pipenv_filename_full, no_pipenv_update
):
    if os.path.exists("Pipfile.lock"):
        if no_pipenv_update:
            watch_logger.info(
                "Keeping existing lock file with pipenv file '%s'."
                % pipenv_filename_full
            )

        elif not dry_run:
            watch_logger.info(
                "Working with pipenv file '%s' to update virtualenv, may take a while."
                % pipenv_filename_full
            )

            check_call(
                [
                    installed_python.getPythonExe(),
                    "-m",
                    "pipenv",
                    "update",
                    "--python",
                    installed_python.getPythonExe(),
                ]
            )
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


def _compileCase(case_data, case_dir, installed_python):
    check_call(
        [
            installed_python.getPythonExe(),
            "-m",
            "pipenv",
            "run",
            "python",
            nuitka_binary,
            os.path.join(case_dir, case_data["filename"]),
            "--report=compilation-report.xml",
            "--report-diffable",
            "--report-user-provided=pipenv_hash=%s"
            % getFileContentsHash("Pipfile.lock"),
        ]
    )

    if case_data["interactive"] == "no":
        binaries = getFileList(
            ".",
            ignore_filenames=("__constants.bin",),
            only_suffixes=(".exe" if os.name == "nt" else ".bin"),
        )

        if len(binaries) != 1:
            sys.exit("Error, failed to identify created binary.")

        stdout, stderr, exit_nuitka = executeProcess([binaries[0]])

        if exit_nuitka != 0:
            sys.exit(
                "Error, failed to execute %s with code %d." % (binaries[0], exit_nuitka)
            )

        with open("compiled-stdout.txt", "wb") as output:
            output.write(stdout)
        with open("compiled-stderr.txt", "wb") as output:
            output.write(stderr)


def _updateCase(
    case_dir, case_data, dry_run, no_pipenv_update, installed_python, result_path
):
    # Not good for dry run, but tough life.
    makePath(result_path)

    # Update the pipenv file in any case, ought to be stable but we follow
    # global changes this way.
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
        _updatePipenvLockFile(
            installed_python=installed_python,
            dry_run=dry_run,
            pipenv_filename_full=pipenv_filename_full,
            no_pipenv_update=no_pipenv_update,
        )

        # Check if compilation is required.
        if os.path.exists("compilation-report.xml"):
            old_report_root = fromFile("compilation-report.xml")

            existing_hash = getFileContentsHash("Pipfile.lock")
            old_report_root_hash = (
                old_report_root.find("user-data").find("pipenv_hash").text
            )

            old_nuitka_version = old_report_root.attrib["nuitka_version"]

            if nuitka_update_mode == "force":
                need_compile = True
            elif nuitka_update_mode == "newer":
                if _compareNuitkaVersions(old_nuitka_version, nuitka_version):
                    need_compile = True
                else:
                    if existing_hash != old_report_root_hash:
                        watch_logger.info(
                            "Recompilation with identical Nuitka for '%s' due to changed pipfile."
                            % pipenv_filename_full
                        )

                        need_compile = True
                    elif old_nuitka_version == nuitka_version:
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

        if need_compile:
            _compileCase(
                case_data=case_data,
                case_dir=case_dir,
                installed_python=installed_python,
            )


def updateCase(case_dir, case_data, dry_run, no_pipenv_update):
    case_name = case_data["case"]

    # Wrong OS maybe.
    os_name = selectOS(case_data["os"])
    if os_name is None:
        return

    nuitka_min_version = case_data.get("nuitka")

    # Too old Nuitka version maybe.
    if nuitka_min_version is not None and _compareNuitkaVersions(
        nuitka_version, nuitka_min_version
    ):
        return

    # For all relevant Pythons applicable to this case.
    for installed_python in selectPythons(
        anaconda=case_data["anaconda"] == "yes",
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
            installed_python=installed_python,
            result_path=result_path,
        )


def updateCases(case_dir, dry_run, no_pipenv_update):
    for case_data in parseYaml(getFileContents("case.yml", mode="rb")):
        updateCase(
            case_dir=case_dir,
            case_data=case_data,
            dry_run=dry_run,
            no_pipenv_update=no_pipenv_update,
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
        "--dry-run",
        action="store_false",
        dest="dry_run",
        default=False,
        help="""\
Do not change anything, just report what would be done. Default %default.""",
    )

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

    options, positional_args = parser.parse_args()

    assert len(positional_args) <= 1, positional_args

    if positional_args and os.path.isdir(positional_args[0]):
        base_dir = positional_args[0]
    else:
        base_dir = os.getcwd()

    for python_version in options.python_versions or reversed(
        getTestExecutionPythonVersions()
    ):
        installed_pythons[python_version] = findPythons(python_version)

    nuitka_binary = os.path.abspath(os.path.expanduser(options.nuitka_binary))
    assert os.path.exists(nuitka_binary)

    global nuitka_version  # singleton, pylint: disable=global-statement
    nuitka_version = extractNuitkaVersionFromFilePath(
        os.path.join(os.path.dirname(nuitka_binary), "..", "nuitka", "Version.py")
    )

    watch_logger.info("Working with Nuitka %s." % nuitka_version)

    base_dir = os.path.abspath(base_dir)

    with withDirectoryChange(base_dir):
        for case_filename in scanCases(base_dir):
            case_relpath = relpath(case_filename, start=base_dir)

            watch_logger.info(
                "Consider watch cases from Yaml file '%s'." % case_relpath
            )

            with withDirectoryChange(os.path.dirname(case_filename)):
                updateCases(
                    os.path.dirname(case_filename),
                    dry_run=options.dry_run,
                    no_pipenv_update=options.no_pipenv_update,
                )


if __name__ == "__main__":
    main()
