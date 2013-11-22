#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Freezer for precompiled modules. Not compiled modules.

This is including modules as bytecode and mostly intended for modules, where
we know compiling it useless or does not make much sense, or for portable mode
to access modules during CPython library init that cannot be avoided.
"""

from nuitka import Utils

from nuitka.codegen.Indentation import indented

from nuitka.codegen import CodeTemplates, BlobCodes


frozen_modules = []

def addFrozenModule( frozen_module ):
    frozen_modules.append( frozen_module )

def getFrozenModuleCount():
    return len( frozen_modules )

stream_data = BlobCodes.StreamData()

def generatePrecompiledFrozenCode():
    frozen_defs = []

    for frozen_module in frozen_modules:
        module_name, code_data, is_package = frozen_module

        size = len( code_data )

        # Packages are indicated with negative size.
        if is_package:
            size = -size

        frozen_defs.append(
            """(char *)"%s", (unsigned char *)%s, %d,""" % (
                ( module_name if Utils.python_version < 300 else \
                  module_name.decode() ),
                stream_data.getStreamDataCode( code_data, fixed_size = True ),
                size
            )
        )

    return CodeTemplates.template_frozen_modules % {
        "stream_data"    : "".join( stream_data.encodeStreamData() ),
        "frozen_modules" : indented( frozen_defs )
    }
