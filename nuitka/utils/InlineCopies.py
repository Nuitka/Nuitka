#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Policies for locating inline copies."""

import os
import sys

from nuitka.PythonVersions import python_version
from nuitka.Tracing import general


def _getInlineCopyBaseFolder():
    """Base folder for inline copies."""
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "build", "inline_copy")
    )


def getInlineCopyFolder(module_name):
    """Get the inline copy folder for a given name."""
    folder_name = os.path.join(_getInlineCopyBaseFolder(), module_name)

    candidate_27 = folder_name + "_27"
    candidate_35 = folder_name + "_35"

    # Use specific versions if needed.
    if python_version < 0x300 and os.path.exists(candidate_27):
        folder_name = candidate_27
    elif python_version < 0x360 and os.path.exists(candidate_35):
        folder_name = candidate_35

    return folder_name


def getInlineCopyFolderIfExists(module_name):
    """Get the inline copy folder for a given name, or None if it does not exist."""
    folder_name = getInlineCopyFolder(module_name)

    if os.path.isdir(folder_name):
        return folder_name
    else:
        return None


def _importFromFolder(logger, module_name, path, must_exist, message):
    """Import a module from a folder by adding it temporarily to sys.path"""

    # Cyclic dependency here
    from .FileOperations import isFilenameBelowPath

    if module_name in sys.modules:
        # May already be loaded, but the wrong one from a ".pth" file of
        # clcache that we then don't want to use.
        if module_name != "clcache" or isFilenameBelowPath(
            path=path, filename=sys.modules[module_name].__file__
        ):
            return sys.modules[module_name]
        else:
            del sys.modules[module_name]

    # Temporarily add the inline path of the module to the import path.
    sys.path.insert(0, path)

    # Handle case without inline copy too.
    try:
        return __import__(module_name, level=0)
    except (ImportError, SyntaxError, RuntimeError) as e:
        if not must_exist:
            return None

        exit_message = (
            "Error, expected inline copy of '%s' to be in '%s', error was: %r."
            % (module_name, path, e)
        )

        if message is not None:
            exit_message += "\n" + message

        return logger.sysexit(exit_message)
    finally:
        # Do not forget to remove it from sys.path again.
        del sys.path[0]


_deleted_modules = {}


def importFromInlineCopy(module_name, must_exist, delete_module=False):
    """Import a module from the inline copy stage."""

    folder_name = getInlineCopyFolder(module_name)

    module = _importFromFolder(
        module_name=module_name,
        path=folder_name,
        must_exist=must_exist,
        message=None,
        logger=general,
    )

    if delete_module and module_name in sys.modules:
        delete_module_names = set([module_name])

        for m in sys.modules:
            if m.startswith(module_name + "."):
                delete_module_names.add(m)

        for delete_module_name in delete_module_names:
            _deleted_modules[delete_module_name] = sys.modules[delete_module_name]
            del sys.modules[delete_module_name]

    return module


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
