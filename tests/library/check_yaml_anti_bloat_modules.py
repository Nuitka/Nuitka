#!/usr/bin/env python
#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" This test runner compiles all Python files as a module.

This is a test to achieve some coverage, it will only find assertions of
within Nuitka or warnings from the C compiler. Code will not be run
normally.

"""

import os
import sys

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

from nuitka import Options
from nuitka.__past__ import iter_modules
from nuitka.importing.Importing import (
    addMainScriptDirectory,
    decideModuleSourceRef,
    locateModule,
)
from nuitka.tools.testing.Common import my_print, setup, test_logger
from nuitka.Tracing import plugins_logger
from nuitka.tree.SourceHandling import (
    getSourceCodeDiff,
    readSourceCodeFromFilenameWithInformation,
)
from nuitka.utils.ModuleNames import ModuleName

python_version = setup(suite="python_modules", needs_io_encoding=True)


addMainScriptDirectory("/doesnotexist")
Options.is_full_compat = False


def scanModule(name_space, module_iterator):
    # plenty details here, pylint: disable=too-many-branches,too-many-locals

    from nuitka.tree.TreeHelpers import parseSourceCodeToAst

    for module_desc in module_iterator:
        if name_space is None:
            module_name = ModuleName(module_desc.name)
        else:
            module_name = name_space.getChildNamed(module_desc.name)

        try:
            _module_name, module_filename, finding = locateModule(
                module_name=module_name, parent_package=None, level=0
            )
        except AssertionError:
            # TODO: Currently bytecode only modules are triggering an assertion.
            continue

        assert _module_name == module_name, module_desc

        # Only source code that is found.
        if module_filename is None:
            continue

        (
            _main_added,
            _is_package,
            _is_namespace,
            _source_ref,
            source_filename,
        ) = decideModuleSourceRef(
            filename=module_filename,
            module_name=module_name,
            is_main=False,
            is_fake=False,
            logger=test_logger,
        )

        try:
            (
                source_code,
                original_source_code,
                contributing_plugins,
            ) = readSourceCodeFromFilenameWithInformation(
                module_name=module_name, source_filename=source_filename
            )
        except SyntaxError:
            continue

        try:
            parseSourceCodeToAst(
                source_code=source_code,
                module_name=module_name,
                filename=source_filename,
                line_offset=0,
            )
        except (SyntaxError, IndentationError) as e:
            try:
                parseSourceCodeToAst(
                    source_code=original_source_code,
                    module_name=module_name,
                    filename=source_filename,
                    line_offset=0,
                )
            except (SyntaxError, IndentationError):
                # Also an exception without the plugins, that is OK
                pass
            else:
                source_diff = getSourceCodeDiff(original_source_code, source_code)

                for line in source_diff:
                    plugins_logger.warning(line)

                if len(contributing_plugins) == 1:
                    contributing_plugins[0].sysexit(
                        "Making changes to '%s' that cause SyntaxError '%s'"
                        % (module_name, e)
                    )
                else:
                    test_logger.sysexit(
                        "One of the plugins '%s' is making changes to '%s' that cause SyntaxError '%s'"
                        % (",".join(contributing_plugins), module_name, e)
                    )

        my_print(module_name, ":", finding, "OK")

        if module_desc.ispkg:
            scanModule(module_name, iter_modules([module_filename]))


def main():
    scanModule(None, iter_modules())


if __name__ == "__main__":
    main()
