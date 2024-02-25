#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Objects use to describe control flow escapes.

Typically returned by shape operations to indicate what can and can not
have happened.

"""


class ControlFlowDescriptionBase(object):
    @staticmethod
    def isUnsupported():
        return False


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


class ControlFlowDescriptionZeroDivisionNoEscape(ControlFlowDescriptionNoEscape):
    @staticmethod
    def getExceptionExit():
        return ZeroDivisionError


class ControlFlowDescriptionValueErrorNoEscape(ControlFlowDescriptionNoEscape):
    @staticmethod
    def getExceptionExit():
        return ValueError


class ControlFlowDescriptionComparisonUnorderable(ControlFlowDescriptionNoEscape):
    @staticmethod
    def getExceptionExit():
        return TypeError

    @staticmethod
    def isUnsupported():
        return True


class ControlFlowDescriptionFormatError(ControlFlowDescriptionFullEscape):
    pass


class ControlFlowDescriptionOperationUnsupportedBase(ControlFlowDescriptionNoEscape):
    @staticmethod
    def getExceptionExit():
        return TypeError

    @staticmethod
    def isUnsupported():
        return True


class ControlFlowDescriptionAddUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionSubUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionMulUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionFloorDivUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionTrueDivUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionOldDivUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionModUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionDivmodUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionPowUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionBitorUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionBitandUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionBitxorUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionLshiftUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionRshiftUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


class ControlFlowDescriptionMatmultUnsupported(
    ControlFlowDescriptionOperationUnsupportedBase
):
    pass


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
