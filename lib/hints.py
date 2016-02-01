#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from __future__ import print_function

original_import = __import__

_indentation = 0

def enableImportTracing():


    def _ourimport(name, globals = None, locals = None, fromlist = None,
                   level = -1):
        global _indentation
        try:
            _indentation += 1

            print(_indentation * " " + "name=%r level=%d" % (name, level))


            for entry in traceback.extract_stack()[:-1]:
                if entry[2] == "_ourimport":
                    print("__import__")
                else:
                    print("|".join(str(s) for s in entry))

            print(_indentation * " " + "*" * 40)

            result = original_import(name, globals, locals, fromlist, level)
            print(_indentation * " " + "RESULT:", result)
            return result
        finally:
            _indentation -= 1
    try:
        import __builtin__ as builtins
    except ImportError:
        import builtins

    import traceback
    builtins.__import__ = _ourimport
