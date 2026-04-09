#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

"""Exercise cleanup after exact list add MemoryError."""

import gc
import resource


def current_vm_bytes():
    with open("/proc/self/status", "r", encoding="utf-8") as status_file:
        for line in status_file:
            if line.startswith("VmSize:"):
                return int(line.split()[1]) * 1024

    raise RuntimeError("VmSize not found")


def churn_dict_items(rounds):
    for _ in range(rounds):
        tuple({"left": 1, "right": 2}.items())
        gc.collect(1)


gc.set_threshold(1, 1, 1)

a = [None] * 2_000_000
b = [None] * 2_000_000

churn_dict_items(16)

current_vm = current_vm_bytes()
resource.setrlimit(
    resource.RLIMIT_AS,
    (current_vm + 1024 * 1024, current_vm + 1024 * 1024),
)

try:
    _ = a + b
except MemoryError:
    print("memory-error")

    del a
    del b

    gc.collect()
    churn_dict_items(128)

    print("post-gc-ok")
else:
    print("concat-succeeded")
