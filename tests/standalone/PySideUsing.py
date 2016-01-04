#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#

# This test is using signals and will only work if PySide properly accepts
# compiled functions as callables.

from __future__ import print_function

from PySide.QtCore import Slot, Signal, QObject, QMetaObject

class Communicate(QObject):
    speak = Signal(int)
    def __init__(self,name = "",parent = None):
        QObject.__init__(self,parent)
        self.setObjectName(name)

class Speaker(QObject):
    @Slot(int)
    def on_communicator_speak(self, stuff):
        print(stuff)

speaker = Speaker()
someone = Communicate(name = "communicator",parent = speaker)

QMetaObject.connectSlotsByName(speaker)

print("The answer is:",end = "")
# emit  'speak' signal
someone.speak.emit(42)
print("Slot should have made output by now.")
