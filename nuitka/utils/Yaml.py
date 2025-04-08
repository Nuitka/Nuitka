#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nuitka yaml utility functions.

Because we want to work with Python2.6 or higher, we play a few tricks with
what library to use for what Python. We have an 2 inline copy of PyYAML, one
that still does 2.6 and one for newer Pythons.

Also we put loading for specific packages in here and a few helpers to work
with these config files.
"""

# Otherwise "Yaml" and "yaml" collide on case insensitive setups
from __future__ import absolute_import

import os
import pkgutil

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.Options import getUserProvidedYamlFiles
from nuitka.Tracing import general

from .FileOperations import getFileContents
from .Hashing import HashCRC32
from .Importing import importFromInlineCopy
from .ModuleNames import checkModuleName


class PackageConfigYaml(object):
    __slots__ = (
        "name",
        "data",
    )

    def __init__(self, name, file_data):
        self.name = name

        assert type(file_data) is bytes
        data = parseYaml(file_data)

        if not data:
            general.sysexit(
                """\
Error, empty (or malformed?) user package configuration '%s' used."""
                % name
            )

        assert type(data) is list, type(data)

        self.data = OrderedDict()

        for item in data:
            module_name = item.pop("module-name")

            if not module_name:
                general.sysexit(
                    "Error, invalid config in '%s' looks like an empty module name was given."
                    % (self.name)
                )

            if "/" in module_name:
                general.sysexit(
                    "Error, invalid module name in '%s' looks like a file path '%s'."
                    % (self.name, module_name)
                )

            if not checkModuleName(module_name):
                general.sysexit(
                    "Error, invalid module name in '%s' not valid '%s'."
                    % (self.name, module_name)
                )

            if module_name in self.data:
                general.sysexit("Duplicate module name '%s' encountered." % module_name)

            self.data[module_name] = item

    def __repr__(self):
        return "<PackageConfigYaml %s>" % self.name

    def get(self, name, section):
        """Return a configs for that section."""
        result = self.data.get(name)

        if result is not None:
            result = result.get(section, ())
        else:
            result = ()

        # TODO: Ought to become a list universally, but data-files currently
        # are not, and options-nanny too.
        if type(result) in (dict, OrderedDict):
            result = (result,)

        return result

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def update(self, other):
        # TODO: Full blown merging, including respecting an overload flag, where a config
        # replaces another one entirely, for now we expect to not overlap.
        for key, value in other.items():
            assert key not in self.data, key

            self.data[key] = value


def getYamlPackage():
    if not hasattr(getYamlPackage, "yaml"):
        try:
            import yaml

            getYamlPackage.yaml = yaml
        except ImportError:
            getYamlPackage.yaml = importFromInlineCopy(
                "yaml", must_exist=True, delete_module=True
            )

    return getYamlPackage.yaml


def parseYaml(data):
    yaml = getYamlPackage()

    # Make sure dictionaries are ordered even before 3.6 in the result. We use
    # them for hashing in caching keys.
    class OrderedLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)

        return OrderedDict(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
    )

    return yaml.load(data, OrderedLoader)


_yaml_cache = {}


def getYamlDataHash(data):
    result = HashCRC32()
    result.updateFromValues(data)

    return result.asHexDigest()


def parsePackageYaml(package_name, filename):
    key = package_name, filename

    if key not in _yaml_cache:
        if package_name is None:
            file_data = getFileContents(filename, mode="rb")
        else:
            file_data = pkgutil.get_data(package_name, filename)

        if file_data is None:
            raise IOError("Cannot find %s.%s" % (package_name, filename))

        _yaml_cache[key] = PackageConfigYaml(name=filename, file_data=file_data)

    return _yaml_cache[key]


_package_config = None


def getYamlPackageConfiguration():
    """Get Nuitka package configuration. Merged from multiple sources."""
    # Singleton, pylint: disable=global-statement
    global _package_config

    if _package_config is None:
        _package_config = parsePackageYaml(
            "nuitka.plugins.standard",
            "standard.nuitka-package.config.yml",
        )
        _package_config.update(
            parsePackageYaml(
                "nuitka.plugins.standard",
                "stdlib2.nuitka-package.config.yml",
            )
        )
        _package_config.update(
            parsePackageYaml(
                "nuitka.plugins.standard",
                "stdlib3.nuitka-package.config.yml",
            )
        )

        try:
            _package_config.update(
                parsePackageYaml(
                    "nuitka.plugins.commercial", "commercial.nuitka-package.config.yml"
                )
            )
        except IOError:
            # No commercial configuration found.
            pass

        # User or plugin provided filenames, but we want PRs though, and will nag
        # about it somewhat.
        for user_yaml_filename in getUserProvidedYamlFiles():
            _package_config.update(
                PackageConfigYaml(
                    name=user_yaml_filename,
                    file_data=getFileContents(user_yaml_filename, mode="rb"),
                )
            )

    return _package_config


def getYamlPackageConfigurationSchemaFilename():
    """Get the filename of the schema for Nuitka package configuration."""
    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "misc",
        "nuitka-package-config-schema.json",
    )


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
