#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Differential structural test for the Nuitka dictionary helpers.

Builds two dictionaries with the same operation sequence. One is driven only
by CPython APIs, the other by a mix of CPython APIs and Nuitka helpers (the
compiled subscript operations). After every step the internal dictionary state
is compared.
"""

import ctypes
import random
import sys

py_version = sys.version_info[:2]
voidp = ctypes.c_void_p

if hasattr(ctypes, "c_ssize_t"):
    py_ssize_t = ctypes.c_ssize_t
elif ctypes.sizeof(voidp) == 8:
    py_ssize_t = ctypes.c_int64
else:
    py_ssize_t = ctypes.c_int32


def _at(address, structure):
    return ctypes.cast(address, ctypes.POINTER(structure)).contents


def _voidp_at(address, index):
    return ctypes.cast(address, ctypes.POINTER(voidp))[index]


def _signed_at(address, index, size):
    if size == 1:
        return ctypes.cast(address, ctypes.POINTER(ctypes.c_int8))[index]
    if size == 2:
        return ctypes.cast(address, ctypes.POINTER(ctypes.c_int16))[index]
    if size == 4:
        return ctypes.cast(address, ctypes.POINTER(ctypes.c_int32))[index]
    return ctypes.cast(address, ctypes.POINTER(ctypes.c_int64))[index]


class PyDictEntry(ctypes.Structure):
    _fields_ = [
        ("me_hash", py_ssize_t),
        ("me_key", voidp),
        ("me_value", voidp),
    ]


if py_version < (3, 0):

    class PyDictObject(ctypes.Structure):
        _fields_ = [
            ("ob_refcnt", py_ssize_t),
            ("ob_type", voidp),
            ("ma_fill", py_ssize_t),
            ("ma_used", py_ssize_t),
            ("ma_mask", py_ssize_t),
            ("ma_table", voidp),
            ("ma_lookup", voidp),
            ("ma_smalltable", PyDictEntry * 8),
        ]

    def getDictState(d):
        mp = _at(id(d), PyDictObject)
        table = _at(mp.ma_table, PyDictEntry)
        entries = []

        for i in range(mp.ma_mask + 1):
            entry = _at(mp.ma_table + i * ctypes.sizeof(PyDictEntry), PyDictEntry)
            entry_hash = entry.me_hash if entry.me_value is not None else 0
            entries.append((entry_hash, entry.me_key, entry.me_value))

        return ("open", mp.ma_used, mp.ma_fill, mp.ma_mask, tuple(entries))

elif py_version < (3, 6):

    class PyDictKeysObject(ctypes.Structure):
        _fields_ = [
            ("dk_refcnt", py_ssize_t),
            ("dk_size", py_ssize_t),
            ("dk_lookup", voidp),
            ("dk_usable", py_ssize_t),
            ("dk_entries", PyDictEntry * 1),
        ]

    class PyDictObject(ctypes.Structure):
        _fields_ = [
            ("ob_refcnt", py_ssize_t),
            ("ob_type", voidp),
            ("ma_used", py_ssize_t),
            ("ma_keys", voidp),
            ("ma_values", voidp),
        ]

    def getDictState(d):
        mp = _at(id(d), PyDictObject)
        keys = _at(mp.ma_keys, PyDictKeysObject)
        entries_address = ctypes.addressof(keys) + PyDictKeysObject.dk_entries.offset
        entries = []

        for i in range(keys.dk_size):
            entry = _at(entries_address + i * ctypes.sizeof(PyDictEntry), PyDictEntry)
            value = entry.me_value

            if mp.ma_values:
                value = _voidp_at(mp.ma_values, i)

            entry_hash = entry.me_hash if entry.me_key is not None else 0
            entries.append((entry_hash, entry.me_key, value))

        return (
            "split" if mp.ma_values else "combined",
            mp.ma_used,
            keys.dk_size,
            keys.dk_usable,
            tuple(entries),
        )

else:

    class PyDictKeysObject610(ctypes.Structure):
        _fields_ = [
            ("dk_refcnt", py_ssize_t),
            ("dk_size", py_ssize_t),
            ("dk_lookup", voidp),
            ("dk_usable", py_ssize_t),
            ("dk_nentries", py_ssize_t),
            ("dk_indices", ctypes.c_uint8 * 1),
        ]

    class PyDictObject610(ctypes.Structure):
        _fields_ = [
            ("ob_refcnt", py_ssize_t),
            ("ob_type", voidp),
            ("ma_used", py_ssize_t),
            ("ma_version_tag", ctypes.c_uint64),
            ("ma_keys", voidp),
            ("ma_values", voidp),
        ]

    class PyDictKeysObject311(ctypes.Structure):
        _fields_ = [
            ("dk_refcnt", py_ssize_t),
            ("dk_log2_size", ctypes.c_uint8),
            ("dk_log2_index_bytes", ctypes.c_uint8),
            ("dk_kind", ctypes.c_uint8),
            ("dk_version", ctypes.c_uint32),
            ("dk_usable", py_ssize_t),
            ("dk_nentries", py_ssize_t),
            ("dk_indices", ctypes.c_uint8 * 1),
        ]

    class PyDictObject313(ctypes.Structure):
        _fields_ = [
            ("ob_refcnt", py_ssize_t),
            ("ob_type", voidp),
            ("ma_used", py_ssize_t),
            ("ma_version_tag", ctypes.c_uint64),
            ("ma_keys", voidp),
            ("ma_values", voidp),
        ]

    class PyDictObject314(ctypes.Structure):
        _fields_ = [
            ("ob_refcnt", py_ssize_t),
            ("ob_type", voidp),
            ("ma_used", py_ssize_t),
            ("_ma_watcher_tag", ctypes.c_uint64),
            ("ma_keys", voidp),
            ("ma_values", voidp),
        ]

    class PyDictValues313(ctypes.Structure):
        _fields_ = [
            ("capacity", ctypes.c_uint8),
            ("size", ctypes.c_uint8),
            ("embedded", ctypes.c_uint8),
            ("valid", ctypes.c_uint8),
            ("values", voidp * 1),
        ]

    def _index_size(size):
        if size <= 0xFF:
            return 1
        if size <= 0xFFFF:
            return 2
        if size <= 0xFFFFFFFF:
            return 4
        return 8

    def getDictState(d):
        if py_version < (3, 11):
            mp = _at(id(d), PyDictObject610)
            keys = _at(mp.ma_keys, PyDictKeysObject610)
            indices_address = (
                ctypes.addressof(keys) + PyDictKeysObject610.dk_indices.offset
            )
            index_size = _index_size(keys.dk_size)
            entries_address = indices_address + index_size * keys.dk_size
            indices = tuple(
                _signed_at(indices_address, i, index_size) for i in range(keys.dk_size)
            )
            entries = []
            values = mp.ma_values

            for i in range(keys.dk_nentries):
                entry = _at(
                    entries_address + i * ctypes.sizeof(PyDictEntry), PyDictEntry
                )
                value = entry.me_value

                if values:
                    value = _voidp_at(values, i)

                entry_hash = entry.me_hash if entry.me_key is not None else 0
                entries.append((entry_hash, entry.me_key, value))

            return (
                "split" if values else "combined",
                mp.ma_used,
                0,
                keys.dk_size,
                keys.dk_usable,
                keys.dk_nentries,
                indices,
                tuple(entries),
            )

        if py_version < (3, 14):
            mp = _at(id(d), PyDictObject313)
        else:
            mp = _at(id(d), PyDictObject314)

        keys = _at(mp.ma_keys, PyDictKeysObject311)
        size = 1 << keys.dk_log2_size
        index_bytes = 1 << keys.dk_log2_index_bytes
        indices_address = ctypes.addressof(keys) + PyDictKeysObject311.dk_indices.offset
        entries_address = indices_address + index_bytes
        index_size = _index_size(size)
        indices = tuple(_signed_at(indices_address, i, index_size) for i in range(size))
        unicode_keys = keys.dk_kind != 0
        entry_size = 16 if unicode_keys else ctypes.sizeof(PyDictEntry)
        entries = []
        values = mp.ma_values
        values_state = None

        if values and py_version < (3, 13):
            order_size = ctypes.cast(values - 2, ctypes.POINTER(ctypes.c_uint8))[0]
            order = tuple(
                ctypes.cast(values - 3 - i, ctypes.POINTER(ctypes.c_uint8))[0]
                for i in range(order_size)
            )
            entries_state = []

            for i in range(keys.dk_nentries):
                entry_address = entries_address + i * entry_size
                key = _voidp_at(entry_address, 0)
                entries_state.append((0, key, _voidp_at(values, i)))

            return (
                "split",
                mp.ma_used,
                keys.dk_version,
                keys.dk_kind,
                size,
                keys.dk_usable,
                keys.dk_nentries,
                indices,
                tuple(entries_state),
                order,
            )

        if values:
            values_object = _at(values, PyDictValues313)
            values_address = values + PyDictValues313.values.offset
            order_address = values_address + values_object.capacity * ctypes.sizeof(
                voidp
            )
            order = tuple(
                ctypes.cast(order_address + i, ctypes.POINTER(ctypes.c_uint8))[0]
                for i in range(values_object.size)
            )
            entries_state = []

            for i in range(keys.dk_nentries):
                entry_address = entries_address + i * entry_size
                key = _voidp_at(entry_address, 0)
                entries_state.append((0, key, _voidp_at(values_address, i)))

            return (
                "split",
                mp.ma_used,
                keys.dk_version,
                keys.dk_kind,
                size,
                keys.dk_usable,
                keys.dk_nentries,
                indices,
                tuple(entries_state),
                order,
            )

        for i in range(keys.dk_nentries):
            entry_address = entries_address + i * entry_size

            if unicode_keys:
                key = _voidp_at(entry_address, 0)
                value = _voidp_at(entry_address, 1)
                entries.append((0, key, value))
            else:
                entry = _at(entry_address, PyDictEntry)
                entry_hash = entry.me_hash if entry.me_key is not None else 0
                entries.append((entry_hash, entry.me_key, entry.me_value))

        return (
            "combined",
            mp.ma_used,
            keys.dk_version,
            keys.dk_kind,
            size,
            keys.dk_usable,
            keys.dk_nentries,
            indices,
            tuple(entries),
        )


def describe(state):
    return repr(state)


def getVersionTag(d):
    # Nuitka maintains the tag for 3.6 through 3.12; Python 3.13 removes it.
    if py_version < (3, 6) or py_version >= (3, 13):
        return None

    return _at(id(d), PyDictObject610).ma_version_tag


def compareStates(ref, cand, step):
    state_ref = getDictState(ref)
    state_cand = getDictState(cand)

    if state_ref != state_cand:
        sys.stderr.write(
            "MISMATCH at step %d\nREF: %s\nCAND: %s\n"
            % (step, describe(state_ref), describe(state_cand))
        )
        return False

    return True


class HashKey(object):
    def __init__(self, value, hash_value):
        self.value = value
        self.hash_value = hash_value

    def __hash__(self):
        return self.hash_value

    def __eq__(self, other):
        return isinstance(other, HashKey) and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)


def makeOperations():
    operations = []

    ints = [i for i in range(60)]
    strings = ["key%d" % i for i in range(30)]
    tuples = [(i, i + 1) for i in range(10)]
    collisions = [HashKey(i, 7) for i in range(10)]

    keys = ints + strings + tuples + collisions

    for key in keys:
        operations.append((0, "set", key, key))

    for key in keys[::3]:
        operations.append((1, "set", key, "replaced"))

    for key in keys[::4]:
        operations.append((0, "del", key, None))

    for key in keys[::4]:
        operations.append((1, "set", key, key))

    for key in keys[::5]:
        operations.append((0, "del", key, None))
        operations.append((1, "del", key, None))

    random.seed(1871)

    for _ in range(300):
        key = keys[random.randrange(len(keys))]
        mix = random.randrange(2)

        if random.randrange(3):
            operations.append((mix, "set", key, random.randrange(1000)))
        else:
            operations.append((mix, "del", key, None))

    return operations


def runOperations(operations):
    reference = {}
    candidate = {}

    previous_ref_tag = getVersionTag(reference)
    previous_candidate_tag = getVersionTag(candidate)

    if not compareStates(reference, candidate, 0):
        return False

    for step, operation in enumerate(operations, 1):
        mix, kind, key, value = operation

        if kind == "set":
            dict.__setitem__(reference, key, value)

            if mix:
                dict.__setitem__(candidate, key, value)
            else:
                candidate[key] = value
        else:
            ref_error = None
            candidate_error = None

            try:
                dict.__delitem__(reference, key)
            except KeyError:
                ref_error = "KeyError"

            try:
                if mix:
                    dict.__delitem__(candidate, key)
                else:
                    del candidate[key]
            except KeyError:
                candidate_error = "KeyError"

            if ref_error != candidate_error:
                sys.stderr.write(
                    "ERROR MISMATCH at step %d: %r != %r\n"
                    % (step, ref_error, candidate_error)
                )
                return False

        current_ref_tag = getVersionTag(reference)
        current_candidate_tag = getVersionTag(candidate)

        if current_ref_tag is not None:
            ref_changed = current_ref_tag != previous_ref_tag
            candidate_changed = current_candidate_tag != previous_candidate_tag

            if ref_changed != candidate_changed:
                sys.stderr.write(
                    "VERSION TAG MISMATCH at step %d (%s != %s)\n"
                    % (step, ref_changed, candidate_changed)
                )
                return False

        if not compareStates(reference, candidate, step):
            return False

        previous_ref_tag = current_ref_tag
        previous_candidate_tag = current_candidate_tag

    if reference != candidate:
        sys.stderr.write("FINAL DICT MISMATCH\n")
        return False

    if list(reference) != list(candidate):
        sys.stderr.write("FINAL ORDER MISMATCH\n")
        return False

    return True


def runSameValueTest():
    reference = {}
    candidate = {}
    key = ("same",)
    sentinel = None

    for _ in range(1000):
        dict.__setitem__(reference, key, sentinel)
        candidate[key] = sentinel

    if not compareStates(reference, candidate, 1000):
        sys.stderr.write("SAME VALUE MISMATCH\n")
        return False

    return True


class SplitTableObject(object):
    pass


class CSplitTableObject(object):
    pass


def makeSplitObjectDict(seed_value, object_type):
    obj = object_type()
    setattr(obj, "seed", seed_value)
    instance_dict = obj.__dict__

    if getDictState(instance_dict)[0] != "split":
        sys.stderr.write("EXPECTED SPLIT DICT\n")
        return None, None

    return obj, instance_dict


def swapSplitDict(candidate, source):
    if py_version < (3, 6):
        dict_type = PyDictObject
    else:
        dict_type = PyDictObject610

    candidate_fields = ctypes.cast(id(candidate), ctypes.POINTER(dict_type)).contents
    source_fields = ctypes.cast(id(source), ctypes.POINTER(dict_type)).contents

    candidate_used = candidate_fields.ma_used
    candidate_keys = candidate_fields.ma_keys
    candidate_values = candidate_fields.ma_values

    candidate_fields.ma_used = source_fields.ma_used
    candidate_fields.ma_keys = source_fields.ma_keys
    candidate_fields.ma_values = source_fields.ma_values

    source_fields.ma_used = candidate_used
    source_fields.ma_keys = candidate_keys
    source_fields.ma_values = candidate_values


def runSplitTableTest():
    if py_version < (3, 4):
        return True

    seed_value = 0
    ref_obj, reference = makeSplitObjectDict(seed_value, SplitTableObject)
    cand_obj, candidate_source = makeSplitObjectDict(seed_value, SplitTableObject)

    if reference is None or candidate_source is None:
        return False

    source_target = {}
    source_target.update(candidate_source)
    source_expected = {}
    source_expected.update(reference)

    if not compareStates(source_expected, source_target, 0):
        sys.stderr.write("SPLIT SOURCE MERGE MISMATCH\n")
        return False

    # 3.13 and later store instance dictionary values inside the instance,
    # so the values pointer cannot be transferred to a local dictionary.
    if py_version >= (3, 13):
        return True

    candidate = {}
    swapSplitDict(candidate, candidate_source)

    if not compareStates(reference, candidate, 0):
        sys.stderr.write("SPLIT SWAP MISMATCH\n")
        return False

    sentinel = None

    for _ in range(1000):
        dict.__setitem__(reference, "seed", sentinel)
        candidate["seed"] = sentinel

    if not compareStates(reference, candidate, 1001):
        sys.stderr.write("SPLIT SAME VALUE MISMATCH\n")
        return False

    names = ["split_key_%d" % i for i in range(40)]

    for i, name in enumerate(names):
        value = i

        if i % 2:
            candidate[name] = value
            dict.__setitem__(reference, name, value)
        else:
            dict.__setitem__(reference, name, value)
            candidate[name] = value

        if not compareStates(reference, candidate, i + 1):
            sys.stderr.write("SPLIT INSERT MISMATCH: %s\n" % name)
            return False

    for i in range(0, len(names), 3):
        name = names[i]
        value = i * 10
        dict.__setitem__(reference, name, value)
        candidate[name] = value

        if not compareStates(reference, candidate, i + 100):
            sys.stderr.write("SPLIT UPDATE MISMATCH: %s\n" % name)
            return False

    for i in range(0, len(names), 4):
        name = names[i]
        dict.__delitem__(reference, name)
        del candidate[name]

        if not compareStates(reference, candidate, i + 200):
            sys.stderr.write("SPLIT DELETE MISMATCH: %s\n" % name)
            return False

    source = {}

    for i in range(0, len(names), 5):
        source[names[i]] = i + 1000

    reference.update(source)
    candidate.update(source)

    if not compareStates(reference, candidate, 300):
        sys.stderr.write("SPLIT TARGET MERGE MISMATCH\n")
        return False

    pairs = [(names[i], i + 2000) for i in range(0, len(names), 7)]

    reference.update(pairs)
    candidate.update(pairs)

    if not compareStates(reference, candidate, 301):
        sys.stderr.write("SPLIT TARGET SEQUENCE MERGE MISMATCH\n")
        return False

    if reference != candidate:
        sys.stderr.write("FINAL SPLIT DICT MISMATCH\n")
        return False

    if list(reference) != list(candidate):
        sys.stderr.write("FINAL SPLIT ORDER MISMATCH\n")
        return False

    return True


def runCSplitTableTest():
    if py_version < (3, 4):
        return True

    set_item = globals().get("_nuitka_test_dict_set_item")
    remove_item = globals().get("_nuitka_test_dict_remove_item")
    update_from = globals().get("_nuitka_test_dict_update_from")
    update_from_seq = globals().get("_nuitka_test_dict_update_from_seq")

    if (
        set_item is None
        or remove_item is None
        or update_from is None
        or update_from_seq is None
    ):
        return True

    seed_value = 0
    ref_obj, reference = makeSplitObjectDict(seed_value, CSplitTableObject)
    cand_obj, candidate = makeSplitObjectDict(seed_value, CSplitTableObject)

    if reference is None or candidate is None:
        return False

    if not compareStates(reference, candidate, 0):
        sys.stderr.write("C SPLIT INITIAL MISMATCH\n")
        return False

    sentinel = None

    for _ in range(1000):
        dict.__setitem__(reference, "seed", sentinel)
        set_item(candidate, "seed", sentinel)

    if not compareStates(reference, candidate, 1001):
        sys.stderr.write("C SPLIT SAME VALUE MISMATCH\n")
        return False

    names = ["c_split_key_%d" % i for i in range(40)]

    for i, name in enumerate(names):
        value = i

        if i % 2:
            set_item(candidate, name, value)
            dict.__setitem__(reference, name, value)
        else:
            dict.__setitem__(reference, name, value)
            set_item(candidate, name, value)

        if not compareStates(reference, candidate, i + 1):
            sys.stderr.write("C SPLIT INSERT MISMATCH: %s\n" % name)
            return False

    for i in range(0, len(names), 3):
        name = names[i]
        value = i * 10
        dict.__setitem__(reference, name, value)
        set_item(candidate, name, value)

        if not compareStates(reference, candidate, i + 100):
            sys.stderr.write("C SPLIT UPDATE MISMATCH: %s\n" % name)
            return False

    for i in range(0, len(names), 4):
        name = names[i]
        dict.__delitem__(reference, name)
        remove_item(candidate, name)

        if not compareStates(reference, candidate, i + 200):
            sys.stderr.write("C SPLIT DELETE MISMATCH: %s\n" % name)
            return False

    source = {}

    for i in range(0, len(names), 5):
        source[names[i]] = i + 1000

    reference.update(source)
    update_from(candidate, source)

    if not compareStates(reference, candidate, 300):
        sys.stderr.write("C SPLIT TARGET MERGE MISMATCH\n")
        return False

    pairs = [(names[i], i + 2000) for i in range(0, len(names), 7)]

    reference.update(pairs)
    update_from_seq(candidate, pairs)

    if not compareStates(reference, candidate, 301):
        sys.stderr.write("C SPLIT TARGET SEQUENCE MERGE MISMATCH\n")
        return False

    if reference != candidate:
        sys.stderr.write("FINAL C SPLIT DICT MISMATCH\n")
        return False

    if list(reference) != list(candidate):
        sys.stderr.write("FINAL C SPLIT ORDER MISMATCH\n")
        return False

    return True


class MutatingKey(object):
    def __init__(self, source, name):
        self.source = source
        self.name = name
        self.armed = False

    def __hash__(self):
        return 7

    def __eq__(self, other):
        if self.armed and self.name == "a":
            self.armed = False
            del self.source[1]
            self.source[100] = 100

        return self is other


def runCloneTest():
    if py_version >= (3, 6):
        source = {1: 1}
        target = {}

        source_tag_before = getVersionTag(source)
        target_tag_before = getVersionTag(target)

        target.update(source)

        if source_tag_before is not None:
            if getVersionTag(source) != source_tag_before:
                sys.stderr.write("CLONE CHANGED SOURCE VERSION TAG\n")
                return False

            if getVersionTag(target) == target_tag_before:
                sys.stderr.write("CLONE DID NOT UPDATE TARGET VERSION TAG\n")
                return False

    if py_version < (3, 10):
        return True

    for size in (5, 100):
        source = {}

        for i in range(size):
            source[i] = i

        target = {}
        source_tag_before = getVersionTag(source)
        target_tag_before = getVersionTag(target)

        target.update(source)

        if target_tag_before is not None:
            if getVersionTag(source) != source_tag_before:
                sys.stderr.write("CLONE CHANGED SOURCE VERSION TAG\n")
                return False

            if getVersionTag(target) == target_tag_before:
                sys.stderr.write("CLONE DID NOT UPDATE TARGET VERSION TAG\n")
                return False

        source_state = getDictState(source)
        target_state = getDictState(target)

        if source_state != target_state:
            sys.stderr.write(
                "CLONE MISMATCH (%d entries)\nSOURCE: %s\nTARGET: %s\n"
                % (size, describe(source_state), describe(target_state))
            )
            return False

    return True


def runCCloneTest():
    update_from = globals().get("_nuitka_test_dict_update_from")

    if update_from is None or py_version < (3, 6):
        return True

    for size in (1, 5, 100):
        source = {}

        for i in range(size):
            source[i] = i

        target = {}
        update_from(target, source)

        if target != source:
            sys.stderr.write("C CLONE MISMATCH (%d entries)\n" % size)
            return False

        if getDictState(target) != getDictState(source):
            sys.stderr.write("C CLONE STATE MISMATCH (%d entries)\n" % size)
            return False

    return True


def runMutationTest():
    source = {}
    key_a = MutatingKey(source, "a")
    key_b = MutatingKey(source, "b")
    source[key_a] = "a"
    source[key_b] = "b"

    for i in range(10):
        source[i] = i

    key_a.armed = True
    target = {99: 99}
    mutated = False

    try:
        target.update(source)
    except RuntimeError as exception:
        if str(exception) != "dict mutated during update":
            sys.stderr.write("MUTATION WRONG ERROR: %s\n" % (exception,))
            return False

        mutated = True

    # CPython only has this mutation check on 3.6 through 3.12.
    expected_mutated = (3, 6) <= py_version < (3, 13)

    if mutated != expected_mutated:
        sys.stderr.write(
            "MUTATION MISMATCH: raised=%s expected=%s\n" % (mutated, expected_mutated)
        )
        return False

    return True


def runSubclassMergeTest():
    class TrickyDict(dict):
        def keys(self):
            return ["fake"]

        def __getitem__(self, key):
            return 99

    source = TrickyDict(real=1)
    expected = {"real": 1}

    if dict(source) != expected:
        sys.stderr.write("SUBCLASS CONSTRUCTOR MISMATCH: %r\n" % (dict(source),))
        return False

    target = {}
    target.update(source)

    if target != expected:
        sys.stderr.write("SUBCLASS UPDATE MISMATCH: %r\n" % (target,))
        return False

    return True


def main():
    operations = makeOperations()

    if not runOperations(operations):
        return 1

    if not runSubclassMergeTest():
        return 1

    if not runMutationTest():
        return 1

    if not runSameValueTest():
        return 1

    if not runSplitTableTest():
        return 1

    if not runCSplitTableTest():
        return 1

    if not runCloneTest():
        return 1

    if not runCCloneTest():
        return 1

    sys.stdout.write(
        "Dictionary structure test passed on Python %s (%d operations).\n"
        % (
            ".".join(str(part) for part in sys.version_info[:3]),
            len(operations),
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())

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
