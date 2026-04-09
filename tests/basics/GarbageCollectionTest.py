#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

"""Exercise cleanup after exact list add MemoryError."""

# nuitka-skip-unless-expression: sys.platform.startswith("linux") and os.path.exists("/proc/self/status") and hasattr(__import__("resource"), "RLIMIT_AS")

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


def exercise_list_add_memory_error(name, inplace):
    gc.set_threshold(1, 1, 1)

    a = [None] * 2_000_000
    b = [None] * 2_000_000

    churn_dict_items(16)

    current_vm = current_vm_bytes()
    old_soft_limit, old_hard_limit = resource.getrlimit(resource.RLIMIT_AS)
    target_soft_limit = current_vm + 1024 * 1024

    if old_hard_limit not in (-1, resource.RLIM_INFINITY):
        target_soft_limit = min(target_soft_limit, old_hard_limit)

    resource.setrlimit(resource.RLIMIT_AS, (target_soft_limit, old_hard_limit))

    try:
        try:
            if inplace:
                a += b
            else:
                _ = a + b
        except MemoryError:
            print(name, "memory-error")

            del a
            del b

            gc.collect()
            churn_dict_items(128)

            print(name, "post-gc-ok")
        else:
            print(name, "concat-succeeded")
    finally:
        resource.setrlimit(resource.RLIMIT_AS, (old_soft_limit, old_hard_limit))


exercise_list_add_memory_error("add", inplace=False)
exercise_list_add_memory_error("iadd", inplace=True)
