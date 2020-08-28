#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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


class ModuleName(str):
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

    def hasNamespace(self, package_name):
        return self == package_name or self.isBelowNamespace(package_name)

    def hasOneOfNamespaces(self, *package_names):
        for package_name in package_names:
            if self.hasNamespace(package_name):
                return True

        return False

    def isBelowNamespace(self, package_name):
        return self.startswith(package_name + ".")
