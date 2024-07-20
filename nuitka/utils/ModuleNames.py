#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Module names are common string type, which deserves special operations.

These are used in Nuitka for module and package names in most places, and
allow to easily make checks on them.

"""

import fnmatch
import os


def checkModuleName(value):
    return ".." not in str(value) and not (
        str(value).endswith(".") or str(value) == "."
    )


# Trigger names for shared use.
post_module_load_trigger_name = "-postLoad"
pre_module_load_trigger_name = "-preLoad"

trigger_names = (pre_module_load_trigger_name, post_module_load_trigger_name)


def makeTriggerModuleName(module_name, trigger_name):
    assert trigger_name in trigger_names

    return ModuleName(module_name + trigger_name)


# Multidist prefix
_multi_dist_prefix = "multidist-"


def makeMultidistModuleName(count, suffix):
    return ModuleName("%s%d-%s" % (_multi_dist_prefix, count, suffix))


class ModuleName(str):
    def __init__(self, value):
        assert checkModuleName(value), value

        # TODO: Disallow some conversion, e.g. from module, function, etc.
        # objects, and white list what types we accept.

        str.__init__(value)

    @staticmethod
    def makeModuleNameInPackage(module_name, package_name):
        """Create a module name in a package.

        Args:
            - module_name (str or ModuleName) module name to put below the package
            - package_name (str or ModuleName or None) package to put below

        Returns:
            Module name "package_name.module_name" or if "package_name" is None
            then simply "module_name".

        Notes:
            Prefer this factory function over manually duplicating the pattern
            behind it.

        """

        if package_name is not None:
            return ModuleName(package_name + "." + module_name)
        else:
            return ModuleName(module_name)

    def __repr__(self):
        return "<ModuleName '%s'>" % str(self)

    def asString(self):
        """Get a simply str value.

        Notes:
            This should only be used to create constant values for code
            generation, there is no other reason to lower the type of
            these values otherwise.
        """

        return str(self)

    def asPath(self):
        return str(self).replace(".", os.path.sep)

    def getPackageName(self):
        """Get the package name if any.

        Returns:
            ModuleName of the containing package or None if already
            top level.
        """

        return self.splitModuleBasename()[0]

    def getParentPackageNames(self):
        """Yield parent packages in descending order."""
        parent_packages = []

        parent_package = self.getPackageName()
        while parent_package is not None:
            parent_packages.append(parent_package)

            parent_package = parent_package.getPackageName()

        for parent_package in reversed(parent_packages):
            yield parent_package

    def getRelativePackageName(self, level):
        assert level >= 0

        parts = self.asString().split(".")

        while level > 0:
            if not parts:
                return None

            del parts[-1]
            level -= 1

        return ModuleName(".".join(parts))

    def getTopLevelPackageName(self):
        """Get the top level package name.

        Returns:
            ModuleName of the top level name.
        """
        package_name = self.getPackageName()

        if package_name is None:
            return self
        else:
            return package_name.getTopLevelPackageName()

    def getBasename(self):
        """Get leaf name of the module without package part.

        Returns:
            ModuleName without package.
        """
        return self.splitModuleBasename()[1]

    def splitModuleBasename(self):
        """Split a module into package name and module name."""

        if "." in self:
            package_part = ModuleName(self[: self.rfind(".")])
            module_name = ModuleName(self[self.rfind(".") + 1 :])
        else:
            package_part = None
            module_name = self

        return package_part, module_name

    def splitPackageName(self):
        """Split a module into the top level package name and remaining module name."""

        if "." in self:
            package_part = ModuleName(self[: self.find(".")])
            module_name = ModuleName(self[self.find(".") + 1 :])
        else:
            package_part = None
            module_name = self

        return package_part, module_name

    def hasNamespace(self, package_name):
        return self == package_name or self.isBelowNamespace(package_name)

    def hasOneOfNamespaces(self, *package_names):
        """Check if a module name is below one of many namespaces.

        Args:
            - package_names: Star argument that allows also lists and tuples

        Returns:
            bool - module name is below one of the packages.
        """

        for package_name in package_names:
            if type(package_name) in (tuple, list, set):
                if self.hasOneOfNamespaces(*package_name):
                    return True
            elif self.hasNamespace(package_name):
                return True

        return False

    def isBelowNamespace(self, package_name):
        assert type(package_name) in (str, ModuleName), package_name

        # Avoid startswith on these.
        return str(self).startswith(package_name + ".")

    def getChildNamed(self, *args):
        """Get a child package with these names added."""
        return ModuleName(".".join([self] + list(args)))

    def getSiblingNamed(self, *args):
        """Get a sub-package relative to this child package."""
        return self.getPackageName().getChildNamed(*args)

    def relocateModuleNamespace(self, parent_old, parent_new):
        """Get a module name, where the top level part is translated from old to new."""
        assert self.hasNamespace(parent_old)

        submodule_name_str = str(self)[len(str(parent_old)) + 1 :]

        if submodule_name_str:
            return ModuleName(parent_new).getChildNamed(submodule_name_str)
        else:
            return ModuleName(parent_new)

    def getChildNameFromPackage(self, package_name):
        """Get child a module name part for a name in the package."""
        assert self.hasNamespace(package_name)

        submodule_name_str = str(self)[len(str(package_name)) + 1 :]
        return ModuleName(submodule_name_str)

    def matchesToShellPattern(self, pattern):
        """Match a module name to a patterns

        Args:
            pattern:
                Complies with fnmatch.fnmatch description
                or also is below the package. So "*.tests" will matches to also
                "something.tests.MyTest", thereby allowing to match whole
                packages with one pattern only.
        Returns:
            Tuple of two values, where the first value is the result, second value
            explains why the pattern matched and how.
        """

        if self == pattern:
            return True, "is exact match of '%s'" % pattern
        elif self.isBelowNamespace(pattern):
            return True, "is package content of '%s'" % pattern
        elif fnmatch.fnmatch(self.asString(), pattern):
            return True, "matches pattern '%s'" % pattern
        elif fnmatch.fnmatch(self.asString(), pattern + ".*"):
            return True, "is package content of match to pattern '%s'" % pattern
        else:
            return False, None

    def matchesToShellPatterns(self, patterns):
        """Match a module name to a list of patterns

        Args:
            patterns:
                List of patterns that comply with fnmatch.fnmatch description
                or also is below the package. So "*.tests" will matches to also
                "something.tests.MyTest", thereby allowing to match whole
                packages with one pattern only.
        Returns:
            Tuple of two values, where the first value is the result, second value
            explains which pattern matched and how.
        """

        for pattern in patterns:
            match, reason = self.matchesToShellPattern(pattern)

            if match:
                return match, reason

        # No match result
        return False, None

    def isFakeModuleName(self):
        return str(self).endswith(trigger_names)

    def isMultidistModuleName(self):
        return str(self).startswith(_multi_dist_prefix)

    # Reject APIs being used. TODO: Maybe make this a decorator for reuse.
    # TODO: Add rsplit and subscript operations too.
    for _func_name in ("split", "startswith", "endswith", "__mod__"):
        code = """\
def %(func_name)s(*args, **kwargs):
    from nuitka.Errors import NuitkaCodeDeficit
    raise NuitkaCodeDeficit('''
Do not use %(func_name)s on ModuleName objects, use e.g.
.hasNamespace(),
.getBasename(),
.getTopLevelPackageName()
.hasOneOfNamespaces()

Check API documentation of nuitka.utils.ModuleNames.ModuleName for more
variations.
''')
""" % {
            "func_name": _func_name
        }

        exec(code)  # Avoid code duplication, pylint: disable=exec-used


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
