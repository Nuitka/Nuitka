#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Objects use to describe control flow escapes.

Typically returned by shape operations to indicate what can and can not
have happened.

"""


class ControlFlowDescriptionBase(object):
    pass


class ControlFlowDescriptionElementBasedEscape(ControlFlowDescriptionBase):
    @staticmethod
    def getExceptionExit():
        return BaseException

    @staticmethod
    def isValueEscaping():
        return True

    @staticmethod
    def isControlFlowEscape():
        return True


class ControlFlowDescriptionFullEscape(ControlFlowDescriptionBase):
    @staticmethod
    def getExceptionExit():
        return BaseException

    @staticmethod
    def isValueEscaping():
        return True

    @staticmethod
    def isControlFlowEscape():
        return True


class ControlFlowDescriptionNoEscape(ControlFlowDescriptionBase):
    @staticmethod
    def getExceptionExit():
        return None

    @staticmethod
    def isValueEscaping():
        return False

    @staticmethod
    def isControlFlowEscape():
        return False


class ControlFlowDescriptionComparisonUnorderable(ControlFlowDescriptionFullEscape):
    pass


class ControlFlowDescriptionAddUnsupported(ControlFlowDescriptionFullEscape):
    pass
