""" This module is only an abstraction of OrderedSet which is not present in
Python at all.

"""

try:
    # spell-checker: ignore orderedset
    from orderedset import OrderedSet
except ImportError:
    try:
        from ordered_set import OrderedSet
    except ImportError:
        from .OrderedSetsFallback import OrderedSet


def buildOrderedSet(*producers):
    """Helper function to merge multiple producers into one OrderedSet value"""
    values = []

    for producer in producers:
        values.extend(producer)

    return OrderedSet(values)
