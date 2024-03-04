#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


import sys
import types


class OurModule(types.ModuleType):
    attribute_dict = {
        "valid": "valid_value",
        # Import mechanics use these.
        "__package__": __package__,
        "__name__": __name__,
    }

    if "__loader__" in globals():
        attribute_dict["__loader__"] = __loader__

    def __init__(self, name):
        super(OurModule, self).__init__(name)

    def __getattr__(self, attr):
        try:
            return self.attribute_dict[attr]
        except KeyError:
            raise AttributeError(attr)


sys.modules[__name__] = OurModule(__name__)

#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
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
