# nuitka-skip-unless-imports: cairo

import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gdk, Gtk

Gtk.init()

image = cairo.ImageSurface.create_from_png("../../doc/images/Nuitka-Logo-Symbol.png")
region = Gdk.cairo_region_create_from_surface(image)

print("All OK")
