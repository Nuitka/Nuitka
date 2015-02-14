#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Emission of source code.

Code generation is driven via "emit", which is to receive lines of code and
this is to collect them, providing the emit implementation. Sometimes nested
use of these will occur.

"""

class SourceCodeCollector:
    def __init__(self):
        self.codes = []

    def __call__(self, code):
        self.emit(code)

    def emit(self,code):
        for line in code.split('\n'):
            self.codes.append(line)
