# MIT License
#
# Copyright The SCons Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""The SCons warnings framework."""

import sys

import SCons.Errors

class SConsWarning(SCons.Errors.UserError):
    pass

class WarningOnByDefault(SConsWarning):
    pass


# NOTE:  If you add a new warning class, add it to the man page, too!
# Not all warnings are defined here, some are defined in the location of use

class TargetNotBuiltWarning(SConsWarning): # Should go to OnByDefault
    pass

class CacheVersionWarning(WarningOnByDefault):
    pass

class CacheWriteErrorWarning(SConsWarning):
    pass

class CorruptSConsignWarning(WarningOnByDefault):
    pass

class DependencyWarning(SConsWarning):
    pass

class DevelopmentVersionWarning(WarningOnByDefault):
    pass

class DuplicateEnvironmentWarning(WarningOnByDefault):
    pass

class FutureReservedVariableWarning(WarningOnByDefault):
    pass

class LinkWarning(WarningOnByDefault):
    pass

class MisleadingKeywordsWarning(WarningOnByDefault):
    pass

class MissingSConscriptWarning(WarningOnByDefault):
    pass

class NoObjectCountWarning(WarningOnByDefault):
    pass

class NoParallelSupportWarning(WarningOnByDefault):
    pass

class ReservedVariableWarning(WarningOnByDefault):
    pass

class StackSizeWarning(WarningOnByDefault):
    pass

class VisualCMissingWarning(WarningOnByDefault):
    pass

# Used when MSVC_VERSION and MSVS_VERSION do not point to the
# same version (MSVS_VERSION is deprecated)
class VisualVersionMismatch(WarningOnByDefault):
    pass

class VisualStudioMissingWarning(SConsWarning):
    pass

class FortranCxxMixWarning(LinkWarning):
    pass


# Deprecation warnings

class FutureDeprecatedWarning(SConsWarning):
    pass

class DeprecatedWarning(SConsWarning):
    pass

class MandatoryDeprecatedWarning(DeprecatedWarning):
    pass


# Special case; base always stays DeprecatedWarning
class PythonVersionWarning(DeprecatedWarning):
    pass

class DeprecatedSourceCodeWarning(FutureDeprecatedWarning):
    pass

class TaskmasterNeedsExecuteWarning(DeprecatedWarning):
    pass

class DeprecatedOptionsWarning(MandatoryDeprecatedWarning):
    pass

class DeprecatedDebugOptionsWarning(MandatoryDeprecatedWarning):
    pass

class DeprecatedMissingSConscriptWarning(DeprecatedWarning):
    pass

class ToolQtDeprecatedWarning(FutureDeprecatedWarning):
    pass

# The below is a list of 2-tuples.  The first element is a class object.
# The second element is true if that class is enabled, false if it is disabled.
_enabled = []

# If set, raise the warning as an exception
_warningAsException = False

# If not None, a function to call with the warning
_warningOut = None

def suppressWarningClass(clazz):
    """Suppresses all warnings of type clazz or derived from clazz."""
    _enabled.insert(0, (clazz, False))

def enableWarningClass(clazz):
    """Enables all warnings of type clazz or derived from clazz."""
    _enabled.insert(0, (clazz, True))

def warningAsException(flag=True):
    """Set global _warningAsExeption flag.

    Args:
        flag: value to set warnings-as-exceptions to [default: True]

    Returns:
        The previous value.
    """
    global _warningAsException
    old = _warningAsException
    _warningAsException = flag
    return old

def warn(clazz, *args):
    """Issue a warning, accounting for SCons rules.

    Check if warnings for this class are enabled.
    If warnings are treated as exceptions, raise exception.
    Use the global warning-emitter _warningOut, which allows selecting
    different ways of presenting a traceback (see Script/Main.py)
    """
    warning = clazz(args)
    for cls, flag in _enabled:
        if isinstance(warning, cls):
            if flag:
                if _warningAsException:
                    raise warning

                if _warningOut:
                    _warningOut(warning)
            break

def process_warn_strings(arguments):
    """Process requests to enable/disable warnings.

    The requests are strings passed to the --warn option or the
    SetOption('warn') function.

    An argument to this option should be of the form "warning-class"
    or "no-warning-class".  The warning class is munged and has
    the suffix "Warning" added in order to get an actual class name
    from the classes above, which we need to pass to the
    {enable,disable}WarningClass() functions.

    For example, "deprecated" will enable the DeprecatedWarning class.
    "no-dependency" will disable the DependencyWarning class.

    As a special case, --warn=all and --warn=no-all will enable or
    disable (respectively) the base class of all SCons warnings.
    """

    def _classmunge(s):
        """Convert a warning argument to SConsCase.

        The result is CamelCase, except "Scons" is changed to "SCons"
        """
        s = s.replace("-", " ").title().replace(" ", "")
        return s.replace("Scons", "SCons")

    for arg in arguments:
        enable = True
        if arg.startswith("no-"):
            enable = False
            arg = arg[len("no-") :]
        if arg == 'all':
            class_name = "SConsWarning"
        else:
            class_name = _classmunge(arg) + 'Warning'
        try:
            clazz = globals()[class_name]
        except KeyError:
            sys.stderr.write("No warning type: '%s'\n" % arg)
        else:
            if enable:
                enableWarningClass(clazz)
            elif issubclass(clazz, MandatoryDeprecatedWarning):
                fmt = "Can not disable mandataory warning: '%s'\n"
                sys.stderr.write(fmt % arg)
            else:
                suppressWarningClass(clazz)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
