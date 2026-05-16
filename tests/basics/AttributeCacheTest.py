#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


class WithProperty:
    @property
    def x(self):
        return "from_property"


obj = WithProperty()
obj.__dict__["x"] = "from_instance_dict"

print("property shadows instance dict:", obj.x)


class WithNonDataDescriptor:
    class _nd:
        def __get__(self, obj, objtype=None):
            return "from_non_data_descriptor"

    y = _nd()


obj2 = WithNonDataDescriptor()
obj2.__dict__["y"] = "from_instance_dict"

print("instance dict shadows non-data descriptor:", obj2.y)


class WithCustomGetattribute:
    def __getattribute__(self, name):
        if name == "z":
            return "intercepted"
        return object.__getattribute__(self, name)


obj3 = WithCustomGetattribute()
obj3.__dict__["z"] = "raw_value"

print("custom __getattribute__ called:", obj3.z)


class Plain:
    def __init__(self):
        self.value = 42


obj4 = Plain()
print("plain instance attribute:", obj4.value)


class Empty:
    pass


try:
    _ = Empty().missing
    print("no exception raised")
except AttributeError:
    print("AttributeError on missing attribute: ok")


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
