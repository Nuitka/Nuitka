#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-project: --enable-plugin=pyqt5

# nuitka-skip-unless-imports: PyQt5.QtGui

# nuitka-project-if: {OS} != "Darwin":
#   nuitka-project: --mode=standalone
# nuitka-project-else:
#   nuitka-project: --mode=app

from __future__ import print_function

import gc
import sys
import types
import weakref

from PyQt5.QtCore import (
    QCoreApplication,
    QMetaObject,
    QObject,
    QSettings,
    Qt,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)

# This test is playing with configuration settings and checking that works.

app = QCoreApplication([])
app.setOrganizationName("BOGUS_NAME")
app.setOrganizationDomain("bogosity.com")
app.setApplicationName("BOGUS")
print("OK.")

# This test is using signals and will only work if PySide properly accepts
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
        if sys.version_info[0] >= 3:
            description = super().describe()
        else:
            description = super(Speaker, self).describe()

        print(stuff, description)


class UndecoratedSpeaker(QObject):
    def on_communicator_speak(self, stuff):
        print("undecorated", stuff)


class PlainReceiver(object):
    def on_signal(self, value):
        print("plain receiver", value)


class TimerReceiver(QObject):
    @pyqtSlot()
    def on_decorated_timeout(self):
        timer_calls.append("decorated")

    def on_plain_timeout(self):
        timer_calls.append("plain")


class LifetimeTimerReceiver(QObject):
    def on_timeout(self):
        lifetime_timer_calls.append("called")


speaker = Speaker()
someone = Communicate(name="communicator", parent=speaker)

# Decorated slots must be exposed as real Python methods, otherwise PyQt5
# consumers that use the SIP method checks will reject them.
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

# Timers must recognize the receiver, including for compiled methods.
timer_receiver = TimerReceiver()
timer_calls = []

QTimer.singleShot(0, timer_receiver.on_decorated_timeout)
QTimer.singleShot(0, timer_receiver.on_plain_timeout)
QTimer.singleShot(0, Qt.PreciseTimer, timer_receiver.on_plain_timeout)

for _unused in range(1000):
    app.processEvents()

    if len(timer_calls) == 3:
        break

print("timer calls:", sorted(timer_calls))
assert sorted(timer_calls) == ["decorated", "plain", "plain"], timer_calls

# The timer must only weakly reference the receiver, so that it can be
# collected and the callback is not run after that.
lifetime_timer_calls = []
lifetime_receiver = LifetimeTimerReceiver()
lifetime_receiver_ref = weakref.ref(lifetime_receiver)

QTimer.singleShot(0, lifetime_receiver.on_timeout)
del lifetime_receiver
gc.collect()

print("timer receiver gone:", lifetime_receiver_ref() is None)
assert lifetime_receiver_ref() is None

for _unused in range(1000):
    app.processEvents()

    if lifetime_timer_calls:
        break

print("timer lifetime calls:", lifetime_timer_calls)
assert lifetime_timer_calls == [], lifetime_timer_calls

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
