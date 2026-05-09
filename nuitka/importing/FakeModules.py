#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Handling of fake module descriptions and reserved names."""

from nuitka.containers.Namedtuples import makeNamedtupleClass
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.utils.ModuleNames import ModuleName

from .ImportingResults import makeFindModuleResult

FakeModuleDescription = makeNamedtupleClass(
    "FakeModuleDescription",
    (
        "module_name",
        "source_code",
        "source_filename",
        "reason",
    ),
)

_fake_modules = OrderedSet()


def makeFakeModuleDescription(module_name, source_code, source_filename, reason):
    return FakeModuleDescription(
        module_name=module_name,
        source_code=source_code,
        source_filename=source_filename,
        reason=reason,
    )


def addFakeModule(module_name):
    assert type(module_name) is ModuleName, module_name

    _fake_modules.add(module_name)


def locateFakeModule(module_name):
    if module_name in _fake_modules:
        return makeFindModuleResult(
            found_module_name=module_name,
            module_package=module_name.getPackageName(),
            module_filename=None,
            module_kind="py",
            finding="fake",
        )

    return None


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
