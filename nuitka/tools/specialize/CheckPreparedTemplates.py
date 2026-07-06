#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Check prepared code templates against legacy '%' formatting."""

import sys

from nuitka.code_generation.templates.CodeTemplatesGenerated import (
    template_infos,
    template_variables,
)
from nuitka.code_generation.templates.TemplateDebugWrapper import emitTemplate
from nuitka.code_generation.Emission import SourceCodeCollector
from nuitka.code_generation.Indentation import indented
from nuitka.States import states


def _importTemplate(template_key):
    module_name, template_name = template_key.rsplit(".", 1)
    module = __import__(module_name, fromlist=[template_name])

    return getattr(module, template_name)


def _makeTemplateValues(template_key):
    value_types = {}

    for variable_name, conversion in template_variables[template_key]:
        if conversion == "d" or value_types.get(variable_name) == "d":
            value_types[variable_name] = "d"
        else:
            value_types[variable_name] = "s"

    result = {}

    for variable_name, conversion in value_types.items():
        if conversion == "d":
            result[variable_name] = 123
        else:
            result[variable_name] = "VALUE_%s" % variable_name

    return result


def iterPreparedTemplateChecks():
    for template_key in sorted(template_infos):
        template = _importTemplate(template_key)
        values = _makeTemplateValues(template_key)

        yield template_key, template, values


def checkPreparedTemplates():
    old_readable_code = states.is_readable_code
    checked = 0

    try:
        states.is_readable_code = True

        for template_key, template, values in iterPreparedTemplateChecks():
            if not hasattr(template, "emit"):
                sys.stderr.write("Template is not prepared: %s\n" % template_key)
                return False

            legacy_result = str(template) % values

            emitted = []
            template.emit(emitted.append, values)
            prepared_result = "".join(emitted)

            if legacy_result != prepared_result:
                sys.stderr.write("Template parity mismatch: %s\n" % template_key)
                sys.stderr.write("Legacy result:\n%s\n" % legacy_result)
                sys.stderr.write("Prepared result:\n%s\n" % prepared_result)

                return False

            collector = SourceCodeCollector()
            emitTemplate(template, collector, values)
            collector_result = indented(collector)

            if legacy_result != collector_result:
                sys.stderr.write(
                    "Template collector parity mismatch: %s\n" % template_key
                )
                sys.stderr.write("Legacy result:\n%s\n" % legacy_result)
                sys.stderr.write("Collector result:\n%s\n" % collector_result)

                return False

            states.is_readable_code = False
            collector = SourceCodeCollector()
            emitTemplate(template, collector, values)
            indented(collector)
            states.is_readable_code = True

            checked += 1
    finally:
        states.is_readable_code = old_readable_code

    sys.stdout.write(
        "Validated %d prepared templates: legacy '%%' rendering matches prepared emission.\n"
        % checked
    )

    return True


def main():
    if checkPreparedTemplates():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()


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
