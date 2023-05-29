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
""" Multidist re-formulation. """

import os

from nuitka.Options import getMainEntryPointFilenames
from nuitka.utils.ModuleNames import makeMultidistModuleName


def _stripPythonSuffix(filename):
    if filename.lower().endswith(".py"):
        return filename[:-3]
    elif filename.lower().endswith(".pyw"):
        return filename[:-4]
    else:
        return filename


def createMultidistMainSourceCode(main_filenames):
    main_basenames = [
        _stripPythonSuffix(os.path.basename(main_filename))
        for main_filename in main_filenames
    ]

    main_module_names = [
        makeMultidistModuleName(count, main_basename)
        for count, main_basename in enumerate(main_basenames, start=1)
    ]

    from nuitka.utils.Jinja2 import renderTemplateFromString

    source_code = renderTemplateFromString(
        r"""
import sys, re, os
main_basename = re.sub(r'(.pyw?|\.exe|\.bin)?$', '', os.path.normcase(os.path.basename(sys.argv[0])))
{% for main_module_name, main_basename in zip(main_module_names, main_basenames) %}
if main_basename == "{{main_basename}}":
    __import__("{{main_module_name.asString()}}")
    sys.exit(0)
{% endfor %}

sys.exit("Error, failed to detect what to do for filename derived name '%s'." % main_basename)
""",
        main_module_names=main_module_names,
        main_basenames=main_basenames,
        zip=zip,
    )

    return source_code


def locateMultidistModule(module_name):
    multidist_index = int(str(module_name).split("-")[1])

    return (
        module_name,
        getMainEntryPointFilenames()[multidist_index - 1],
        "py",
        "absolute",
    )
