#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Textual standalone test with lazy-loaded widgets."""

# nuitka-skip-unless-imports: textual

# nuitka-project: --mode=standalone

from __future__ import print_function

from textual.app import App
from textual.widgets import Footer, Header, Static


class TextualUsingApp(App):
    def compose(self):
        yield Header()
        yield Static("Textual body", id="body")
        yield Footer()

    def on_ready(self):
        header = self.query_one(Header)
        body = self.query_one(Static)
        footer = self.query_one(Footer)

        print("Header module:", Header.__module__)
        print("Static module:", Static.__module__)
        print("Footer module:", Footer.__module__)
        print(
            "Mounted widgets:",
            ",".join(widget.__class__.__name__ for widget in (header, body, footer)),
        )
        print("Body id:", body.id)

        self.exit()


if __name__ == "__main__":
    TextualUsingApp().run(headless=True)
    print("OK.")

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
