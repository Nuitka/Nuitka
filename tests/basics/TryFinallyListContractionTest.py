#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Cover list comprehensions in cloned try/finally final blocks."""

from __future__ import print_function


def run(flag):
    try:
        if flag:
            return "returned"

        print("body")
    finally:
        values = [x for x in range(3)]
        print("finally", values)


print(run(False))
print(run(True))
