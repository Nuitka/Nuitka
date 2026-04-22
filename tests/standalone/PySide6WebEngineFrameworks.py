#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Regression test for macOS PySide6 Qt WebEngine framework inclusion."""

# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --mode=app
# nuitka-project: --macos-app-icon=none

# nuitka-skip-unless-expression: sys.platform == "darwin"
# nuitka-skip-unless-imports: PySide6.QtWebEngineWidgets

from __future__ import print_function

import sys

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

app = QApplication([])
view = QWebEngineView()
view.resize(320, 200)

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

state = {"timed_out": False}


def onJavaScriptDone(result):
    print("js-result=%s" % result)
    sys.stdout.flush()
    app.quit()


def onLoadFinished(ok):
    print("loaded=%s" % ok)

    if not ok:
        raise AssertionError("WebEngine failed to load inline HTML")

    print("title=%s" % view.title())
    view.page().runJavaScript("getAnswer()", onJavaScriptDone)


def onTimeout():
    state["timed_out"] = True
    print("timeout")
    sys.stdout.flush()
    app.quit()


view.loadFinished.connect(onLoadFinished)
QTimer.singleShot(15000, onTimeout)
view.setHtml(html, QUrl("file:///qtwe3857.html"))
app.exec()

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
