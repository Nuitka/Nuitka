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
""" Module names are common string type, which deserves special operations.

These are used in Nuitka for module and package names in most places, and
allow to easily make checks on them.

"""

import fnmatch
import os


class ModuleName(str):
    def __init__(self, value):
        assert ".." not in str(value), value

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
        return "<ModuleName %s>" % str(self)

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
        """ Split a module into package name and module name."""

        if "." in self:
            package_part = ModuleName(self[: self.rfind(".")])
            module_name = ModuleName(self[self.rfind(".") + 1 :])
        else:
            package_part = None
            module_name = self

        return package_part, module_name

    def splitPackageName(self):
        """ Split a module into the top level package name and remaining module name."""

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
            if type(package_name) in (tuple, list):
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
        return ModuleName(".".join([self] + list(args)))

    def matchesToShellPatterns(self, patterns):
        """Match a module name to a list of patterns

        Args:
            patters:
                List of patterns that comply with fnmatch.fnmatch description
                or also is below the package. So "*.tests" will matches to also
                "something.tests.MyTest", thereby allowing to match whole
                packages with one pattern only.
        Returns:
            Tuple of two values, where the first value is the result, second value
            explains which pattern matched and how.
        """

        for pattern in patterns:
            if self == pattern:
                return True, "is exact match of %r" % pattern
            elif self.isBelowNamespace(pattern):
                return True, "is package content of %r" % pattern
            elif fnmatch.fnmatch(self.asString(), pattern):
                return True, "matches pattern %r" % pattern
            elif fnmatch.fnmatch(self.asString(), pattern + ".*"):
                return True, "is package content of match to pattern %r" % pattern

        return False, None

    # Reject APIs being used. TODO: Maybe make this a decorator for reuse.
    # TODO: Add rsplit and subscript operations too.
    for _func_name in ("split", "startswith", "endswith"):
        code = """\
def %(func_name)s(*args, **kwargs):
    from nuitka.Errors import NuitkaCodeDeficit
    raise NuitkaCodeDeficit('''
Do not use %(func_name)s on ModuleName objects, use e.g.
.hasNamespace(),
.getBasename(),
.getTopLevelPackageName()
.hasOneOfNamespaces

Check API documentation of nuitka.utils.ModuleNames.ModuleName
''')
""" % {
            "func_name": _func_name
        }

        exec(code)  # Avoid code duplication, pylint: disable=exec-used
