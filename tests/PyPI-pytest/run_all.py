#!/usr/bin/env python
#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#

import os
import sys
import subprocess

from nuitka.tools.testing.OutputComparison import compareOutput
from nuitka.tools.testing.Virtualenv import withVirtualenv
from nuitka.utils.FileOperations import removeDirectory


# currently trying to start automating with urllib3, 
#   will extend to other PyPI packages in the future

packages = {
    "urllib3": {
        "url": "https://github.com/urllib3/urllib3.git",
        "requirements_file": "dev-requirements.txt",
        "uncompiled_whl": "urllib3-1.25.3-py2.py3-none-any.whl",
        "compiled_whl": "urllib3-1.25.3-cp37-cp37m-win32.whl",
    },

    "dateutil": {
        "url": "https://github.com/dateutil/dateutil.git",
        "requirements_file": "requirements-dev.txt",
        "uncompiled_whl": "python_dateutil-2.8.1.dev79+g29c80ec-py2.py3-none-any.whl",
        "compiled_whl": "python_dateutil-2.8.1.dev79+g29c80ec-cp37-cp37m-win32.whl",
    }
}

base_dir = os.getcwd()


for package_name, details in packages.items():
    try:
        with withVirtualenv("venv_%s" % package_name) as venv:
            # setup the virtualenv for pytest
            dist_dir = os.path.join(venv.getVirtualenvDir(), package_name, "dist")

            venv.runCommand(
                commands=[
                    "git clone %s" % details["url"],
                    "git clone https://github.com/nuitka/nuitka.git",
                    "cd nuitka",
                    "python setup.py develop",
                    "cd ../%s" % package_name,
                    "python -m pip install -r %s" % details["requirements_file"],
                    "python setup.py bdist_wheel",
                    "python -m pip uninstall -y %s" % package_name,
                    "python -m pip install %s" % os.path.join(dist_dir, details["uncompiled_whl"]),
                ]
            )

            # get uncompiled pytest results
            uncompiled_stdout, uncompiled_stderr = venv.runCommandWithOutput(
                popen_args=[
                    "cd %s" % package_name,
                    "python -m pytest --disable-warnings",
                ]
            )

            # now get compiled pytest results
            venv.runCommand(
                commands=[
                    "cd %s" % package_name,
                    "python setup.py bdist_nuitka",
                    "python -m pip uninstall -y %s" % package_name,
                    "python -m pip install %s" % os.path.join(dist_dir, details["compiled_whl"]),
                ]
            )

            compiled_stdout, compiled_stderr = venv.runCommandWithOutput(
                popen_args=[
                    "cd %s" % package_name,
                    "python -m pytest --disable-warnings",
                ]
            )

    except Exception as exceptObj:
        print("Package", package_name, "ran into an exception during execution, traceback: ")
        print(exceptObj)
        continue


    # print statements for debugging
    '''
    print("uncompiled_stdout:")
    print(uncompiled_stdout)
    print("\nuncompiled_stderr:")
    print(uncompiled_stderr)

    print("---------------------------------------------------------------------------------")

    print("compiled_stdout:")
    print(compiled_stdout)
    print("\ncompiled_stderr:")
    print(compiled_stderr)
    '''

    os.chdir(base_dir)

    # TODO: remove venv directories
    removeDirectory(os.path.join(base_dir, "venv_%s" % package_name), ignore_errors=False) # currently not working

    # compare outputs
    exit_code_stdout = compareOutput(
        "stdout",
        uncompiled_stdout,
        compiled_stdout,
        ignore_warnings=True,
        ignore_infos=True,
        syntax_errors=True,
    )

    exit_code_stderr = compareOutput(
        "stderr",
        uncompiled_stderr,
        compiled_stderr,
        ignore_warnings=True,
        ignore_infos=True,
        syntax_errors=True,
    )
    
    print("---------------------------------------------------------------------------------")
    print("exit_stdout:", exit_code_stdout, "exit_stderr:", exit_code_stderr)

    if exit_code_stdout or exit_code_stderr:
        print("Error, outputs differed.")
