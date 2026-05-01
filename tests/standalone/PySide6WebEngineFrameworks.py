#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Regression test for macOS PySide6 Qt WebEngine framework inclusion."""

# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --mode=app
# nuitka-project: --macos-app-icon=none

# nuitka-skip-unless-expression: sys.platform == "darwin"
# nuitka-skip-unless-imports: PySide6.QtWebEngineCore

from __future__ import print_function

import os
import sys

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtWebEngineCore import QWebEnginePage

os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")


# The macOS builder is headless, so avoid requiring a visible WebEngine widget.
app = QGuiApplication(sys.argv[:1] + ["-platform", "offscreen"])
page = QWebEnginePage()

html = """\
<!DOCTYPE html>
<html>
<head>
  <title>qtwe3857</title>
  <script>
    function getAnswer() {
      return document.getElementById("answer").textContent;
    }
  </script>
</head>
<body>
  <h1 id="answer">3857</h1>
</body>
</html>
"""

state = {"error": None, "timed_out": False}


def onFailure(message):
    state["error"] = message
    print("failure=%s" % message)
    sys.stdout.flush()
    app.quit()


def onJavaScriptDone(result):
    print("js-result=%s" % result)

    if result != "3857":
        onFailure("Unexpected JavaScript result '%s'" % result)
        return

    sys.stdout.flush()
    app.quit()


def onLoadFinished(ok):
    print("loaded=%s" % ok)

    if not ok:
        onFailure("WebEngine failed to load inline HTML")
        return

    title = page.title()
    print("title=%s" % title)

    if title != "qtwe3857":
        onFailure("Unexpected page title '%s'" % title)
        return

    page.runJavaScript("getAnswer()", onJavaScriptDone)


def onTimeout():
    state["timed_out"] = True
    print("timeout")
    sys.stdout.flush()
    app.quit()


page.loadFinished.connect(onLoadFinished)
QTimer.singleShot(15000, onTimeout)
page.setHtml(html, QUrl("file:///qtwe3857.html"))
app.exec()

if state["error"] is not None:
    raise AssertionError(state["error"])

if state["timed_out"]:
    raise AssertionError("WebEngine timed out")

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
