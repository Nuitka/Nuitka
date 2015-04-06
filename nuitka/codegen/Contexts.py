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
""" Code generation contexts.

"""

import hashlib

from nuitka import Options
from nuitka.__past__ import iterItems
from nuitka.Constants import constant_builtin_types
from nuitka.utils.Utils import python_version

from .Namify import namifyConstant


# Many methods won't use self, but it's the interface. pylint: disable=R0201

class TempMixin:
    # Lots of details, everything gets to store bits here, to indicate
    # code generation states, and there are many, pylint: disable=R0902

    def __init__(self):
        self.tmp_names = {}
        self.tmp_types = {}
        self.forgotten_names = set()

        self.labels = {}

        # For exception handling
        self.needs_exception_variables = False
        self.exception_escape = None
        self.exception_ok = None
        self.loop_continue = None
        self.loop_break = None
        # Python3 frame exception stack
        self.frame_preservation_stack = []

        # For exception handlers visibility of caught exception
        self.exception_published = True

        # For branches
        self.true_target = None
        self.false_target = None

        self.keeper_variable_count = 0

    def formatTempName(self, base_name, number):
        if number is None:
            return "tmp_{name}".format(
                name = base_name
            )
        else:
            return "tmp_{name}_{number:d}".format(
                name   = base_name,
                number = number
            )

    def allocateTempName(self, base_name, type_name, unique):
        if unique:
            number = None
        else:
            number = self.tmp_names.get(base_name, 0)
            number += 1

        self.tmp_names[base_name] = number

        if base_name not in self.tmp_types:
            self.tmp_types[base_name] = type_name
        else:
            assert self.tmp_types[base_name] == type_name, \
                (self.tmp_types[base_name], type_name)

        return self.formatTempName(
            base_name = base_name,
            number    = number
        )

    def hasTempName(self, base_name):
        return base_name in self.tmp_names

    def forgetTempName(self, tmp_name):
        self.forgotten_names.add(tmp_name)

    def getTempNameInfos(self):
        result  = []

        for base_name, count in sorted(iterItems(self.tmp_names)):
            if count is not None:
                for number in range(1,count+1):
                    tmp_name = self.formatTempName(
                        base_name = base_name,
                        number    = number
                    )

                    if tmp_name not in self.forgotten_names:
                        result.append(
                            (
                                tmp_name,
                                self.tmp_types[base_name]
                            )
                        )
            else:
                tmp_name = self.formatTempName(
                    base_name = base_name,
                    number    = None
                )

                if tmp_name not in self.forgotten_names:
                    result.append(
                        (
                            tmp_name,
                            self.tmp_types[base_name]
                        )
                    )

        return result

    def getExceptionEscape(self):
        return self.exception_escape

    def setExceptionEscape(self, label):
        self.exception_escape = label

    def getExceptionNotOccurred(self):
        return self.exception_ok

    def setExceptionNotOccurred(self, label):
        self.exception_ok = label

    def isExceptionPublished(self):
        return self.exception_published

    def setExceptionPublished(self, value):
        self.exception_published = value

    def getLoopBreakTarget(self):
        return self.loop_break

    def setLoopBreakTarget(self, label, name = None):
        if name is None:
            self.loop_break = label
        else:
            self.loop_break = label, name

    def getLoopContinueTarget(self):
        return self.loop_continue

    def setLoopContinueTarget(self, label, name = None):
        if name is None:
            self.loop_continue = label
        else:
            self.loop_continue = label, name

    def allocateLabel(self, label):
        result = self.labels.get(label, 0)
        result += 1
        self.labels[label] = result

        return "{name}_{number:d}".format(
            name   = label,
            number = result
        )

    def needsExceptionVariables(self):
        return self.needs_exception_variables

    def markAsNeedsExceptionVariables(self):
        self.needs_exception_variables = True

    def getExceptionKeeperVariables(self):
        self.keeper_variable_count += 1

        return (
            "exception_keeper_type_%d" % self.keeper_variable_count,
            "exception_keeper_value_%d" % self.keeper_variable_count,
            "exception_keeper_tb_%d" % self.keeper_variable_count
        )

    def getKeeperVariableCount(self):
        return self.keeper_variable_count

    def getTrueBranchTarget(self):
        return self.true_target

    def getFalseBranchTarget(self):
        return self.false_target

    def setTrueBranchTarget(self, label):
        self.true_target = label

    def setFalseBranchTarget(self, label):
        self.false_target = label

    def pushFrameExceptionPreservationDepth(self):
        if self.frame_preservation_stack:
            self.frame_preservation_stack.append(
                self.getExceptionKeeperVariables()
            )
        else:
            self.frame_preservation_stack.append(
                None
            )

        return self.frame_preservation_stack[-1]

    def popFrameExceptionPreservationDepth(self):
        result = self.frame_preservation_stack[-1]
        del self.frame_preservation_stack[-1]
        return result


class CodeObjectsMixin:
    def __init__(self):
        # Code objects needed made unique by a key.
        self.code_objects = {}

    def getCodeObjects(self):
        return sorted(iterItems(self.code_objects))

    # Sad but true, code objects have these many details that actually are fed
    # from all different sources, pylint: disable=R0913
    def getCodeObjectHandle(self, filename, code_name, line_number, var_names,
                            arg_count, kw_only_count, is_generator,
                            is_optimized, has_starlist, has_stardict,
                            has_closure, future_flags):
        var_names = tuple(var_names)

        assert type(has_starlist) is bool
        assert type(has_stardict) is bool

        key = (
            filename,
            code_name,
            line_number,
            var_names,
            arg_count,
            kw_only_count,
            is_generator,
            is_optimized,
            has_starlist,
            has_stardict,
            has_closure,
            future_flags
        )

        if key not in self.code_objects:
            self.code_objects[key] = "codeobj_%s" % self._calcHash(key)

        return self.code_objects[key]

    if python_version < 300:
        def _calcHash(self, key):
            hash_value = hashlib.md5(
                "%s%s%d%s%d%d%s%s%s%s%s%s" % key
            )

            return hash_value.hexdigest()
    else:
        def _calcHash(self, key):
            hash_value = hashlib.md5(
                ("%s%s%d%s%d%d%s%s%s%s%s%s" % key).encode("utf-8")
            )

            return hash_value.hexdigest()


class PythonContextBase:
    def __init__(self):
        self.temp_counts = {}

        self.source_ref = None

    def isPythonModule(self):
        return False

    def allocateTempNumber(self, tmp_scope):
        result = self.temp_counts.get(tmp_scope, 0) + 1
        self.temp_counts[ tmp_scope ] = result
        return result


class PythonChildContextBase(PythonContextBase):
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
        self.parent.addHelperCode(key, code)

    def addDeclaration(self, key, code):
        self.parent.addDeclaration(key, code)



def _getConstantDefaultPopulation():
    result = (
        # Basic values that the helper code uses all the times.
        (),
        {},
        "",
        True,
        False,
        0,
        1,

        # For Python3 empty bytes, no effect for Python2, same as "", used for
        # code objects.
        b"",

        # Python mechanics, used in various helpers.
        "__module__",
        "__class__",
        "__name__",
        "__metaclass__",
        "__dict__",
        "__doc__",
        "__file__",
        "__enter__",
        "__exit__",
        "__builtins__",
        "__all__",
        "__cmp__",
        "__iter__",

        # Patched module name.
        "inspect",

        # Names of builtins used in helper code.
        "compile",
        "range",
        "open",
        "__import__",
    )

    # For Python3 modules
    if python_version >= 300:
        result += (
            "__cached__",
        )

    # For Python3 print
    if python_version >= 300:
        result += (
            "print",
            "end",
            "file",
        )

    if python_version >= 330:
        result += (
            # Modules have that attribute.
            "__loader__",
        )

    if python_version >= 340:
        result += (
            # YIELD_FROM uses this starting 3.4, with 3.3 other code is used.
            "send",
        )
    if python_version >= 330:
        result += (
            # YIELD_FROM uses this
            "throw",
            "close",
        )


    # For patching Python2 internal class type
    if python_version < 300:
        result += (
            "__getattr__",
            "__setattr__",
            "__delattr__",
        )

    # For patching Python2 sys attributes for current exception
    if python_version < 300:
        result += (
            "exc_type",
            "exc_value",
            "exc_traceback"
        )

    # The xrange built-in is Python2 only.
    if python_version < 300:
        result += (
            "xrange",
        )

    # Executables only
    if not Options.shallMakeModule():
        result += (
            "__main__",
        )

        # The "site" module is referenced in inspect patching.
        result += (
            "site",
        )

    # Builtin original values
    if not Options.shallMakeModule():
        result += (
            "type",
            "len",
            "range",
            "repr",
            "int",
            "iter",
        )

        if python_version < 300:
            result += (
                "long",
            )

    # Disabling warnings at startup
    if "no_warnings" in Options.getPythonFlags():
        result += (
            "ignore",
        )

    return result


class PythonGlobalContext:
    def __init__(self):
        self.constants = {}
        self.constant_use_count = {}

        for constant in _getConstantDefaultPopulation():
            code = self.getConstantCode(constant)

            # Force them to be global.
            self.countConstantUse(code)
            self.countConstantUse(code)

        self.needs_exception_variables = False

    def getConstantCode(self, constant):
        # Use in user code, or for constants building code itself

        if constant is None:
            key = "Py_None"
        elif constant is True:
            key = "Py_True"
        elif constant is False:
            key = "Py_False"
        elif constant is Ellipsis:
            key = "Py_Ellipsis"
        elif constant in constant_builtin_types:
            type_name = constant.__name__

            if constant is int and python_version >= 300:
                type_name = "long"

            if constant is str and python_version < 300:
                type_name = "string"

            if constant is str and python_version > 300:
                type_name = "unicode"

            key = "(PyObject *)&Py%s_Type" % type_name.title()
        else:
            key = "const_" + namifyConstant(constant)

        if key not in self.constants:
            self.constants[key] = constant

        return key

    def countConstantUse(self, constant):
        if constant not in self.constant_use_count:
            self.constant_use_count[constant] = 0

        self.constant_use_count[constant] += 1

    def getConstantUseCount(self, constant):
        return self.constant_use_count[constant]

    def getConstants(self):
        return self.constants


class FrameDeclarationsMixin:
    def __init__(self):
        self.frame_declarations = []

    def addFrameDeclaration(self, frame_decl):
        self.frame_declarations.append(frame_decl)

    def getFrameDeclarations(self):
        return self.frame_declarations


class PythonModuleContext(PythonContextBase, TempMixin, CodeObjectsMixin,
                          FrameDeclarationsMixin):
    # Plenty of attributes, because it's storing so many different things.
    # pylint: disable=R0902

    def __init__(self, module, module_name, code_name, filename, is_empty,
                global_context):
        PythonContextBase.__init__(self)

        TempMixin.__init__(self)
        CodeObjectsMixin.__init__(self)
        FrameDeclarationsMixin.__init__(self)

        self.module = module
        self.name = module_name
        self.code_name = code_name
        self.filename = filename
        self.is_empty = is_empty

        self.global_context = global_context

        self.declaration_codes = {}
        self.helper_codes = {}

        self.constants = set()

        self.frame_handle = None

        self.needs_module_filename_object = False

    def __repr__(self):
        return "<PythonModuleContext instance for module %s>" % self.filename

    def getOwner(self):
        return self.module

    def isPythonModule(self):
        return True

    def hasLocalsDict(self):
        return False

    def getFrameHandle(self):
        return self.frame_handle

    def setFrameHandle(self, frame_handle):
        self.frame_handle = frame_handle

    def getName(self):
        return self.name

    def getFilename(self):
        return self.filename

    def isEmptyModule(self):
        return self.is_empty

    getModuleName = getName

    def getModuleCodeName(self):
        return self.code_name

    # There cannot be local variable in modules no need to consider the name.
    # pylint: disable=W0613
    def hasLocalVariable(self, var_name):
        return False

    def hasClosureVariable(self, var_name):
        return False
    # pylint: enable=W0613

    def setFrameGuardMode(self, guard_mode):
        assert guard_mode == "once"

    def addHelperCode(self, key, code):
        assert key not in self.helper_codes, key

        self.helper_codes[ key ] = code

    def getHelperCodes(self):
        return self.helper_codes

    def addDeclaration(self, key, code):
        assert key not in self.declaration_codes

        self.declaration_codes[ key ] = code

    def getDeclarations(self):
        return self.declaration_codes

    def setReturnReleaseMode(self, value):
        pass

    def getReturnReleaseMode(self):
        pass

    def getReturnTarget(self):
        return None

    def setReturnTarget(self, label):
        pass

    def mayRecurse(self):
        return False

    def getConstantCode(self, constant):
        result = self.global_context.getConstantCode(constant)

        if result not in self.constants:
            self.constants.add(result)
            self.global_context.countConstantUse(result)

        return result

    def getConstants(self):
        return self.constants

    def markAsNeedsModuleFilenameObject(self):
        self.needs_module_filename_object = True

    def needsModuleFilenameObject(self):
        return self.needs_module_filename_object


class PythonFunctionContext(PythonChildContextBase, TempMixin,
                            FrameDeclarationsMixin):
    def __init__(self, parent, function):
        PythonChildContextBase.__init__(
            self,
            parent = parent
        )

        TempMixin.__init__(self)
        FrameDeclarationsMixin.__init__(self)

        self.function = function

        self.return_exit = None

        self.setExceptionEscape("function_exception_exit")
        self.setReturnTarget("function_return_exit")

        self.return_release_mode = False

        self.frame_handle = None

    def __repr__(self):
        return "<PythonFunctionContext for %s '%s'>" % (
            "function" if not self.function.isClassDictCreation() else "class",
            self.function.getName()
        )

    def getFunction(self):
        return self.function

    def getOwner(self):
        return self.function

    def hasLocalsDict(self):
        return self.function.hasLocalsDict()

    def hasLocalVariable(self, var_name):
        return var_name in self.function.getLocalVariableNames()

    def hasClosureVariable(self, var_name):
        return var_name in self.function.getClosureVariableNames()

    def getFrameHandle(self):
        return self.frame_handle

    def setFrameHandle(self, frame_handle):
        self.frame_handle = frame_handle

    def getReturnTarget(self):
        return self.return_exit

    def setReturnTarget(self, label):
        self.return_exit = label

    def setReturnReleaseMode(self, value):
        self.return_release_mode = value

    def getReturnReleaseMode(self):
        return self.return_release_mode

    def mayRecurse(self):
        # TODO: Determine this at compile time for enhanced optimizations.
        return True

    def getCodeObjectHandle(self, **kw):
        return self.parent.getCodeObjectHandle(**kw)


class PythonFunctionDirectContext(PythonFunctionContext):
    def isForDirectCall(self):
        return True

    def isForCrossModuleUsage(self):
        return self.function.isCrossModuleUsed()

    def isForCreatedFunction(self):
        return False


class PythonFunctionCreatedContext(PythonFunctionContext):
    def isForDirectCall(self):
        return False

    def isForCreatedFunction(self):
        return True


class PythonStatementCContext(PythonChildContextBase):
    def __init__(self, parent):
        PythonChildContextBase.__init__(
            self,
            parent = parent
        )

        self.cleanup_names = []

        self.current_source_ref = None
        self.last_source_ref = None

    def getOwner(self):
        return self.parent.getOwner()

    def isPythonModule(self):
        return self.parent.isPythonModule()

    def getFunction(self):
        return self.parent.getFunction()

    def hasLocalsDict(self):
        return self.parent.hasLocalsDict()

    def isForDirectCall(self):
        return self.parent.isForDirectCall()

    def allocateTempName(self, base_name, type_code = "PyObject *",
                         unique = False):
        return self.parent.allocateTempName(base_name, type_code, unique)

    def getIntResName(self):
        return self.allocateTempName("res", "int", unique = True)

    def getBoolResName(self):
        return self.allocateTempName("result", "bool", unique = True)

    def getReturnValueName(self):
        return self.allocateTempName("return_value", unique = True)

    def getGeneratorReturnValueName(self):
        if python_version >= 330:
            return self.allocateTempName(
                "return_value",
                "PyObject *",
                unique = True
            )
        else:
            return self.allocateTempName(
                "generator_return",
                "bool",
                unique = True
            )

    def getExceptionEscape(self):
        return self.parent.getExceptionEscape()

    def setExceptionEscape(self, label):
        self.parent.setExceptionEscape(label)

    def getExceptionNotOccurred(self):
        return self.parent.getExceptionNotOccurred()

    def setExceptionNotOccurred(self, label):
        self.parent.setExceptionNotOccurred(label)

    def isExceptionPublished(self):
        return self.parent.isExceptionPublished()

    def setExceptionPublished(self, value):
        self.parent.setExceptionPublished(value)

    def getLoopBreakTarget(self):
        return self.parent.getLoopBreakTarget()

    def setLoopBreakTarget(self, label, name = None):
        self.parent.setLoopBreakTarget(label, name)

    def getLoopContinueTarget(self):
        return self.parent.getLoopContinueTarget()

    def setLoopContinueTarget(self, label, name = None):
        self.parent.setLoopContinueTarget(label, name)

    def getTrueBranchTarget(self):
        return self.parent.getTrueBranchTarget()

    def setTrueBranchTarget(self, label):
        self.parent.setTrueBranchTarget(label)

    def getFalseBranchTarget(self):
        return self.parent.getFalseBranchTarget()

    def setFalseBranchTarget(self, label):
        self.parent.setFalseBranchTarget(label)

    def getReturnTarget(self):
        return self.parent.getReturnTarget()

    def setReturnTarget(self, label):
        self.parent.setReturnTarget(label)

    def getReturnReleaseMode(self):
        return self.parent.getReturnReleaseMode()

    def setReturnReleaseMode(self, value):
        self.parent.setReturnReleaseMode(value)

    def allocateLabel(self, label):
        return self.parent.allocateLabel(label)

    def addCleanupTempName(self, tmp_name):
        assert tmp_name not in self.cleanup_names, tmp_name

        self.cleanup_names.append(tmp_name)

    def removeCleanupTempName(self, tmp_name):
        assert tmp_name in self.cleanup_names, tmp_name
        self.cleanup_names.remove(tmp_name)

    def needsCleanup(self, tmp_name):
        return tmp_name in self.cleanup_names

    def isUsed(self, tmp_name):
        if tmp_name.startswith("tmp_unused_"):
            return False
        else:
            return True

    def forgetTempName(self, tmp_name):
        self.parent.forgetTempName(tmp_name)

    def getCleanupTempnames(self):
        return self.cleanup_names

    def getFrameHandle(self):
        return self.parent.getFrameHandle()

    def setFrameHandle(self, frame_handle):
        return self.parent.setFrameHandle(frame_handle)

    def getExceptionKeeperVariables(self):
        return self.parent.getExceptionKeeperVariables()

    def needsExceptionVariables(self):
        return self.parent.needsExceptionVariables()

    def markAsNeedsExceptionVariables(self):
        self.parent.markAsNeedsExceptionVariables()

    def addFrameDeclaration(self, frame_decl):
        self.parent.addFrameDeclaration(frame_decl)

    def mayRecurse(self):
        return self.parent.mayRecurse()

    def pushFrameExceptionPreservationDepth(self):
        return self.parent.pushFrameExceptionPreservationDepth()

    def popFrameExceptionPreservationDepth(self):
        return self.parent.popFrameExceptionPreservationDepth()

    def getCodeObjectHandle(self, **kw):
        return self.parent.getCodeObjectHandle(**kw)

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

    def markAsNeedsModuleFilenameObject(self):
        self.parent.markAsNeedsModuleFilenameObject()
