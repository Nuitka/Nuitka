#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-project: --mode=app-dist
# nuitka-project: --enable-plugin=pyqt6

# nuitka-skip-unless-imports: PyQt6.QtGui

from __future__ import print_function

import types

from PyQt6.QtCore import (
    QCoreApplication,
    QMetaObject,
    QObject,
    QSettings,
    pyqtSignal,
    pyqtSlot,
)

# This test is playing with configuration settings and checking that works.

app = QCoreApplication([])
app.setOrganizationName("BOGUS_NAME")
app.setOrganizationDomain("bogosity.com")
app.setApplicationName("BOGUS")
print("OK.")

# This test is using signals and will only work if PyQt6 properly accepts
# compiled functions as callables.


class Communicate(QObject):
    speak = pyqtSignal(int)

    def __init__(self, name="", parent=None):
        QObject.__init__(self, parent)
        self.setObjectName(name)


class SpeakerBase(QObject):
    def describe(self):
        return "base speaker"


class Speaker(SpeakerBase):
    @pyqtSlot(int)
    def on_communicator_speak(self, stuff):
        # This checks that zero-argument "super()" works with compiled slot
        # methods, which use the implicit "__class__" closure.
        print(stuff, super().describe())


class UndecoratedSpeaker(QObject):
    def on_communicator_speak(self, stuff):
        print("undecorated", stuff)


class PlainReceiver(object):
    def on_signal(self, value):
        print("plain receiver", value)


speaker = Speaker()
someone = Communicate(name="communicator", parent=speaker)

# Decorated slots must be exposed as real Python methods, otherwise PyQt6
# consumers that use the SIP method checks, e.g. QtDBus, will reject them.
assert type(speaker.on_communicator_speak) is types.MethodType, type(
    speaker.on_communicator_speak
)
assert hasattr(speaker.on_communicator_speak, "__pyqtSignature__")

QMetaObject.connectSlotsByName(speaker)

print("The answer is:", end="")
# emit  'speak' signal
someone.speak.emit(42)
print("Slot should have made output by now.")

# Connections to compiled methods must be disconnectable by a new bound method
# object, and the receiver must be recognized, so that connection lifetime is
# not extended by the proxy used for arbitrary callables.

sender = Communicate(name="sender")
undecorated_speaker = UndecoratedSpeaker()

sender.speak.connect(undecorated_speaker.on_communicator_speak)
sender.speak.emit(1)
sender.speak.disconnect(undecorated_speaker.on_communicator_speak)
sender.speak.emit(2)

plain_receiver = PlainReceiver()

sender.speak.connect(plain_receiver.on_signal)
sender.speak.emit(3)
sender.speak.disconnect(plain_receiver.on_signal)
sender.speak.emit(4)

# Each connection is disconnected separately, and matching happens by receiver
# and function, not by the bound method object identity.
sender.speak.connect(plain_receiver.on_signal)
sender.speak.connect(plain_receiver.on_signal)
sender.speak.emit(5)
sender.speak.disconnect(plain_receiver.on_signal)
sender.speak.emit(6)

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
