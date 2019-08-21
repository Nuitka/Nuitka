#     Copyright 2019, Tommy Li, mailto:tommyli3318@gmail.com
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


# nuitka-skip-unless-imports: markupsafe

from markupsafe import Markup, escape

# escape replaces special characters and wraps in Markup
print(escape('<script>alert(document.cookie);</script>'))

# wrap in Markup to mark text "safe" and prevent escaping
Markup('<strong>Hello</strong>')

print(escape(Markup('<strong>Hello</strong>')))

# Markup is a text subclass (str on Python 3, unicode on Python 2)
# methods and operators escape their arguments
template = Markup("Hello <em>%s</em>")
print(template % '"World"')
