#!/usr/bin/env python
"""Manual verification script for AST source code caching.

This module is used to manually verify that the AST caching feature works correctly.
It is NOT part of the automated test suite.

To test caching:
1. Compile this module:
   python -m nuitka --module test_caching.py --remove-output
   Expected output: "Source AST cache: 0 hits, 1 misses"

2. Compile again without changes:
   python -m nuitka --module test_caching.py --remove-output
   Expected output: "Source AST cache: 1 hits, 0 misses (100.0% hit rate)"

3. Modify this file and recompile:
   Expected output: "Source AST cache: 0 hits, 1 misses" (new cache entry)

TODO: Convert this into proper automated tests that integrate with Nuitka's test
infrastructure (tests/basics/ or similar). Automated tests should verify:
- First compilation creates cache files
- Second compilation uses cached AST (cache hit)
- Modified source invalidates cache (cache miss)
- Cache statistics are accurate
"""


def hello():
    """Print a greeting."""
    print("Hello from cached module!")


def add(a, b):
    """Add two numbers."""
    return a + b


def main():
    """Main function."""
    hello()
    result = add(5, 3)
    print(f"5 + 3 = {result}")


if __name__ == "__main__":
    main()
