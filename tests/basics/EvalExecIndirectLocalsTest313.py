#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-project: --experimental=force-locals-frame-proxy

"""Test indirect "eval" accessing locals of compiled frames."""

import builtins
import gc
import sys


def eval_local(convert):
    value = 21

    return convert("value * 2")


def exec_local(convert):
    value = 5

    convert("value = value + 1")

    return value


def frame_builtins():
    x = 1
    y = 2

    return sorted(builtins.locals()), sorted(builtins.vars()), builtins.dir()


print("eval-local", eval_local(eval))
print("exec-local", exec_local(exec))
print("frame-builtins", frame_builtins())


def closure_frame_gc():
    value = []

    def inner():
        gc.collect()
        return value

    return inner


print("closure-frame-gc", closure_frame_gc()())


def test_frame_locals_proxy_update():
    a = 1
    flp = sys._getframe().f_locals

    # Plain dict update
    flp.update({"a": 2, "extra": 10})
    print("update-plain", a, flp.get("extra"))

    # Dict subclass overriding items() with non-tuple/short-tuple results, plus
    # keys() and __getitem__(): CPython uses keys() + __getitem__(), never items().
    class SubDictBadItems(dict):
        def items(self):
            print("SubDictBadItems.items called")
            return [42, ()]

        def keys(self):
            print("SubDictBadItems.keys called")
            return ["a", "sub_extra"]

        def __getitem__(self, key):
            print("SubDictBadItems.__getitem__ called", key)
            return super().__getitem__(key) + 100

    flp.update(SubDictBadItems(a=5, sub_extra=7))
    print("update-subdict", a, flp.get("sub_extra"))

    # In-place |= with the same dict subclass
    flp |= SubDictBadItems(a=6, sub_extra=8)
    print("ior-subdict", a, flp.get("sub_extra"))

    # Dict subclass overriding only __getitem__() (not keys())
    class SubDictGetItemOnly(dict):
        def __getitem__(self, key):
            print("SubDictGetItemOnly.__getitem__ called", key)
            return super().__getitem__(key) + 10

    flp.update(SubDictGetItemOnly(a=2, only_extra=3))
    print("update-subdict-getitem", a, flp.get("only_extra"))

    # Dict subclass whose keys() returns a generator
    class SubDictGenKeys(dict):
        def keys(self):
            yield "a"
            yield "gen_extra"

    flp.update(SubDictGenKeys(a=20, gen_extra=30))
    print("update-subdict-genkeys", a, flp.get("gen_extra"))

    # Self-update (update and |=)
    flp.update(flp)
    flp |= flp
    print("update-self", a, flp.get("gen_extra"))

    # Update from another live compiled FrameLocalsProxy
    def update_from_other_proxy(target_flp):
        a = 123
        other_local = 456
        other_flp = sys._getframe().f_locals
        other_flp["other_extra"] = 789

        target_flp.update(other_flp)
        print(
            "update-other-proxy",
            target_flp["a"],
            target_flp.get("other_local"),
            target_flp.get("other_extra"),
        )

        other_flp["other_extra"] = 790
        target_flp |= other_flp
        print("ior-other-proxy", target_flp["a"], target_flp.get("other_extra"))

    update_from_other_proxy(flp)
    print("after-other-proxy", a, flp.get("other_local"), flp.get("other_extra"))

    # Update from an uncompiled (exec) CPython FrameLocalsProxy
    exec_ns = {"sys": sys}
    exec(
        "def make_exec_proxy():\n"
        "    a = 321\n"
        "    exec_local = 654\n"
        "    return sys._getframe().f_locals\n",
        exec_ns,
    )
    exec_flp = exec_ns["make_exec_proxy"]()
    flp.update(exec_flp)
    print("update-exec-proxy", a, flp.get("exec_local"))

    flp |= exec_flp
    print("ior-exec-proxy", a, flp.get("exec_local"))

    # Exact dict mutated during update via key __eq__
    mut_dict = {}

    class MutatorKey:
        def __hash__(self):
            return hash("a")

        def __eq__(self, other):
            for i in range(10):
                mut_dict["added_%d" % i] = i
            return False

    mut_dict[MutatorKey()] = 1
    mut_dict["after_mut"] = 2
    flp.update(mut_dict)
    print("update-mutated-dict", "after_mut" in flp, "added_0" in flp)

    # Invalid argument types for update() and |=
    class CustomMapping:
        def keys(self):
            return ["a"]

        def __getitem__(self, key):
            return 999

    for label, bad in (
        ("int", 123),
        ("list", [("a", 1)]),
        ("custom-mapping", CustomMapping()),
    ):
        try:
            flp.update(bad)
        except Exception as exc:
            print("update-bad", label, type(exc).__name__, str(exc))

        try:
            flp |= bad
        except Exception as exc:
            print("ior-bad", label, type(exc).__name__, str(exc))


test_frame_locals_proxy_update()

#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
