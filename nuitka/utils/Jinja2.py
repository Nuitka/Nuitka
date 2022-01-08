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

import sys

from nuitka.__past__ import unicode

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


_jinja2 = None

# For pkg resources, we need to keep a reference, after we delete it from
# "sys.modules" again.

_loaded_pkg_resources = None


def getJinja2Package():
    global _jinja2, _loaded_pkg_resources  # singleton package using a cache, pylint: disable=global-statement

    # Import dependencies, sadly we get to manage this ourselves.
    importFromInlineCopy("markupsafe", must_exist=True)

    # Newer Jinja2 may not use it, but we load it and remove it, so it
    # does not interfere with anything else.
    if "pkg_resources" not in sys.modules:
        _loaded_pkg_resources = importFromInlineCopy("pkg_resources", must_exist=False)

    _jinja2 = importFromInlineCopy("jinja2", must_exist=True)

    # Unload if it was us loading it, as the inline copy is incomplete.
    if _loaded_pkg_resources is not None:
        del sys.modules["pkg_resources"]

    return _jinja2


def getEnvironment(package_name, template_subdir, extensions):
    key = package_name, template_subdir, extensions

    if key not in environments:
        jinja2 = getJinja2Package()

        if package_name is not None:
            loader = jinja2.PackageLoader(package_name, template_subdir)
        elif template_subdir is not None:
            loader = jinja2.FileSystemLoader(template_subdir)
        else:
            loader = jinja2.BaseLoader()

        env = jinja2.Environment(
            loader=loader,
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


def getTemplateC(
    package_name, template_name, template_subdir="templates_c", extensions=()
):
    return getEnvironment(
        package_name=package_name,
        template_subdir=template_subdir,
        extensions=extensions,
    ).get_template(template_name)


def getTemplateFromString(template_str):
    return getEnvironment(
        package_name=None, template_subdir=None, extensions=()
    ).from_string(template_str.strip())


_template_cache = {}


def renderTemplateFromString(template_str, **kwargs):
    # Avoid recreating templates, hoping to save some time.
    if template_str not in _template_cache:
        _template_cache[template_str] = getTemplateFromString(template_str)

    result = _template_cache[template_str].render(**kwargs)

    # Jinja produces unicode value, but our emission wants str, or else
    # it messes up. TODO: We might switch to unicode one day or bytes
    # for Python3 one day, but that seems to much work.
    if str is not unicode:
        return result.encode("utf8")
    else:
        return result
