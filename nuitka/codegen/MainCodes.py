#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Main program code generation.

This is for the actual entry point code, which is mostly fed by a template,
but also customized through a lot of runtime configuration values.

Examples of these are sys.executable, and sys.flags, but of course also the
frame object data (filename, etc).
"""

from .ConstantCodes import getConstantCode
from .CodeObjectCodes import getCodeObjectHandle
from .Identifiers import NullIdentifier

from . import CodeTemplates

from nuitka import Options, Utils

import sys

def getMainCode(codes, context):
    python_flags = Options.getPythonFlags()

    if context.isEmptyModule():
        code_identifier = NullIdentifier()
    else:
        code_identifier = getCodeObjectHandle(
            context       = context,
            filename      = context.getFilename(),
            var_names     = (),
            arg_count     = 0,
            kw_only_count = 0,
            line_number   = 0,
            code_name     = "<module>",
            is_generator  = False,
            is_optimized  = False,
            has_starlist  = False,
            has_stardict  = False
        )

    main_code        = CodeTemplates.main_program % {
        "sys_executable"       : getConstantCode(
            constant = "python.exe"
                         if Utils.getOS() == "Windows" and \
                            Options.isStandaloneMode() else
                       sys.executable,
            context  = context
        ),
        "python_sysflag_debug" : sys.flags.debug,
        "python_sysflag_py3k_warning" : ( sys.flags.py3k_warning
            if hasattr( sys.flags, "py3k_warning" ) else 0 ),
        "python_sysflag_division_warning" : ( sys.flags.division_warning
            if hasattr( sys.flags, "division_warning" ) else 0 ),
        #"python_sysflag_division_new" : sys.flags.division_new, #not supported
        "python_sysflag_inspect" : sys.flags.inspect,
        "python_sysflag_interactive" : sys.flags.interactive,
        "python_sysflag_optimize" : sys.flags.optimize,
        "python_sysflag_dont_write_bytecode" : sys.flags.dont_write_bytecode,
        "python_sysflag_no_site" : sys.flags.no_site,
        "python_sysflag_no_user_site" : sys.flags.no_user_site,
        "python_sysflag_ignore_environment" : sys.flags.ignore_environment,
        "python_sysflag_tabcheck" : ( sys.flags.tabcheck
            if hasattr( sys.flags, "tabcheck" ) else 0 ),
        "python_sysflag_verbose" : 1 if "trace_imports" in python_flags else 0,
        "python_sysflag_unicode" : ( sys.flags.unicode
            if hasattr( sys.flags, "unicode" ) else 0 ),
        "python_sysflag_bytes_warning" : sys.flags.bytes_warning,
        "python_sysflag_hash_randomization" : ( sys.flags.hash_randomization
            if hasattr( sys.flags, "hash_randomization" )  and "no_randomization" not in python_flags else 0 ),
        "code_identifier"      : code_identifier.getCodeTemporaryRef()
    }

    return codes + main_code
