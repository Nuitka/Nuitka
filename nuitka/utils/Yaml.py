#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nuitka yaml utility functions.

Because we want to work with Python2.6 or higher, we play a few tricks with
what library to use for what Python. We have an 2 inline copy of PyYAML, one
that still does 2.6 and one for newer Pythons.

Also we put loading for specific packages in here and a few helpers to work
with these config files.
"""

# Otherwise "Yaml" and "yaml" collide on case insensitive setups
from __future__ import absolute_import

import ast
import os
import pkgutil
import re
from posixpath import normpath

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.options.Options import getUserProvidedYamlFiles
from nuitka.Tracing import general

from .FileOperations import getFileContents
from .Hashing import HashCRC32
from .Importing import importFromInlineCopy
from .ModuleNames import checkModuleName
from .PrivatePipSpace import getPrivatePackage


def _isParsable(value):
    """Check if a value is parsable python code."""
    try:
        ast.parse(value)
    except (SyntaxError, IndentationError):
        return False
    else:
        return True


def _isNormalizedPosixPath(path):
    """Check if a path is a normalized POSIX path."""
    if "\\" in path:
        return False

    return path == normpath(path)


def _checkNotEmptyString(logger, filename, module_name, section, k, value):
    """Check if a string value is not empty and log error if it is."""
    if value == "":
        logger.info(
            """\
%s: %s config value of %s %s cannot be empty."""
            % (filename, module_name, section, k),
            keep_format=True,
        )
        return False

    return True


def _checkParsable(logger, filename, module_name, section, k, value):
    """Check if a value is parsable python code and log error if not."""
    if not _checkNotEmptyString(logger, filename, module_name, section, k, value):
        return False

    if not _isParsable(value):
        logger.info(
            """\
%s: %s config value of '%s' '%s' contains invalid syntax in value '%s'"""
            % (filename, module_name, section, k, value),
            keep_format=True,
        )
        return False

    return True


def _checkRegexp(logger, filename, module_name, section, k, regexp, replacement):
    """Check if a regexp value is valid and log error if not."""
    if not _checkNotEmptyString(logger, filename, module_name, section, k, regexp):
        return False

    try:
        re.sub(regexp, replacement, "", re.S)
    except re.error as e:
        logger.info(
            """\
%s: %s config value of '%s' '%s' contains invalid regexp \
syntax in value '%s' leading to error '%s'"""
            % (filename, module_name, section, regexp, replacement, e),
            keep_format=True,
        )
        return False

    return True


def _checkNormalizedPosixPath(logger, filename, module_name, section, k, value):
    """Check if a value is a normalized POSIX path and log error if not."""
    if not _isNormalizedPosixPath(value):
        logger.info(
            """\
%s: module '%s' config value of '%s' '%s' should be normalized posix \
path, with '/' style slashes not '%s'."""
            % (filename, module_name, section, k, value),
            keep_format=True,
        )
        return False

    return True


def checkSectionValues(logger, filename, module_name, section, value):
    """Check values of the YAML file."""
    # many checks of course, pylint: disable=too-many-branches,too-many-statements

    result = True

    if type(value) is dict:
        for k, v in value.items():
            if k == "description" and v != v.strip():
                logger.info(
                    """\
%s: %s config value of %s %s should not contain trailing or leading spaces"""
                    % (filename, module_name, section, k),
                    keep_format=True,
                )
                result = False

            if k in ("when", "append_result"):
                if not _checkParsable(logger, filename, module_name, section, k, v):
                    result = False

            if k in ("replacements", "global_replacements"):
                for m, d in v.items():
                    if not _checkNotEmptyString(
                        logger, filename, module_name, section, k, m
                    ):
                        result = False
                    elif not _checkParsable(
                        logger, filename, module_name, section, k, d
                    ):
                        result = False

            if k in ("replacements_re", "global_replacements_re"):
                for m, d in v.items():
                    if not _checkRegexp(
                        logger, filename, module_name, section, k, m, d
                    ):
                        result = False

            if k == "replacements_plain":
                for m, d in v.items():
                    if not _checkNotEmptyString(
                        logger, filename, module_name, section, k, m
                    ):
                        result = False

            if k in ("dest_path", "relative_path") and not _checkNormalizedPosixPath(
                logger, filename, module_name, section, k, v
            ):
                result = False

            if k in ("dirs", "raw_dirs", "empty_dirs"):
                for e in v:
                    if not _checkNormalizedPosixPath(
                        logger, filename, module_name, section, k, e
                    ):
                        result = False

            if k == "parameters":
                for item in v:
                    if "values" in item:
                        if not _checkParsable(
                            logger, filename, module_name, section, k, item["values"]
                        ):
                            result = False

            if k == "no-auto-follow":
                for m, d in v.items():
                    if d == "":
                        logger.info(
                            """\
%s: %s config value of %s %s should not use empty value for %s, use 'ignore' \
if you want no message."""
                            % (filename, module_name, section, k, m),
                            keep_format=True,
                        )
                        result = False

            if k == "declarations":
                for m, d in v.items():
                    if not _checkNotEmptyString(
                        logger, filename, module_name, section, k, m
                    ):
                        result = False

                    if not _checkParsable(logger, filename, module_name, section, k, d):
                        result = False

            if k == "append_plain":
                if not _checkParsable(logger, filename, module_name, section, k, v):
                    result = False

            if k == "setup_code":
                if type(v) is list:
                    if not _checkParsable(
                        logger, filename, module_name, section, k, "\n".join(v)
                    ):
                        result = False
                elif not _checkParsable(logger, filename, module_name, section, k, v):
                    result = False

            if k == "environment":
                for m, d in v.items():
                    if not _checkParsable(logger, filename, module_name, section, k, d):
                        result = False

            if not checkSectionValues(logger, filename, module_name, section, v):
                result = False
    elif type(value) in (list, tuple):
        for item in value:
            if not checkSectionValues(logger, filename, module_name, section, item):
                result = False

    return result


def getJsonschemaPackage(logger, assume_yes_for_downloads, reject_message):
    """Get jsonschema package from private pip space or globally."""
    return getPrivatePackage(
        logger=logger,
        package_name="jsonschema",
        module_name="jsonschema",
        package_version=None,
        submodule_names=("validators",),
        assume_yes_for_downloads=assume_yes_for_downloads,
        reject_message=reject_message,
    )


def getRuamelYamlPackage(logger, assume_yes_for_downloads):
    """Get ruamel.yaml package from private pip space or globally."""
    return getPrivatePackage(
        logger=logger,
        package_name="ruamel.yaml",
        module_name="ruamel.yaml",
        package_version=None,
        submodule_names=None,
        assume_yes_for_downloads=assume_yes_for_downloads,
        reject_message="Autoformat YAML needs ruamel.yaml.",
    )


def getYamllintPackage(logger, assume_yes_for_downloads, reject_message):
    """Get yamllint package from private pip space or globally."""
    return getPrivatePackage(
        logger=logger,
        package_name="yamllint",
        module_name="yamllint",
        package_version=None,
        submodule_names=("cli",),
        assume_yes_for_downloads=assume_yes_for_downloads,
        reject_message=reject_message,
    )


def getDeepDiffPackage(logger, assume_yes_for_downloads):
    """Get deepdiff package from private pip space or globally."""
    return getPrivatePackage(
        logger=logger,
        package_name="deepdiff",
        module_name="deepdiff",
        package_version=None,
        submodule_names=("diff",),
        assume_yes_for_downloads=assume_yes_for_downloads,
        reject_message="Autoformat YAML needs deepdiff.",
    )


def checkDataChecksums(file_data, data):
    # Checksum is valid, if the file contains a line with the checksum of the
    # file content without that line.

    result = []

    # We are parsing the file manually here, which is not great, but strict
    # enough for the auto-formatted files we have.
    for line in file_data.decode("utf8").splitlines():
        if not line.startswith("- module-name:"):
            continue

        parts = line.split(":", 2)

        module_name = parts[1]
        module_name = module_name.split("#", 2)[0]
        module_name = module_name.strip()
        module_name = module_name.strip("'")

        if "# checksum: " not in line:
            result.append(module_name)
            continue

        expected_checksum = line.split("# checksum: ")[1].strip()

        yaml_module_data = data.get(module_name)

        if getYamlDataHash(yaml_module_data) != expected_checksum:
            result.append(module_name)
            continue

    return result


def validateSchema(logger, name, data, assume_yes_for_downloads, reject_message):
    if not getJsonschemaPackage(
        logger,
        assume_yes_for_downloads=assume_yes_for_downloads,
        reject_message=reject_message,
    ):
        logger.warning("Cannot validate schema due to lack of 'jsonschema' package.")
        return

    # pylint: disable=I0021,import-error
    from jsonschema import validators

    schema_filename = getYamlPackageConfigurationSchemaFilename()

    if not os.path.exists(schema_filename):
        logger.sysexit("Cannot validate schema due to missing schema file.")

    import json

    schema = json.loads(getFileContents(schema_filename))

    validator = validators.Draft202012Validator(schema=schema)

    error_messages = []

    for error in validator.iter_errors(instance=data):
        try:
            module_name = repr(data[error.path[0]]["module-name"])
        except Exception:  # pylint: disable=broad-except
            module_name = "some"

        error_messages.append("For %s module: %s" % (module_name, error.message))

    if error_messages:
        logger.sysexit(
            "Error, invalid package configuration in '%s':\n%s"
            % (name, "\n".join(error_messages))
        )


class PackageConfigYaml(object):
    __slots__ = (
        "name",
        "data",
        "logger",
        "checked_sections",
    )

    def __init__(
        self, logger, name, file_data, assume_yes_for_downloads, check_checksums
    ):
        self.logger = logger
        self.name = name

        assert type(file_data) is bytes
        data = parseYaml(
            logger=logger,
            data=file_data,
            error_message="""\
Error, empty (or malformed?) user package configuration '%s' used."""
            % name,
        )

        assert type(data) is list, type(data)

        self._init(logger, data)

        if check_checksums:
            bad_checksum_modules = checkDataChecksums(file_data, self.data)

            if bad_checksum_modules:
                logger.info(
                    "Detected %d module(s) with mismatching checksum in '%s': %s"
                    % (len(bad_checksum_modules), name, ",".join(bad_checksum_modules))
                )

                validateSchema(
                    logger=logger,
                    name=name,
                    data=data,
                    assume_yes_for_downloads=assume_yes_for_downloads,
                    reject_message=None,
                )

    def _init(self, logger, data):
        self.data = OrderedDict()

        for item in data:
            module_name = item.get("module-name")

            if not module_name:
                return logger.sysexit(
                    "Error, invalid config in '%s' looks like an empty module name was given."
                    % (self.name)
                )

            if "/" in module_name:
                return logger.sysexit(
                    "Error, invalid module name in '%s' looks like a file path '%s'."
                    % (self.name, module_name)
                )

            if not checkModuleName(module_name):
                return logger.sysexit(
                    "Error, invalid module name in '%s' not valid '%s'."
                    % (self.name, module_name)
                )

            if module_name in self.data:
                return logger.sysexit(
                    "Duplicate module name '%s' encountered." % module_name
                )

            # Do not replicate module name in data.
            self.data[module_name] = item.copy()
            del self.data[module_name]["module-name"]

        self.checked_sections = set()

    def __repr__(self):
        return "<PackageConfigYaml %s>" % self.name

    def get(self, name, section):
        """Return a configs for that section."""
        result = self.data.get(name)

        if result is not None:
            result = result.get(section, ())
        else:
            result = ()

        if section in ("options", "variables") and type(result) in (dict, OrderedDict):
            result = (result,)

        if type(result) is list:
            result = tuple(result)

        # Ensure result is a tuple; otherwise exit with an error
        if not isinstance(result, tuple):
            self.logger.sysexit(
                "Error, unexpected result type %s for %s module %s section %s."
                % (type(result), self.name, name, section)
            )

        if result and (name, section) not in self.checked_sections:
            checkSectionValues(self.logger, self.name, name, section, result)
            self.checked_sections.add((name, section))

        return result

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def update(self, other):
        # TODO: Full blown merging, including respecting an overload flag, where
        # a config replaces another one entirely, for now we expect to not
        # overlap and offer only merging of implicit-imports.
        for key, value in other.items():
            # assert key not in self.data, key
            if key in self.data:
                new_implicit_imports = value.get("implicit-imports", None)
                if new_implicit_imports:
                    value.pop("implicit-imports")
                    if self.data[key].get("implicit-imports", None) is None:
                        self.data[key]["implicit-imports"] = new_implicit_imports
                    else:
                        self.data[key]["implicit-imports"].extend(new_implicit_imports)
                if len(value) > 0:
                    general.sysexit(
                        "Error, duplicate config for module name '%s' encountered in '%s'."
                        % (key, self.name)
                    )
                else:
                    general.info("Merged implicit-imports for '%s'." % key)
            else:
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


def parseYaml(logger, data, error_message):
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

    result = yaml.load(data, OrderedLoader)

    if not result:
        return logger.sysexit(error_message)

    return result


_yaml_cache = {}


def getYamlDataHash(data):
    result = HashCRC32()
    result.updateFromValues(data)

    return result.asHexDigest()


def parsePackageYaml(
    logger, package_name, filename, assume_yes_for_downloads, check_checksums
):
    key = package_name, filename

    if key not in _yaml_cache:
        if package_name is None:
            file_data = getFileContents(filename, mode="rb")
        else:
            file_data = pkgutil.get_data(package_name, filename)

        if file_data is None:
            raise IOError("Cannot find %s.%s" % (package_name, filename))

        _yaml_cache[key] = PackageConfigYaml(
            logger=logger,
            name=filename,
            file_data=file_data,
            assume_yes_for_downloads=assume_yes_for_downloads,
            check_checksums=check_checksums,
        )

    return _yaml_cache[key]


_package_config = None


def getYamlPackageConfiguration(logger, assume_yes_for_downloads, check_checksums):
    """Get Nuitka package configuration. Merged from multiple sources."""
    # Singleton, pylint: disable=global-statement
    global _package_config

    if logger is None:
        logger = general

    if _package_config is None:
        _package_config = parsePackageYaml(
            logger=logger,
            package_name="nuitka.plugins.standard",
            filename="standard.nuitka-package.config.yml",
            assume_yes_for_downloads=assume_yes_for_downloads,
            check_checksums=check_checksums,
        )
        _package_config.update(
            parsePackageYaml(
                logger=logger,
                package_name="nuitka.plugins.standard",
                filename="stdlib2.nuitka-package.config.yml",
                assume_yes_for_downloads=assume_yes_for_downloads,
                check_checksums=check_checksums,
            )
        )
        _package_config.update(
            parsePackageYaml(
                logger=logger,
                package_name="nuitka.plugins.standard",
                filename="stdlib3.nuitka-package.config.yml",
                assume_yes_for_downloads=assume_yes_for_downloads,
                check_checksums=check_checksums,
            )
        )

        try:
            _package_config.update(
                parsePackageYaml(
                    logger=logger,
                    package_name="nuitka.plugins.commercial",
                    filename="commercial.nuitka-package.config.yml",
                    assume_yes_for_downloads=assume_yes_for_downloads,
                    check_checksums=check_checksums,
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
                    logger=logger,
                    name=user_yaml_filename,
                    file_data=getFileContents(user_yaml_filename, mode="rb"),
                    assume_yes_for_downloads=assume_yes_for_downloads,
                    check_checksums=check_checksums,
                )
            )

    return _package_config


def getYamlPackageConfigurationSchemaFilename():
    """Get the filename of the schema for Nuitka package configuration."""
    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "package_config",
        "nuitka-package-config-schema.json",
    )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
