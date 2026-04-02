"""Standalone regression test for multiprocessing forkserver worker start."""

# nuitka-project: --mode=standalone

# nuitka-skip-unless-expression: os.name != "nt"

from __future__ import print_function

import multiprocessing as mp


def poolTask(value):
    return value + 1


if __name__ == "__main__":
    context = mp.get_context("forkserver")
    pool = context.Pool(1)

    try:
        async_result = pool.apply_async(poolTask, (9,))
        result = async_result.get(timeout=10)
    finally:
        pool.close()
        pool.join()

    assert result == 10, result
    print("OK")
