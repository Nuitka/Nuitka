#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Check and update Yaml checksum if possible."""

from nuitka.utils.FileOperations import getFileContents, putTextFileContents
from nuitka.utils.ModuleNames import checkModuleName
from nuitka.utils.Yaml import (
    PackageConfigYaml,
    checkSectionValues,
    getYamlDataHash,
    getYamllintPackage,
    parsePackageYaml,
    parseYaml,
    validateSchema,
)


def checkSchema(logger, document, effective_filename, assume_yes_for_downloads):
    """Check the schema of the Nuitka package configuration YAML file.

    Args:
        logger: logger to use
        document: original path of the YAML file
        effective_filename: filename to use for errors (user provided name)
        assume_yes_for_downloads: if tools should be downloaded automatically
    """
    yaml_data = parseYaml(
        logger=logger,
        data=getFileContents(document, mode="rb"),
        error_message="Error, malformed yaml in '%s'." % document,
    )

    validateSchema(
        logger=logger,
        name=effective_filename or document,
        data=yaml_data,
        assume_yes_for_downloads=assume_yes_for_downloads,
        reject_message="Checking YAML schema requires 'jsonschema'.",
    )

    logger.info("OK, schema validated.", style="blue")


module_allow_list = ("mozilla-ca",)


def checkYamlModuleName(logger, module_name):
    """Check if the module name is valid.

    Args:
        logger: logger to use
        module_name: module name to check

    Returns:
        bool: True if valid, False otherwise
    """
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
    """Check validness of values in the Nuitka package configuration YAML file.

    Mainly checks the module names and sections within the configuration.

    Args:
        logger: logger to use
        filename: path to the YAML file
    """
    yaml = PackageConfigYaml(
        logger=logger,
        name=filename,
        file_data=getFileContents(filename, mode="rb"),
        assume_yes_for_downloads=False,
        check_checksums=False,
    )

    result = True
    for module_name, config in yaml.items():
        if not checkYamlModuleName(logger, module_name):
            result = False

        for section, section_config in config.items():
            if not checkSectionValues(
                logger, filename, module_name, section, section_config
            ):
                result = False

    if result:
        logger.info("OK, manual value tests passed.", style="blue")
    else:
        logger.sysexit("Error, manual value checks are not clean.")


def checkYamllint(logger, document):
    """Run yamllint on the file.

    Args:
        logger: logger to use
        document: path to the YAML file
    """
    yamllint = getYamllintPackage(
        logger=logger,
        assume_yes_for_downloads=True,
        reject_message="Checking YAML requires 'yamllint'.",
    )

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
    """Check or update module checksums.

    Args:
        filename: path to the YAML file
        update: bool - if the checksums should be updated in the file
        logger: logger to use
    """
    yaml_file_text = getFileContents(filename, encoding="utf8")

    yaml_data = parsePackageYaml(
        logger=logger,
        package_name=None,
        filename=filename,
        assume_yes_for_downloads=False,
        check_checksums=False,
    )

    lines = []

    for line in yaml_file_text.splitlines():
        if line.startswith("- module-name:"):
            parts = line.split(":", 2)
            try:
                module_name = parts[1]
                module_name = module_name.split("#", 2)[0]
                module_name = module_name.strip()
                module_name = module_name.strip("'")
            except IndexError:
                logger.sysexit("Malformed line: %s" % line)

            yaml_module_data = yaml_data.data.get(module_name)
            try:
                checksum = getYamlDataHash(yaml_module_data)
            except BaseException as e:  # pylint: disable=broad-exception-caught
                logger.sysexit(
                    "Problem hashing module %s data %s gives %s"
                    % (module_name, yaml_module_data, e)
                )

            line = "- module-name: '%s' # checksum: %s" % (module_name, checksum)

        lines.append(line)

    if update:
        putTextFileContents(filename, lines, encoding="utf8")
        logger.info("OK, checksums updated.", style="blue")


def checkYamlSchema(logger, filename, effective_filename, update):
    """Check the YAML schema and values, and update checksums.

    This is the main entry point for YAML checking of package configs.

    Args:
        logger: logger to use
        filename: current path to the YAML file
        effective_filename: name to use for reports (e.g. repo path)
        update: if checksums should be updated in the file
    """
    logger.info("Checking '%s' for proper contents:" % effective_filename, style="blue")

    checkSchema(
        logger,
        filename,
        effective_filename=effective_filename,
        assume_yes_for_downloads=False,
    )
    checkValues(logger, filename)
    checkOrUpdateChecksum(filename=filename, update=update, logger=logger)
    checkYamllint(logger, filename)


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
