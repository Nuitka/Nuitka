"""This module is only an abstraction of OrderedSet which is not present in
Python at all.

spell-checker: ignore orderedset,orderedsets

"""

from nuitka.PythonVersions import python_version

recommended_orderedset_package_name, recommended_orderedset_module_name = (
    ("ordered-set", "ordered_set")
    if python_version >= 0x370
    else ("orderedset", "orderedsets")
)


def _tryImportOrderedSet():
    try:
        from orderedset import OrderedSet as result
    except ImportError:
        try:
            from ordered_set import OrderedSet as result
        except ImportError:
            return None

    return result


OrderedSet = _tryImportOrderedSet()


if OrderedSet is None:
    from .OrderedSetsFallback import OrderedSet


def buildOrderedSet(*producers):
    """Helper function to merge multiple producers into one OrderedSet value"""
    values = []

    for producer in producers:
        values.extend(producer)

    return OrderedSet(values)
