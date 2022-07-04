""" This module is only an abstraction of OrderedSet which is not present in
Python at all.

"""

# Only for re-export, pylint: disable=unused-import

try:
    # spell-checker: ignore orderedset
    from orderedset import OrderedSet
except ImportError:
    try:
        from ordered_set import OrderedSet
    except ImportError:
        from .OrderedSetsFallback import OrderedSet
