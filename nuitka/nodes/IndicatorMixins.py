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
""" Module for node class mixins that indicate runtime determined facts about a node.

These come into play after finalization only. All of the these attributes (and we could
use properties instead) are determined once or from a default and then used like this.

"""


class MarkContainsTryExceptIndicator:
    """ Mixin for indication that a module, class or function contains a try/except.

    """

    def __init__(self):
        self.try_except_containing = False
        self.try_finally_containing = False
        self.raise_containing = False

    def markAsTryExceptContaining(self):
        self.try_except_containing = True

    def isTryExceptContaining(self):
        return self.try_except_containing

    def markAsTryFinallyContaining(self):
        self.try_finally_containing = True

    def isTryFinallyContaining(self):
        return self.try_finally_containing

    def markAsRaiseContaining(self):
        self.raise_containing = True

    def isRaiseContaining(self):
        return self.raise_containing


class MarkLocalsDictIndicator:
    def __init__(self):
        self.needs_locals_dict = False

    def hasLocalsDict(self):
        return self.needs_locals_dict

    def markAsLocalsDict(self):
        self.needs_locals_dict = True


class MarkGeneratorIndicator:
    """ Mixin for indication that a function/lambda is a generator.

    """

    def __init__(self):
        self.is_generator = False

    def markAsGenerator(self):
        self.is_generator = True

    def isGenerator(self):
        return self.is_generator


class MarkUnoptimizedFunctionIndicator:
    """ Mixin for indication that a function contains an exec or star import.

        These do not access global variables directly, but check a locals dictionary
        first, because they do.
    """

    def __init__(self):
        self.unoptimized_locals = False
        self.unqualified_exec = False
        self.exec_source_ref = None

    def markAsExecContaining(self):
        self.unoptimized_locals = True

    def markAsUnqualifiedExecContaining(self, source_ref):
        self.unqualified_exec = True

        # Let the first one win.
        if self.exec_source_ref is None:
            self.exec_source_ref = source_ref

    markAsStarImportContaining = markAsExecContaining

    def isUnoptimized(self):
        return self.unoptimized_locals

    def isUnqualifiedExec(self):
        return self.unoptimized_locals and self.unqualified_exec

    def getExecSourceRef(self):
        return self.exec_source_ref
