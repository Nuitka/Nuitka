import os
import sys

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

from nuitka.tools.testing.Common import executeReferenceChecked


def simpleFunction1():
    print([*i for i in [[1, 2, 3], [4, 5, 6]]])
    print({*i for i in [[1, 2, 3], [4, 5, 6]]})
    print(list((*i for i in [[1, 2, 3], [4, 5, 6]])))
    print({**a for a in [{1: 2}, {3: 4}]})


# These need stderr to be wrapped.
tests_stderr = ()

# Disabled tests
tests_skipped = {}

result = executeReferenceChecked(
    prefix="simpleFunction",
    names=globals(),
    tests_skipped=tests_skipped,
    tests_stderr=tests_stderr,
    explain=False,
)

print("OK." if result else "FAIL.")
sys.exit(0 if result else 1)
