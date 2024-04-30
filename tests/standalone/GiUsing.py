#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-skip-unless-imports: cairo
# nuitka-skip-unless-imports: gi

import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gdk, Gtk

# isort:start

Gtk.init()

image = cairo.ImageSurface.create_from_png("../../doc/images/Nuitka-Logo-Symbol.png")
region = Gdk.cairo_region_create_from_surface(image)

print("All OK")

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
