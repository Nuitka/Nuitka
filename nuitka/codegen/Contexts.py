#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Code generation contexts.

"""

import collections
import hashlib
from abc import abstractmethod

from nuitka import Options
from nuitka.__past__ import getMetaClassBase, iterItems
from nuitka.constants.Serialization import ConstantAccessor
from nuitka.PythonVersions import python_version
from nuitka.utils.InstanceCounters import (
    counted_del,
    counted_init,
    isCountingInstances,
)

from .VariableDeclarations import VariableDeclaration, VariableStorage

# Many methods won't use self, but it's the interface. pylint: disable=no-self-use


class TempMixin(object):
    # Lots of details, everything gets to store bits here, to indicate
    # code generation states, and there are many, pylint: disable=too-many-instance-attributes

    def __init__(self):
        self.tmp_names = {}

        self.labels = {}

        # For exception and loop handling
        self.exception_escape = None
        self.loop_continue = None
        self.loop_break = None

        # For branches
        self.true_target = None
        self.false_target = None

        self.keeper_variable_count = 0
        self.exception_keepers = (None, None, None, None)

        self.preserver_variable_declaration = {}

        self.cleanup_names = []

    def _formatTempName(self, base_name, number):
        if number is None:
            return "tmp_{name}".format(name=base_name)
        else:
            return "tmp_{name}_{number:d}".format(name=base_name, number=number)

    def allocateTempName(self, base_name, type_name="PyObject *", unique=False):
        # We might be hard coding too many details for special temps
        # here, pylint: disable=too-many-branches

        if unique:
            number = None
        else:
            number = self.tmp_names.get(base_name, 0)
            number += 1

        self.tmp_names[base_name] = number

        formatted_name = self._formatTempName(base_name=base_name, number=number)

        if unique:
            result = self.variable_storage.getVariableDeclarationTop(formatted_name)

            if result is None:
                if base_name == "outline_return_value":
                    init_value = "NULL"
                elif base_name == "return_value":
                    init_value = "NULL"
                elif base_name == "generator_return":
                    init_value = "false"
                else:
                    init_value = None

                if base_name == "unused":
                    result = self.variable_storage.addVariableDeclarationFunction(
                        c_type=type_name,
                        code_name=formatted_name,
                        init_value=init_value,
                    )
                else:
                    result = self.variable_storage.addVariableDeclarationTop(
                        c_type=type_name,
                        code_name=formatted_name,
                        init_value=init_value,
                    )
            else:
                if type_name.startswith("NUITKA_MAY_BE_UNUSED"):
                    type_name = type_name[21:]

                assert result.c_type == type_name

        else:
            result = self.variable_storage.addVariableDeclarationLocal(
                c_type=type_name, code_name=formatted_name
            )

        return result

    def skipTempName(self, base_name):
        number = self.tmp_names.get(base_name, 0)
        number += 1
        self.tmp_names[base_name] = number

    def getIntResName(self):
        return self.allocateTempName("res", "int", unique=True)

    def getBoolResName(self):
        return self.allocateTempName("result", "bool", unique=True)

    def hasTempName(self, base_name):
        return base_name in self.tmp_names

    def getExceptionEscape(self):
        return self.exception_escape

    def setExceptionEscape(self, label):
        result = self.exception_escape
        self.exception_escape = label
        return result

    def getLoopBreakTarget(self):
        return self.loop_break

    def setLoopBreakTarget(self, label):
        result = self.loop_break
        self.loop_break = label
        return result

    def getLoopContinueTarget(self):
        return self.loop_continue

    def setLoopContinueTarget(self, label):
        result = self.loop_continue
        self.loop_continue = label
        return result

    def allocateLabel(self, label):
        result = self.labels.get(label, 0)
        result += 1
        self.labels[label] = result

        return "{name}_{number:d}".format(name=label, number=result)

    def getLabelCount(self, label):
        return self.labels.get(label, 0)

    def allocateExceptionKeeperVariables(self):
        self.keeper_variable_count += 1

        # For finally handlers of Python3, which have conditions on assign and
        # use, the NULL init is needed.
        debug = Options.is_debug and python_version >= 0x300

        if debug:
            keeper_obj_init = "NULL"
        else:
            keeper_obj_init = None

        return (
            self.variable_storage.addVariableDeclarationTop(
                "PyObject *",
                "exception_keeper_type_%d" % self.keeper_variable_count,
                keeper_obj_init,
            ),
            self.variable_storage.addVariableDeclarationTop(
                "PyObject *",
                "exception_keeper_value_%d" % self.keeper_variable_count,
                keeper_obj_init,
            ),
            self.variable_storage.addVariableDeclarationTop(
                "PyTracebackObject *",
                "exception_keeper_tb_%d" % self.keeper_variable_count,
                keeper_obj_init,
            ),
            self.variable_storage.addVariableDeclarationTop(
                "NUITKA_MAY_BE_UNUSED int",
                "exception_keeper_lineno_%d" % self.keeper_variable_count,
                "0" if debug else None,
            ),
        )

    def getExceptionKeeperVariables(self):
        return self.exception_keepers

    def setExceptionKeeperVariables(self, keeper_vars):
        result = self.exception_keepers
        self.exception_keepers = tuple(keeper_vars)
        return result

    def addExceptionPreserverVariables(self, preserver_id):
        # For finally handlers of Python3, which have conditions on assign and
        # use.
        if preserver_id not in self.preserver_variable_declaration:

            debug = Options.is_debug and python_version >= 0x300

            if debug:
                preserver_obj_init = "NULL"
            else:
                preserver_obj_init = None

            self.preserver_variable_declaration[preserver_id] = (
                self.variable_storage.addVariableDeclarationTop(
                    "PyObject *",
                    "exception_preserved_type_%d" % preserver_id,
                    preserver_obj_init,
                ),
                self.variable_storage.addVariableDeclarationTop(
                    "PyObject *",
                    "exception_preserved_value_%d" % preserver_id,
                    preserver_obj_init,
                ),
                self.variable_storage.addVariableDeclarationTop(
                    "PyTracebackObject *",
                    "exception_preserved_tb_%d" % preserver_id,
                    preserver_obj_init,
                ),
            )

        return self.preserver_variable_declaration[preserver_id]

    def getTrueBranchTarget(self):
        return self.true_target

    def getFalseBranchTarget(self):
        return self.false_target

    def setTrueBranchTarget(self, label):
        self.true_target = label

    def setFalseBranchTarget(self, label):
        self.false_target = label

    def getCleanupTempnames(self):
        return self.cleanup_names[-1]

    def addCleanupTempName(self, tmp_name):
        assert tmp_name not in self.cleanup_names[-1], tmp_name
        assert (
            tmp_name.c_type != "nuitka_void" or tmp_name.code_name == "tmp_unused"
        ), tmp_name

        self.cleanup_names[-1].append(tmp_name)

    def removeCleanupTempName(self, tmp_name):
        assert tmp_name in self.cleanup_names[-1], tmp_name
        self.cleanup_names[-1].remove(tmp_name)

    def needsCleanup(self, tmp_name):
        return tmp_name in self.cleanup_names[-1]

    def pushCleanupScope(self):
        self.cleanup_names.append([])

    def popCleanupScope(self):
        assert not self.cleanup_names[-1]
        del self.cleanup_names[-1]


CodeObjectHandle = collections.namedtuple(
    "CodeObjectHandle",
    (
        "co_name",
        "co_kind",
        "co_varnames",
        "co_argcount",
        "co_posonlyargcount",
        "co_kwonlyargcount",
        "co_has_starlist",
        "co_has_stardict",
        "co_filename",
        "line_number",
        "future_flags",
        "co_new_locals",
        "co_freevars",
        "is_optimized",
    ),
)


class CodeObjectsMixin(object):
    def __init__(self):
        # Code objects needed made unique by a key.
        self.code_objects = {}

    def getCodeObjects(self):
        return sorted(iterItems(self.code_objects))

    def getCodeObjectHandle(self, code_object):
        key = CodeObjectHandle(
            co_filename=code_object.getFilename(),
            co_name=code_object.getCodeObjectName(),
            line_number=code_object.getLineNumber(),
            co_varnames=code_object.getVarNames(),
            co_argcount=code_object.getArgumentCount(),
            co_freevars=code_object.getFreeVarNames(),
            co_posonlyargcount=code_object.getPosOnlyParameterCount(),
            co_kwonlyargcount=code_object.getKwOnlyParameterCount(),
            co_kind=code_object.getCodeObjectKind(),
            is_optimized=code_object.getFlagIsOptimizedValue(),
            co_new_locals=code_object.getFlagNewLocalsValue(),
            co_has_starlist=code_object.hasStarListArg(),
            co_has_stardict=code_object.hasStarDictArg(),
            future_flags=code_object.getFutureSpec().asFlags(),
        )

        if key not in self.code_objects:
            self.code_objects[key] = "codeobj_%s" % self._calcHash(key)

        return self.code_objects[key]

    if python_version < 0x300:

        def _calcHash(self, key):
            hash_value = hashlib.md5("-".join(str(s) for s in key))

            return hash_value.hexdigest()

    else:

        def _calcHash(self, key):
            hash_value = hashlib.md5("-".join(str(s) for s in key).encode("utf-8"))

            return hash_value.hexdigest()


class PythonContextBase(getMetaClassBase("Context")):
    @counted_init
    def __init__(self):
        self.source_ref = None

        self.current_source_ref = None
        self.last_source_ref = None

    if isCountingInstances():
        __del__ = counted_del()

    def getCurrentSourceCodeReference(self):
        return self.current_source_ref

    def setCurrentSourceCodeReference(self, value):
        result = self.current_source_ref
        self.current_source_ref = value

        if value is not None:
            self.last_source_ref = result

        return result

    def getLastSourceCodeReference(self):
        result = self.last_source_ref
        # self.last_source_ref = None
        return result

    def getInplaceLeftName(self):
        return self.allocateTempName("inplace_orig", "PyObject *", True)

    @abstractmethod
    def getConstantCode(self, constant):
        pass

    @abstractmethod
    def getModuleCodeName(self):
        pass

    @abstractmethod
    def getModuleName(self):
        pass

    @abstractmethod
    def addHelperCode(self, key, code):
        pass

    @abstractmethod
    def hasHelperCode(self, key):
        pass

    @abstractmethod
    def addDeclaration(self, key, code):
        pass

    @abstractmethod
    def pushFrameVariables(self, frame_variables):
        pass

    @abstractmethod
    def popFrameVariables(self):
        pass

    @abstractmethod
    def getFrameVariableTypeDescriptions(self):
        pass

    @abstractmethod
    def getFrameVariableTypeDescription(self):
        pass

    @abstractmethod
    def getFrameTypeDescriptionDeclaration(self):
        pass

    @abstractmethod
    def getFrameVariableCodeNames(self):
        pass

    @abstractmethod
    def allocateTempName(self, base_name, type_name="PyObject *", unique=False):
        pass

    @abstractmethod
    def skipTempName(self, base_name):
        pass

    @abstractmethod
    def getIntResName(self):
        pass

    @abstractmethod
    def getBoolResName(self):
        pass

    @abstractmethod
    def hasTempName(self, base_name):
        pass

    @abstractmethod
    def getExceptionEscape(self):
        pass

    @abstractmethod
    def setExceptionEscape(self, label):
        pass

    @abstractmethod
    def getLoopBreakTarget(self):
        pass

    @abstractmethod
    def setLoopBreakTarget(self, label):
        pass

    @abstractmethod
    def getLoopContinueTarget(self):
        pass

    @abstractmethod
    def setLoopContinueTarget(self, label):
        pass

    @abstractmethod
    def allocateLabel(self, label):
        pass

    @abstractmethod
    def allocateExceptionKeeperVariables(self):
        pass

    @abstractmethod
    def getExceptionKeeperVariables(self):
        pass

    @abstractmethod
    def setExceptionKeeperVariables(self, keeper_vars):
        pass

    @abstractmethod
    def addExceptionPreserverVariables(self, count):
        pass

    @abstractmethod
    def getTrueBranchTarget(self):
        pass

    @abstractmethod
    def getFalseBranchTarget(self):
        pass

    @abstractmethod
    def setTrueBranchTarget(self, label):
        pass

    @abstractmethod
    def setFalseBranchTarget(self, label):
        pass

    @abstractmethod
    def getCleanupTempnames(self):
        pass

    @abstractmethod
    def addCleanupTempName(self, tmp_name):
        pass

    @abstractmethod
    def removeCleanupTempName(self, tmp_name):
        pass

    @abstractmethod
    def needsCleanup(self, tmp_name):
        pass

    @abstractmethod
    def pushCleanupScope(self):
        pass

    @abstractmethod
    def popCleanupScope(self):
        pass


class PythonChildContextBase(PythonContextBase):
    # Base classes can be abstract, pylint: disable=I0021,abstract-method

    def __init__(self, parent):
        PythonContextBase.__init__(self)

        self.parent = parent

    def getConstantCode(self, constant):
        return self.parent.getConstantCode(constant)

    def getModuleCodeName(self):
        return self.parent.getModuleCodeName()

    def getModuleName(self):
        return self.parent.getModuleName()

    def addHelperCode(self, key, code):
        return self.parent.addHelperCode(key, code)

    def hasHelperCode(self, key):
        return self.parent.hasHelperCode(key)

    def addDeclaration(self, key, code):
        self.parent.addDeclaration(key, code)

    def pushFrameVariables(self, frame_variables):
        return self.parent.pushFrameVariables(frame_variables)

    def popFrameVariables(self):
        return self.parent.popFrameVariables()

    def getFrameVariableTypeDescriptions(self):
        return self.parent.getFrameVariableTypeDescriptions()

    def getFrameVariableTypeDescription(self):
        return self.parent.getFrameVariableTypeDescription()

    def getFrameTypeDescriptionDeclaration(self):
        return self.parent.getFrameTypeDescriptionDeclaration()

    def getFrameVariableCodeNames(self):
        return self.parent.getFrameVariableCodeNames()

    def addFunctionCreationInfo(self, creation_info):
        return self.parent.addFunctionCreationInfo(creation_info)


class FrameDeclarationsMixin(object):
    def __init__(self):
        # Frame is active or not, default not.
        self.frame_variables_stack = [""]
        # Type descriptions of the current frame.
        self.frame_type_descriptions = [()]

        # Types of variables for current frame.
        self.frame_variable_types = {}

        self.frames_used = 0

        # Currently active frame stack inside the context.
        self.frame_stack = [None]

        self.locals_dict_names = None

    def getFrameHandle(self):
        return self.frame_stack[-1]

    def pushFrameHandle(self, code_identifier, is_light):
        self.frames_used += 1

        if is_light:
            frame_identifier = VariableDeclaration(
                "struct Nuitka_FrameObject *",
                "m_frame",
                None,
                self.getContextObjectName(),
            )

        else:
            frame_handle = code_identifier.replace("codeobj_", "frame_")

            if self.frames_used > 1:
                frame_handle += "_%d" % self.frames_used

            frame_identifier = self.variable_storage.addVariableDeclarationTop(
                "struct Nuitka_FrameObject *", frame_handle, None
            )

        self.variable_storage.addVariableDeclarationTop(
            "NUITKA_MAY_BE_UNUSED char const *",
            "type_description_%d" % self.frames_used,
            "NULL",
        )

        self.frame_stack.append(frame_identifier)
        return frame_identifier

    def popFrameHandle(self):
        result = self.frame_stack[-1]
        del self.frame_stack[-1]

        return result

    def getFramesCount(self):
        return self.frames_used

    def pushFrameVariables(self, frame_variables):
        """ Set current the frame variables. """
        self.frame_variables_stack.append(frame_variables)
        self.frame_type_descriptions.append(set())

    def popFrameVariables(self):
        """ End of frame, restore previous ones. """
        del self.frame_variables_stack[-1]
        del self.frame_type_descriptions[-1]

    def setVariableType(self, variable, variable_declaration):
        assert variable.isLocalVariable(), variable

        # TODO: Change value of that dict to take advantage of declaration.
        self.frame_variable_types[variable] = (
            str(variable_declaration),
            variable_declaration.getCType().getTypeIndicator(),
        )

    def getFrameVariableTypeDescriptions(self):
        return self.frame_type_descriptions[-1]

    def getFrameTypeDescriptionDeclaration(self):
        return self.variable_storage.getVariableDeclarationTop(
            "type_description_%d" % (len(self.frame_stack) - 1)
        )

    def getFrameVariableTypeDescription(self):
        result = "".join(
            self.frame_variable_types.get(variable, ("NULL", "N"))[1]
            for variable in self.frame_variables_stack[-1]
        )

        if result:
            self.frame_type_descriptions[-1].add(result)

        return result

    def getFrameVariableCodeNames(self):
        result = []

        for variable in self.frame_variables_stack[-1]:
            variable_code_name, variable_code_type = self.frame_variable_types.get(
                variable, ("NULL", "N")
            )

            if variable_code_type in ("b",):
                result.append("(int)" + variable_code_name)
            else:
                result.append(variable_code_name)

        return result

    def getLocalsDictNames(self):
        return self.locals_dict_names or ()

    def addLocalsDictName(self, locals_dict_name):
        result = self.variable_storage.getVariableDeclarationTop(locals_dict_name)

        if result is None:
            result = self.variable_storage.addVariableDeclarationTop(
                "PyObject *", locals_dict_name, "NULL"
            )

        if self.locals_dict_names is None:
            self.locals_dict_names = set()

        self.locals_dict_names.add(result)

        return result


class ReturnReleaseModeMixin(object):
    def __init__(self):
        self.return_release_mode = False

        self.return_exit = None

    def setReturnReleaseMode(self, value):
        result = self.return_release_mode
        self.return_release_mode = value
        return result

    def getReturnReleaseMode(self):
        return self.return_release_mode

    def setReturnTarget(self, label):
        result = self.return_exit
        self.return_exit = label
        return result

    def getReturnTarget(self):
        return self.return_exit


class ReturnValueNameMixin(object):
    def __init__(self):
        self.return_name = None

    def getReturnValueName(self):
        if self.return_name is None:
            self.return_name = self.allocateTempName("return_value", unique=True)

        return self.return_name

    def setReturnValueName(self, value):
        result = self.return_name
        self.return_name = value
        return result


class PythonModuleContext(
    TempMixin,
    CodeObjectsMixin,
    FrameDeclarationsMixin,
    ReturnReleaseModeMixin,
    ReturnValueNameMixin,
    PythonContextBase,
):
    # Plenty of attributes, because it's storing so many different things.
    # pylint: disable=too-many-instance-attributes

    def __init__(self, module, data_filename):
        PythonContextBase.__init__(self)

        TempMixin.__init__(self)
        CodeObjectsMixin.__init__(self)
        FrameDeclarationsMixin.__init__(self)
        ReturnReleaseModeMixin.__init__(self)

        # TODO: For outlines bodies.
        ReturnValueNameMixin.__init__(self)

        self.module = module
        self.name = module.getFullName()
        self.code_name = module.getCodeName()

        self.declaration_codes = {}
        self.helper_codes = {}

        self.frame_handle = None

        self.variable_storage = VariableStorage(heap_name=None)

        self.function_table_entries = []

        self.constant_accessor = ConstantAccessor(
            top_level_name="mod_consts", data_filename=data_filename
        )

    def __repr__(self):
        return "<PythonModuleContext instance for module %s>" % self.name

    def getOwner(self):
        return self.module

    def getEntryPoint(self):
        return self.module

    def isCompiledPythonModule(self):
        return True

    def getName(self):
        return self.name

    def mayRaiseException(self):
        body = self.module.subnode_body

        return body is not None and body.mayRaiseException(BaseException)

    getModuleName = getName

    def getModuleCodeName(self):
        return self.code_name

    def setFrameGuardMode(self, guard_mode):
        assert guard_mode == "once"

    def addHelperCode(self, key, code):
        assert key not in self.helper_codes, key

        self.helper_codes[key] = code

    def hasHelperCode(self, key):
        return key in self.helper_codes

    def getHelperCodes(self):
        return self.helper_codes

    def addDeclaration(self, key, code):
        assert key not in self.declaration_codes

        self.declaration_codes[key] = code

    def getDeclarations(self):
        return self.declaration_codes

    def mayRecurse(self):
        return False

    def getConstantCode(self, constant):
        return self.constant_accessor.getConstantCode(constant)

    def getConstantsCount(self):
        return self.constant_accessor.getConstantsCount()

    def addFunctionCreationInfo(self, creation_info):
        self.function_table_entries.append(creation_info)

    def getFunctionCreationInfos(self):
        result = self.function_table_entries

        # Release the memory once possible.
        del self.function_table_entries
        return result


class PythonFunctionContext(
    FrameDeclarationsMixin,
    TempMixin,
    ReturnReleaseModeMixin,
    ReturnValueNameMixin,
    PythonChildContextBase,
):
    def __init__(self, parent, function):
        PythonChildContextBase.__init__(self, parent=parent)

        TempMixin.__init__(self)
        FrameDeclarationsMixin.__init__(self)
        ReturnReleaseModeMixin.__init__(self)
        ReturnValueNameMixin.__init__(self)

        self.function = function

        self.setExceptionEscape("function_exception_exit")
        self.setReturnTarget("function_return_exit")

        self.frame_handle = None

        self.variable_storage = self._makeVariableStorage()

    def _makeVariableStorage(self):
        return VariableStorage(heap_name=None)

    def __repr__(self):
        return "<%s for %s '%s'>" % (
            self.__class__.__name__,
            "function" if not self.function.isExpressionClassBody() else "class",
            self.function.getName(),
        )

    def getFunction(self):
        return self.function

    def getOwner(self):
        return self.function

    def getEntryPoint(self):
        return self.function

    def mayRecurse(self):
        # TODO: Determine this at compile time for enhanced optimizations.
        return True

    def getCodeObjectHandle(self, code_object):
        return self.parent.getCodeObjectHandle(code_object)


class PythonFunctionDirectContext(PythonFunctionContext):
    def isForDirectCall(self):
        return True

    def isForCreatedFunction(self):
        return False


class PythonGeneratorObjectContext(PythonFunctionContext):
    def _makeVariableStorage(self):
        return VariableStorage(heap_name="%s_heap" % self.getContextObjectName())

    def isForDirectCall(self):
        return False

    def isForCreatedFunction(self):
        return False

    def getContextObjectName(self):
        return "generator"

    def getGeneratorReturnValueName(self):
        if python_version >= 0x300:
            return self.allocateTempName("return_value", "PyObject *", unique=True)
        else:
            return self.allocateTempName("generator_return", "bool", unique=True)


class PythonCoroutineObjectContext(PythonGeneratorObjectContext):
    def getContextObjectName(self):
        return "coroutine"


class PythonAsyncgenObjectContext(PythonGeneratorObjectContext):
    def getContextObjectName(self):
        return "asyncgen"


class PythonFunctionCreatedContext(PythonFunctionContext):
    def isForDirectCall(self):
        return False

    def isForCreatedFunction(self):
        return True


class PythonFunctionOutlineContext(
    ReturnReleaseModeMixin, ReturnValueNameMixin, PythonChildContextBase
):
    def __init__(self, parent, outline):
        PythonChildContextBase.__init__(self, parent=parent)

        ReturnReleaseModeMixin.__init__(self)
        ReturnValueNameMixin.__init__(self)

        self.outline = outline

        self.variable_storage = parent.variable_storage

    def getOwner(self):
        return self.outline

    def getEntryPoint(self):
        return self.outline.getEntryPoint()

    def allocateLabel(self, label):
        return self.parent.allocateLabel(label)

    def allocateTempName(self, base_name, type_name="PyObject *", unique=False):
        return self.parent.allocateTempName(base_name, type_name, unique)

    def skipTempName(self, base_name):
        return self.parent.skipTempName(base_name)

    def hasTempName(self, base_name):
        return self.parent.hasTempName(base_name)

    def getCleanupTempnames(self):
        return self.parent.getCleanupTempnames()

    def addCleanupTempName(self, tmp_name):
        self.parent.addCleanupTempName(tmp_name)

    def removeCleanupTempName(self, tmp_name):
        self.parent.removeCleanupTempName(tmp_name)

    def needsCleanup(self, tmp_name):
        return self.parent.needsCleanup(tmp_name)

    def pushCleanupScope(self):
        return self.parent.pushCleanupScope()

    def popCleanupScope(self):
        self.parent.popCleanupScope()

    def getCodeObjectHandle(self, code_object):
        return self.parent.getCodeObjectHandle(code_object)

    def getExceptionEscape(self):
        return self.parent.getExceptionEscape()

    def setExceptionEscape(self, label):
        return self.parent.setExceptionEscape(label)

    def getLoopBreakTarget(self):
        return self.parent.getLoopBreakTarget()

    def setLoopBreakTarget(self, label):
        return self.parent.setLoopBreakTarget(label)

    def getLoopContinueTarget(self):
        return self.parent.getLoopContinueTarget()

    def setLoopContinueTarget(self, label):
        return self.parent.setLoopContinueTarget(label)

    def getTrueBranchTarget(self):
        return self.parent.getTrueBranchTarget()

    def getFalseBranchTarget(self):
        return self.parent.getFalseBranchTarget()

    def setTrueBranchTarget(self, label):
        self.parent.setTrueBranchTarget(label)

    def setFalseBranchTarget(self, label):
        self.parent.setFalseBranchTarget(label)

    def getFrameHandle(self):
        return self.parent.getFrameHandle()

    def pushFrameHandle(self, code_identifier, is_light):
        return self.parent.pushFrameHandle(code_identifier, is_light)

    def popFrameHandle(self):
        return self.parent.popFrameHandle()

    def getExceptionKeeperVariables(self):
        return self.parent.getExceptionKeeperVariables()

    def setExceptionKeeperVariables(self, keeper_vars):
        return self.parent.setExceptionKeeperVariables(keeper_vars)

    def setVariableType(self, variable, variable_declaration):
        self.parent.setVariableType(variable, variable_declaration)

    def getIntResName(self):
        return self.parent.getIntResName()

    def getBoolResName(self):
        return self.parent.getBoolResName()

    def allocateExceptionKeeperVariables(self):
        return self.parent.allocateExceptionKeeperVariables()

    def isForDirectCall(self):
        return self.parent.isForDirectCall()

    def mayRecurse(self):
        # The outline is only accessible via its parent.
        return self.parent.mayRecurse()

    def addLocalsDictName(self, locals_dict_name):
        return self.parent.addLocalsDictName(locals_dict_name)

    def addExceptionPreserverVariables(self, count):
        return self.parent.addExceptionPreserverVariables(count)

    def getContextObjectName(self):
        return self.parent.getContextObjectName()
