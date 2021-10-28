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
""" Jinja folklore wrappers and handling of inline copy usage.

"""

from .Importing import importFromInlineCopy

environments = {}


def unlikely_if(value):
    if value:
        return "unlikely"
    else:
        return ""


def unlikely_or_likely_from(value):
    if value:
        return "unlikely"
    else:
        return "likely"


def getEnvironment(package_name, template_subdir, extensions):
    key = package_name, template_subdir, extensions

    if key not in environments:
        # Import dependencies, sadly we get to manage this ourselves.
        importFromInlineCopy("markupsafe", must_exist=True)

        jinja2 = importFromInlineCopy("jinja2", must_exist=True)
        import jinja2

        env = jinja2.Environment(
            loader=jinja2.PackageLoader(package_name, template_subdir),
            extensions=extensions,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # For shared global functions.
        env.globals.update(
            {
                "unlikely_if": unlikely_if,
                "unlikely_or_likely_from": unlikely_or_likely_from,
            }
        )

        env.undefined = jinja2.StrictUndefined

        environments[key] = env

    return environments[key]


def getTemplate(
    package_name, template_name, template_subdir="templates", extensions=()
):
    return getEnvironment(
        package_name=package_name,
        template_subdir=template_subdir,
        extensions=extensions,
    ).get_template(template_name)
