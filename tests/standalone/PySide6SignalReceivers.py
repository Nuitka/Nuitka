#     Copyright 2026, XiaoYouChR, mailto:<XiaoYouChR@qq.com> find license text at end of file


"""Receivers of compiled methods connected to signals must be released."""

# nuitka-project: --mode=standalone
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --no-debug-immortal-assumptions

# nuitka-skip-unless-imports: PySide6.QtCore

from __future__ import print_function

from PySide6.QtCore import QObject, Signal


class Sender(QObject):
    fired = Signal()


class Receiver(object):
    def onFired(self):
        print("Receiver called")


sender = Sender()

# Released receivers are disconnected, and each of these disconnects releases
# the method function once, so it has to survive many of them.
for _ in range(10):
    sender.fired.connect(Receiver().onFired)

sender.fired.emit()
Receiver().onFired()

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
