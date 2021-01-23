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
""" Included entry points for standalone mode.

This keeps track of entry points for standalone. These should be extension
modules, added by core code, the main binary, added by core code, and from
plugins in their getExtraDlls implementation, where they provide DLLs to be
added, and whose dependencies will also be included.
"""

import collections
import os
import shutil

from nuitka.OutputDirectories import getStandaloneDirectoryPath
from nuitka.utils.FileOperations import makePath
from nuitka.utils.Importing import getSharedLibrarySuffix
from nuitka.utils.ModuleNames import ModuleName

IncludedEntryPoint = collections.namedtuple(
    "IncludedEntryPoint", ("kind", "source_path", "dest_path", "package_name")
)


# Since inheritance is not a thing with namedtuple, have factory functions
def makeIncludedEntryPoint(
    kind,
    source_path,
    dest_path,
    package_name,
):
    if package_name is not None:
        package_name = ModuleName(package_name)

    return IncludedEntryPoint(kind, source_path, dest_path, package_name)


def makeExecutableEntryPoint(source_path, dest_path):
    return makeIncludedEntryPoint("executable", source_path, dest_path, None)


def makeDllEntryPoint(source_path, dest_path, package_name):
    # TODO: Get rid of makeDllEntryPointOld by doing this uniformly here.
    dest_path = os.path.join(getStandaloneDirectoryPath(), dest_path)

    return makeIncludedEntryPoint("dll", source_path, dest_path, package_name)


def makeDllEntryPointOld(source_path, dest_path, package_name):
    return makeIncludedEntryPoint("dll", source_path, dest_path, package_name)


def makeExtensionModuleEntryPoint(source_path, dest_path, package_name):
    return makeIncludedEntryPoint("shlib", source_path, dest_path, package_name)


standalone_entry_points = []


def addIncludedEntryPoints(arg):
    standalone_entry_points.extend(arg)


def setMainEntryPoint(binary_filename):
    entry_point = makeExecutableEntryPoint(
        source_path=binary_filename, dest_path=binary_filename
    )

    standalone_entry_points.insert(0, entry_point)


def addShlibEntryPoint(module):
    target_filename = os.path.join(
        getStandaloneDirectoryPath(), module.getFullName().asPath()
    )
    target_filename += getSharedLibrarySuffix(preferred=False)

    target_dir = os.path.dirname(target_filename)

    if not os.path.isdir(target_dir):
        makePath(target_dir)

    shutil.copyfile(module.getFilename(), target_filename)

    standalone_entry_points.append(
        makeExtensionModuleEntryPoint(
            source_path=module.getFilename(),
            dest_path=target_filename,
            package_name=module.getFullName().getPackageName(),
        )
    )


def getStandaloneEntryPoints():
    return standalone_entry_points
