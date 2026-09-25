#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


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

from nuitka.__past__ import re_sub, unicode
from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.options.Options import getMainModuleName, getUserProvidedYamlFiles
from nuitka.Tracing import general

from .FileOperations import getFileContents
from .Hashing import HashCRC32
from .Importing import importFromInlineCopy
from .ModuleNames import checkModuleName
from .PrivatePipSpace import getPrivatePackage, getRequiredVersion

# Pseudo module name for configuration that applies to the main module being
# compiled. It is merged into the configuration of the actual main module.
_main_module_config_name = "<main>"


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
%s: %s config value of %s %s cannot be empty.""" % (filename, module_name, section, k),
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
        _unused = re_sub(regexp, replacement, "", flags=re.S)
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
path, with '/' style slashes not '%s'.""" % (filename, module_name, section, k, value),
            keep_format=True,
        )
        return False

    return True


def _checkRelativePosixPath(logger, filename, module_name, section, k, value):
    """Check if a value is a relative POSIX path and log error if not."""
    if not _checkNormalizedPosixPath(logger, filename, module_name, section, k, value):
        return False

    if value.startswith("/"):
        logger.info(
            """\
%s: module '%s' config value of '%s' '%s' should be a relative posix \
path, not an absolute path, not '%s'.""" % (filename, module_name, section, k, value),
            keep_format=True,
        )
        return False

    if ".." in value.split("/"):
        logger.info(
            """\
%s: module '%s' config value of '%s' '%s' should be a relative posix \
path, without '..' paths, not '%s'.""" % (filename, module_name, section, k, value),
            keep_format=True,
        )
        return False

    if ":" in value:
        logger.info(
            """\
%s: module '%s' config value of '%s' '%s' should be a relative posix \
path, without drive letters, not '%s'.""" % (filename, module_name, section, k, value),
            keep_format=True,
        )
        return False

    return True


def checkSectionValues(logger, filename, module_name, section, value):
    """Check values of the YAML file."""
    # many checks of course, pylint: disable=too-many-branches,too-many-statements

    result = True

    if type(value) in (dict, OrderedDict):
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

            if k == "dest_path" and not _checkNormalizedPosixPath(
                logger, filename, module_name, section, k, v
            ):
                result = False

            if k == "relative_path" and not _checkRelativePosixPath(
                logger, filename, module_name, section, k, v
            ):
                result = False

            if k == "relative_to":
                if not checkModuleName(v):
                    logger.info(
                        """\
%s: module '%s' config value of '%s' '%s' should be a valid module name, not '%s'."""
                        % (filename, module_name, section, k, v),
                        keep_format=True,
                    )
                    result = False
                elif v == module_name:
                    logger.info(
                        """\
%s: module '%s' config value of '%s' '%s' should not be the module name itself, s that's the default, not '%s'."""
                        % (filename, module_name, section, k, v),
                        keep_format=True,
                    )
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
if you want no message.""" % (filename, module_name, section, k, m),
                            keep_format=True,
                        )
                        result = False

            if k == "limit-auto-follow":
                for item in v:
                    if not _checkNotEmptyString(
                        logger, filename, module_name, section, k, item
                    ):
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
        package_version=getRequiredVersion(logger, "jsonschema"),
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
        package_version=getRequiredVersion(logger, "ruamel.yaml"),
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
        package_version=getRequiredVersion(logger, "yamllint"),
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
        package_version=getRequiredVersion(logger, "deepdiff"),
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
        module_name = module_name.strip("'\"")

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
        return logger.sysexit("Cannot validate schema due to missing schema file.")

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
        return logger.sysexit(
            "Error, invalid package configuration in '%s':\n%s"
            % (name, "\n".join(error_messages))
        )


def _parseIncludeConfigPath(logger, module_name, config_path):
    """Parse an 'include-config' path of the form 'module-name/section-name'."""
    if type(config_path) not in (str, unicode):
        return logger.sysexit(
            """\
Error, 'include-config' path of module '%s' must be a string, not '%s'."""
            % (module_name, config_path)
        )

    path_module_name, _sep, path_section_name = config_path.partition("/")

    if not path_module_name or not path_section_name or "/" in path_section_name:
        return logger.sysexit(
            """\
Error, 'include-config' path '%s' of module '%s' must have the form 'module-name/section-name'."""
            % (config_path, module_name)
        )

    return path_module_name, path_section_name


def _parseIncludeConfigEntry(logger, module_name, include):
    """Parse an 'include-config' entry, a path string or a description dict."""
    if type(include) in (str, unicode):
        return include, None, {}, None

    if type(include) not in (dict, OrderedDict):
        return logger.sysexit(
            """\
Error, 'include-config' entries of module '%s' must be strings or dicts, not '%s'."""
            % (module_name, include)
        )

    return _parseIncludeConfigDictEntry(
        logger=logger, module_name=module_name, include=include
    )


def _checkIncludeConfigKeys(logger, module_name, include):
    """Check the keys of an 'include-config' entry description dict."""
    invalid_keys = sorted(
        key for key in include if key not in ("from", "to", "key-map", "when")
    )

    if invalid_keys:
        return logger.sysexit(
            """\
Error, unknown 'include-config' key(s) '%s' of module '%s'."""
            % (", ".join(invalid_keys), module_name)
        )

    if "from" not in include:
        return logger.sysexit(
            """\
Error, 'include-config' entry of module '%s' is missing the 'from' key.""" % module_name
        )

    return True


def _parseIncludeConfigDictEntry(logger, module_name, include):
    """Parse an 'include-config' entry given as a description dict."""
    if not _checkIncludeConfigKeys(
        logger=logger, module_name=module_name, include=include
    ):
        return None

    result_to = include.get("to")

    if result_to is not None and (
        type(result_to) not in (str, unicode) or not result_to
    ):
        return logger.sysexit(
            """\
Error, 'include-config' key 'to' of module '%s' must be a non-empty string, not '%s'."""
            % (module_name, result_to)
        )

    result_key_map = include.get("key-map", {})

    if type(result_key_map) not in (dict, OrderedDict):
        return logger.sysexit(
            """\
Error, 'include-config' key 'key-map' of module '%s' must be a dict, not '%s'."""
            % (module_name, result_key_map)
        )

    for key_map_key, key_map_value in result_key_map.items():
        if (
            type(key_map_key) not in (str, unicode)
            or type(key_map_value) not in (str, unicode)
            or not key_map_key
            or not key_map_value
        ):
            return logger.sysexit(
                """\
Error, 'include-config' key 'key-map' of module '%s' must map non-empty strings to non-empty strings, not '%s' to '%s'."""
                % (module_name, key_map_key, key_map_value)
            )

    result_when = include.get("when")

    if result_when is not None and type(result_when) not in (str, unicode):
        return logger.sysexit(
            """\
Error, 'include-config' key 'when' of module '%s' must be a string, not '%s'."""
            % (module_name, result_when)
        )

    return include["from"], result_to, result_key_map, result_when


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
Error, empty (or malformed?) user package configuration '%s' used.""" % name,
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

    def _applyMainModuleConfig(self):
        """Merge the '<main>' configuration into the actual main module config."""
        main_config = self.data.get(_main_module_config_name)

        if main_config is None:
            return

        main_module_name = getMainModuleName()

        if main_module_name is None or main_module_name == _main_module_config_name:
            return

        main_module_config = self.data.setdefault(main_module_name, OrderedDict())

        for section, section_config in main_config.items():
            if type(section_config) is not list:
                return self.logger.sysexit(
                    """\
Error, '<main>' configuration section '%s' must be list shaped to be applied to the main module."""
                    % section
                )

            destination_config = main_module_config.setdefault(section, [])

            if type(destination_config) is not list:
                return self.logger.sysexit(
                    """\
Error, '<main>' configuration section '%s' cannot be applied to non-list section of the main module."""
                    % section
                )

            for main_entry in section_config:
                if type(main_entry) in (dict, OrderedDict):
                    main_entry = OrderedDict(main_entry)

                destination_config.append(main_entry)

    def _resolveModuleIncludes(self, module_name, resolution_chain):
        module_config = self.data.get(module_name)

        if module_config is None:
            return self.logger.sysexit(
                "Error, 'include-config' references unknown module '%s'." % module_name
            )

        include_config = module_config.pop("include-config", None)

        if not include_config:
            return

        if type(include_config) in (str, unicode):
            include_config = (include_config,)

        for include in include_config:
            self._resolveModuleInclude(
                module_name=module_name,
                module_config=module_config,
                include=include,
                resolution_chain=resolution_chain,
            )

    def _resolveModuleInclude(
        self, module_name, module_config, include, resolution_chain
    ):
        from_path, to_section, key_map, include_when = _parseIncludeConfigEntry(
            logger=self.logger, module_name=module_name, include=include
        )

        target_module_name, target_section = _parseIncludeConfigPath(
            logger=self.logger, module_name=module_name, config_path=from_path
        )

        target_section_config = self._getIncludedConfig(
            module_name=module_name,
            target_module_name=target_module_name,
            target_section=target_section,
            resolution_chain=resolution_chain,
        )

        destination_config = self._getIncludeDestination(
            module_name=module_name,
            module_config=module_config,
            target_section=target_section,
            to_section=to_section,
        )

        self._copyIncludedConfig(
            module_name=module_name,
            destination_config=destination_config,
            target_section_config=target_section_config,
            key_map=key_map,
            include_when=include_when,
        )

    def _getIncludedConfig(
        self, module_name, target_module_name, target_section, resolution_chain
    ):
        if target_module_name == module_name or target_module_name in resolution_chain:
            return self.logger.sysexit(
                """\
Error, 'include-config' cycle detected with module '%s' including module '%s'."""
                % (module_name, target_module_name)
            )

        if target_section == "include-config":
            return self.logger.sysexit(
                """\
Error, 'include-config' of module '%s' cannot include the 'include-config' of module '%s'."""
                % (module_name, target_module_name)
            )

        if target_module_name not in self.data:
            return self.logger.sysexit(
                """\
Error, 'include-config' of module '%s' references unknown module '%s'."""
                % (module_name, target_module_name)
            )

        # Resolve what the included module itself includes first.
        self._resolveModuleIncludes(
            module_name=target_module_name,
            resolution_chain=resolution_chain + (module_name,),
        )

        target_section_config = self.data[target_module_name].get(target_section)

        if target_section_config is None:
            return self.logger.sysexit(
                """\
Error, 'include-config' of module '%s' references missing section '%s' of module '%s'."""
                % (module_name, target_section, target_module_name)
            )

        if type(target_section_config) is not list:
            return self.logger.sysexit(
                """\
Error, 'include-config' of module '%s' can only include list shaped sections, but section '%s' of module '%s' is not."""
                % (module_name, target_section, target_module_name)
            )

        return target_section_config

    def _getIncludeDestination(
        self, module_name, module_config, target_section, to_section
    ):
        if to_section is None:
            destination_section = target_section
        elif to_section == "include-config":
            return self.logger.sysexit(
                """\
Error, 'include-config' of module '%s' cannot include into the 'include-config' section."""
                % module_name
            )
        else:
            destination_section = to_section

        destination_config = module_config.setdefault(destination_section, [])

        if type(destination_config) is not list:
            return self.logger.sysexit(
                """\
Error, 'include-config' of module '%s' cannot include into non-list section '%s'."""
                % (module_name, destination_section)
            )

        return destination_config

    def _copyIncludedConfig(
        self,
        module_name,
        destination_config,
        target_section_config,
        key_map,
        include_when,
    ):
        for target_entry in target_section_config:
            if type(target_entry) in (dict, OrderedDict):
                target_entry = OrderedDict(target_entry)

                self._mapIncludedEntry(
                    target_entry=target_entry,
                    key_map=key_map,
                    include_when=include_when,
                )
            elif include_when is not None or key_map:
                return self.logger.sysexit(
                    """\
Error, 'include-config' of module '%s' cannot use 'when' or 'key-map' with non-dict entry '%s'."""
                    % (module_name, target_entry)
                )

            destination_config.append(target_entry)

    @staticmethod
    def _mapIncludedEntry(target_entry, key_map, include_when):
        for key_map_key, key_map_value in key_map.items():
            if key_map_key in target_entry:
                target_entry[key_map_value] = target_entry.pop(key_map_key)

        if include_when is not None:
            entry_when = target_entry.get("when")

            if entry_when is None:
                target_entry["when"] = include_when
            else:
                target_entry["when"] = "(%s) and (%s)" % (include_when, entry_when)

    def get(self, name, section):
        """Return a configs for that section."""
        result = self.data.get(name)

        if result is not None:
            result = result.get(section, ())
        else:
            result = ()

        if section in (
            "options",
            "variables",
            "constants",
        ) and type(
            result
        ) in (dict, OrderedDict):
            result = (result,)

        if type(result) is list:
            result = tuple(result)

        # Ensure result is a tuple; otherwise exit with an error
        if not isinstance(result, tuple):
            return self.logger.sysexit(
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

    @staticmethod
    def _mergeConfigSection(existing, new_value, section):
        new_entries = new_value.pop(section, None)

        if new_entries:
            if existing.get(section, None) is None:
                existing[section] = new_entries
            else:
                existing[section].extend(new_entries)

    def update(self, other):
        # TODO: Full blown merging, including respecting an overload flag, where
        # a config replaces another one entirely, for now we expect to not
        # overlap and offer only merging of implicit-imports and include-config.
        for key, value in other.items():
            # assert key not in self.data, key
            if key in self.data:
                self._mergeConfigSection(
                    existing=self.data[key],
                    new_value=value,
                    section="implicit-imports",
                )
                self._mergeConfigSection(
                    existing=self.data[key],
                    new_value=value,
                    section="include-config",
                )
                if len(value) > 0:
                    return general.sysexit(
                        "Error, duplicate config for module name '%s' encountered in '%s'."
                        % (key, self.name)
                    )
                else:
                    general.info("Merged configuration for '%s'." % key)
            else:
                self.data[key] = value

    @classmethod
    def getYamlPackageConfiguration(
        cls, logger, assume_yes_for_downloads, check_checksums
    ):
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

            # Resolve 'include-config' references only now, since they may refer to
            # modules configured in any of the loaded files.
            for module_name in list(_package_config.data):
                cls._resolveModuleIncludes(
                    _package_config,
                    module_name=module_name,
                    resolution_chain=(),
                )

            cls._applyMainModuleConfig(_package_config)

        return _package_config


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
    return PackageConfigYaml.getYamlPackageConfiguration(
        logger=logger,
        assume_yes_for_downloads=assume_yes_for_downloads,
        check_checksums=check_checksums,
    )


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
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
