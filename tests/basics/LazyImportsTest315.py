import sys
from types import LazyImportType

lazy import colorsys  # isort:skip

print("Explicit import lazy:", type(globals()["colorsys"]) is LazyImportType)
print("Explicit import loaded:", "colorsys" in sys.modules)
print("Explicit import value:", colorsys.rgb_to_hsv(1.0, 0.0, 0.0))
print("Explicit import loaded:", "colorsys" in sys.modules)

lazy from cmath import sqrt as complex_sqrt  # isort:skip

print("Explicit from import lazy:", type(globals()["complex_sqrt"]) is LazyImportType)
print("Explicit from import loaded:", "cmath" in sys.modules)
print("Explicit from import value:", complex_sqrt(-1))
print("Explicit from import loaded:", "cmath" in sys.modules)

__lazy_modules__ = (
    "fractions",
    "xml.etree.ElementTree",
    "nuitka_missing_lazy_test_module",
)

from fractions import Fraction  # isort:skip
import xml.etree.ElementTree as element_tree  # isort:skip

print("From import lazy:", type(globals()["Fraction"]) is LazyImportType)
print("Aliased import lazy:", type(globals()["element_tree"]) is LazyImportType)
print("From import loaded:", "fractions" in sys.modules)
print("Aliased import loaded:", "xml.etree.ElementTree" in sys.modules)
print("From import value:", Fraction(1, 2) + Fraction(1, 3))
print("Aliased import value:", element_tree.Element("node").tag)
print("From import loaded:", "fractions" in sys.modules)
print("Aliased import loaded:", "xml.etree.ElementTree" in sys.modules)

import nuitka_missing_lazy_test_module  # isort:skip

print(
    "Missing import lazy:",
    type(globals()["nuitka_missing_lazy_test_module"]) is LazyImportType,
)

try:
    nuitka_missing_lazy_test_module
except ModuleNotFoundError as e:
    print("Deferred import error:", e)
