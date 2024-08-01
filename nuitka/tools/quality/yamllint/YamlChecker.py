#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Check and update Yaml checksum if possible."""

import ast
from posixpath import normpath

from nuitka.utils.FileOperations import (
    getFileContents,
    openTextFile,
    putTextFileContents,
)
from nuitka.utils.ModuleNames import checkModuleName
from nuitka.utils.Yaml import (
    PackageConfigYaml,
    getYamlDataHash,
    getYamlPackage,
    getYamlPackageConfigurationSchemaFilename,
    parsePackageYaml,
)


def checkSchema(logger, document):
    import json  # pylint: disable=I0021,import-error

    from jsonschema import validators  # pylint: disable=I0021,import-error
    from jsonschema.exceptions import ValidationError

    yaml = getYamlPackage()

    with openTextFile(getYamlPackageConfigurationSchemaFilename(), "r") as schema_file:
        with openTextFile(document, "r") as yaml_file:
            yaml_data = yaml.load(yaml_file, yaml.BaseLoader)

            try:
                validators.Draft202012Validator(
                    schema=json.loads(schema_file.read())
                ).validate(instance=yaml_data)
            except ValidationError as e:
                try:
                    module_name = repr(yaml_data[e.path[0]]["module-name"])
                except Exception:  # pylint: disable=broad-except
                    module_name = "unknown"

                logger.sysexit(
                    "Error, please fix the schema error in yaml file '%s' for %s module:\n%s"
                    % (document, module_name, e.message)
                )
            else:
                logger.info("OK, schema validated.", style="blue")


def _isParsable(value):
    try:
        ast.parse(value)
    except (SyntaxError, IndentationError):
        return False
    else:
        return True


def _isNormalizedPosixPath(path):
    if "\\" in path:
        return False

    return path == normpath(path)


def _checkValues(logger, filename, module_name, section, value):
    # many checks of course, pylint: disable=too-many-branches

    result = True

    if type(value) is dict:
        for k, v in value.items():
            if k == "description" and v != v.strip():
                logger.info(
                    """\
%s: %s config value of %s %s should not contain trailing or leading spaces"""
                    % (filename, module_name, section, k)
                )
                result = False

            if k in ("when", "append_result"):
                if not _isParsable(v):
                    logger.info(
                        """\
%s: %s config value of '%s' '%s' contains invalid syntax in value '%s'"""
                        % (filename, module_name, section, k, v),
                        keep_format=True,
                    )
                    result = False

            if k == "replacements":
                for m, d in v.items():
                    if m == "":
                        logger.info(
                            """\
%s: %s config value of %s %s cannot be empty."""
                            % (filename, module_name, section, k)
                        )
                        result = False
                    elif not _isParsable(d):
                        logger.info(
                            """\
%s: %s config value of '%s' '%s' contains invalid syntax in value '%s'"""
                            % (filename, module_name, section, k, v),
                            keep_format=True,
                        )
                        result = False

            if k == "replacements_plain":
                for m, d in v.items():
                    if m == "":
                        logger.info(
                            """\
%s: %s config value of %s %s cannot be empty."""
                            % (filename, module_name, section, k)
                        )
                        result = False

            if k in ("dest_path", "relative_path") and not _isNormalizedPosixPath(v):
                logger.info(
                    """\
%s: module '%s' config value of '%s' '%s' should be normalized posix \
path, with '/' style slashes not '%s'."""
                    % (filename, module_name, section, k, v)
                )
                result = False

            if k in ("dirs", "raw_dirs", "empty_dirs"):
                for e in v:
                    if not _isNormalizedPosixPath(e):
                        logger.info(
                            """\
%s: module '%s' config values of '%s' '%s' should be normalized posix \
path, with '/' style slashes not '%s'."""
                            % (filename, module_name, section, k, e)
                        )
                        result = False

            if k == "no-auto-follow":
                for m, d in v.items():
                    if d == "":
                        logger.info(
                            """\
%s: %s config value of %s %s should not use empty value for %s, use 'ignore' \
if you want no message."""
                            % (filename, module_name, section, k, m)
                        )
                        result = False

            if k == "declarations":
                for m, d in v.items():
                    if m == "":
                        logger.info(
                            """\
%s: %s config value of %s %s should not use empty value for declaration name."""
                            % (filename, module_name, section, k)
                        )
                        result = False

                    if d == "":
                        logger.info(
                            """\
%s: %s config value of %s %s should not use empty value for declaration name."""
                            % (filename, module_name, section, k)
                        )
                        result = False
                    elif not _isParsable(d):
                        logger.info(
                            """\
%s: %s config value of '%s' '%s' contains invalid syntax in value '%s'"""
                            % (filename, module_name, section, k, v),
                            keep_format=True,
                        )
                        result = False

            if not _checkValues(logger, filename, module_name, section, v):
                result = False
    elif type(value) in (list, tuple):
        for item in value:
            if not _checkValues(logger, filename, module_name, section, item):
                result = False

    return result


module_allow_list = ("mozilla-ca",)


def checkYamlModuleName(logger, module_name):
    if module_name in module_allow_list:
        return True

    result = True

    if module_name == "" or not checkModuleName(module_name):
        logger.info(
            "Config for module '%s' is for an invalid module name." % module_name
        )
        result = False
    elif "-" in module_name:
        logger.info(
            "Config for module '%s' is using a package name rather than a module name."
            % module_name
        )
        result = False

    return result


def checkValues(logger, filename):
    yaml = PackageConfigYaml(
        name=filename,
        file_data=getFileContents(filename, mode="rb"),
    )

    result = True
    for module_name, config in yaml.items():
        if not checkYamlModuleName(logger, module_name):
            result = False

        for section, section_config in config.items():
            if not _checkValues(logger, filename, module_name, section, section_config):
                result = False

    if result:
        logger.info("OK, manual value tests passed.", style="blue")
    else:
        logger.sysexit("Error, manual value checks are not clean.")


def checkYamllint(logger, document):
    import yamllint.cli  # pylint: disable=I0021,import-error

    try:
        yamllint.cli.run(["--strict", document])
    except SystemExit as e:
        lint_result = e.code

        if lint_result != 0:
            logger.sysexit("Error, not lint clean yaml.")
    else:
        logger.sysexit("Error, yamllint didn't raise expected SystemExit exception.")

    logger.info("OK, yamllint passed.", style="blue")


def checkOrUpdateChecksum(filename, update, logger):
    yaml_file_text = getFileContents(filename, encoding="utf8")

    yaml_data = parsePackageYaml(package_name=None, filename=filename)

    lines = []

    for line in yaml_file_text.splitlines():
        if line.startswith("- module-name:"):
            parts = line.split("'", 2)
            module_name = parts[1]

            checksum = getYamlDataHash(yaml_data.data.get(module_name))

            line = "- module-name: '%s' # checksum: %s" % (module_name, checksum)

        lines.append(line)

    if update:
        putTextFileContents(filename, lines, encoding="utf8")
        logger.info("OK, checksums updated.", style="blue")


def checkYamlSchema(logger, filename, effective_filename, update):
    logger.info("Checking '%s' for proper contents:" % effective_filename, style="blue")

    checkSchema(logger, filename)
    checkValues(logger, filename)
    checkOrUpdateChecksum(filename=filename, update=update, logger=logger)
    checkYamllint(logger, filename)


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
