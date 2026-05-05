#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Jinja folklore wrappers and handling of inline copy usage."""

import os
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
_markupsafe = None


def takeImportedModules(module_name):
    result = {}

    for loaded_module_name in tuple(sys.modules):
        if loaded_module_name == module_name or loaded_module_name.startswith(
            module_name + "."
        ):
            result[loaded_module_name] = sys.modules[loaded_module_name]
            del sys.modules[loaded_module_name]

    return result


def restoreImportedModules(saved_modules):
    for loaded_module_name in sorted(saved_modules):
        sys.modules[loaded_module_name] = saved_modules[loaded_module_name]


def _getTemplateSubDirectory(package_name, template_subdir):
    if package_name not in sys.modules:
        try:
            __import__(package_name)
        except ImportError:
            return None

    module = sys.modules[package_name]
    package_path = None

    if hasattr(module, "__path__"):
        module_path = tuple(module.__path__)

        if module_path:
            package_path = module_path[0]
    elif hasattr(module, "__file__"):
        package_path = os.path.dirname(module.__file__)

    if package_path is None:
        return None

    template_path = os.path.join(package_path, template_subdir)

    if os.path.isdir(template_path):
        return template_path
    else:
        return None


def getJinja2Package():
    global _jinja2, _markupsafe  # singleton package using a cache, pylint: disable=global-statement

    if _jinja2 is None:
        old_pkg_resources = takeImportedModules("pkg_resources")

        try:
            # Keep Jinja2 import isolated from ambient pkg_resources state.
            # Load this before our inline MarkupSafe, or else it will warn when
            # site-packages contains another MarkupSafe installation.
            importFromInlineCopy("pkg_resources", must_exist=False)

            if _markupsafe is None:
                # Prefer our inline copy over any already imported variant, older
                # Jinja2 needs an API that newer MarkupSafe releases removed.
                takeImportedModules("markupsafe")
                _markupsafe = importFromInlineCopy("markupsafe", must_exist=True)

            takeImportedModules("jinja2")
            _jinja2 = importFromInlineCopy("jinja2", must_exist=True)
        finally:
            takeImportedModules("pkg_resources")
            restoreImportedModules(old_pkg_resources)

    return _jinja2


def getEnvironment(package_name, template_subdir, extensions):
    key = package_name, template_subdir, extensions

    if key not in environments:
        jinja2 = getJinja2Package()

        if package_name is not None:
            template_path = _getTemplateSubDirectory(
                package_name=package_name, template_subdir=template_subdir
            )

            if template_path is not None:
                loader = jinja2.FileSystemLoader(template_path)
            else:
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
