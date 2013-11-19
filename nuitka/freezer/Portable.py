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
""" Pack and copy files for portable mode.

This is in heavy flux now, cannot be expected to work or make sense.

"""

import sys, subprocess, marshal
from logging import debug

from nuitka import Utils

from nuitka.codegen.ConstantCodes import needsPickleInit

python_dll_dir_name = "_python"

def loadCodeObjectData( precompiled_path ):
    # Ignoring magic numbers, etc. which we don't have to care for much as
    # CPython already checked them (would have rejected it otherwise).
    return open( precompiled_path, "rb" ).read()[ 8 : ]


def detectEarlyImports():
    # When we are using pickle internally (for some hard constant cases we do),
    # we need to make sure it will be available as well.
    if needsPickleInit():
        command = "import %s;" % (
            "pickle" if Utils.python_version >= 300 else "cPickle"
        )
    else:
        command = ""

    if Utils.python_version >= 300:
        command += "import inspect;"

    if Utils.python_version >= 300:
        command += r'import sys; print( "\n".join( sorted( "import " + module.__name__ + " # sourcefile " + module.__file__ for module in sys.modules.values() if hasattr( module, "__file__" ) and module.__file__ != "<frozen>" ) ), file = sys.stderr )'

    process = subprocess.Popen(
        args   = [ sys.executable, "-s", "-S", "-v", "-c", command ],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    stdout, stderr = process.communicate()

    result = []

    debug( "Detecting early imports:" )

    for line in stderr.replace( b"\r", b"" ).split( b"\n" ):
        if line.startswith( b"import " ):
            # print( line )

            parts = line.split( b" # ", 2 )

            module_name = parts[0].split( b" ", 2 )[1]
            origin = parts[1].split()[0]

            if origin == b"precompiled":
                # This is a ".pyc" file that was imported, even before we have a
                # chance to do anything, we need to preserve it.
                filename = parts[1][ len( b"precompiled from " ): ]

                debug(
                    "Freezing module '%s' (from '%s').",
                    module_name,
                    filename
                )

                result.append(
                    (
                        module_name,
                        loadCodeObjectData( filename ),
                        b"__init__" in filename
                    )
                )

            elif origin == b"sourcefile":
                filename = parts[1][ len( b"sourcefile " ): ]

                debug(
                    "Freezing module '%s' (from '%s').",
                    module_name,
                    filename
                )

                result.append(
                    (
                        module_name,
                        marshal.dumps(
                            compile( open( filename ).read(), filename, "exec" )
                        ),
                        Utils.basename( filename ) == b"__init__.py"
                    )
                )


    debug( "Finished detecting early imports." )

    return result
