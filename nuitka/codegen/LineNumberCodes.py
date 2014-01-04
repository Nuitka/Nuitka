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
""" Generate code that updates the source code line.

"""

# Stack of source code references, to push and pop from, for loops and branches
# to not rely on their last line number.
source_ref_stack = [ None ]

def resetLineNumber():
    source_ref_stack[-1] = None

def pushLineNumberBranch():
    source_ref_stack.append( source_ref_stack[-1] )

def popLineNumberBranch():
    del source_ref_stack[-1]

def mergeLineNumberBranches():
    source_ref_stack[-1] = None

def _getLineNumberCode(line_number):
    return "frame_guard.setLineNumber( %d )" % line_number

def getLineNumberCode(source_ref):
    if source_ref.shallSetCurrentLine():
        line_number = source_ref.getLineNumber()

        if line_number != source_ref_stack[-1]:
            source_ref_stack[-1] = line_number

            return _getLineNumberCode( line_number )
        else:
            return ""
    else:
        return ""
