#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


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

    def __init__(self, name, module):
        super(OurModule, self).__init__(name)
        # Keep the original module alive, on Python2 its dictionary is cleared
        # when it is deallocated, and real world wrappers do keep it too.
        self.__dict__["_module"] = module

    def __getattr__(self, attr):
        try:
            return self.attribute_dict[attr]
        except KeyError:
            raise AttributeError(attr)


MARKER = "marker"


def get_frame_globals():
    return sys._getframe(0).f_globals


def own_globals_used():
    # Compiled functions must keep using the module dictionary they were
    # compiled against, even after the module replaced itself in
    # "sys.modules", i.e. the replacement must not become their globals.
    return get_frame_globals() is globals()


def marker_found():
    return get_frame_globals().get("MARKER")


def builtins_found():
    return "__builtins__" in get_frame_globals()


OurModule.attribute_dict["own_globals_used"] = own_globals_used
OurModule.attribute_dict["marker_found"] = marker_found
OurModule.attribute_dict["builtins_found"] = builtins_found

sys.modules[__name__] = OurModule(__name__, sys.modules[__name__])

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
