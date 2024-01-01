#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Check and update Yaml checksum if possible."""

from nuitka.utils.FileOperations import (
    getFileContents,
    openTextFile,
    putTextFileContents,
)
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


def _checkValues(logger, filename, module_name, section, value):
    if type(value) is dict:
        for k, v in value.items():
            if k == "description" and v != v.strip():
                logger.info(
                    "%s: %s config value of %s %s should not contain trailing or leading spaces"
                    % (filename, module_name, section, k)
                )

            _checkValues(logger, filename, module_name, section, v)
    elif type(value) in (list, tuple):
        for item in value:
            _checkValues(logger, filename, module_name, section, item)


def checkValues(logger, filename):
    yaml = PackageConfigYaml(
        name=filename,
        file_data=getFileContents(filename, mode="rb"),
    )

    for module_name, config in yaml.items():
        for section, section_config in config.items():
            _checkValues(logger, filename, module_name, section, section_config)

    logger.info("OK, manual value tests passed.", style="blue")


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
