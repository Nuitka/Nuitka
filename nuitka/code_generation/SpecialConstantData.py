#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Special constant value types.

Constants that need different serialization or storage than standard
PyObject values, e.g. raw binary blobs.
"""


def _isBlobConstant(name):
    """Check if a constant name denotes blob data (raw bytes, not PyObject)."""

    return name.startswith("blob_") or name.startswith("const_blob_")


def getConstantCType(name):
    """Return the C type for a constant slot given its name key."""
    if _isBlobConstant(name):
        return "char const *"

    return "PyObject *"


def hasSpecialDetails(name):
    """Return True if the named constant carries extra metadata."""
    return _isBlobConstant(name)


class SpecialConstantBase(object):
    """Base for constants that carry extra metadata beyond a plain PyObject."""

    __slots__ = ()

    @staticmethod
    def getConstantDetails():
        return {}


class BlobData(SpecialConstantBase):
    """Used to pickle bytes to become raw pointers."""

    __slots__ = ("data", "name")

    def __init__(self, data, name):
        SpecialConstantBase.__init__(self)
        self.data = data
        self.name = name

    def getData(self):
        return self.data

    def getConstantDetails(self):
        return {"size": len(self.data)}

    def __repr__(self):
        return "<nuitka.code_generation.SpecialConstantData.BlobData %s>" % self.name


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
