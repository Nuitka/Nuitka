#!/usr/bin/env python
"""Test module for AST source code caching verification.

This module serves as the test subject for AST caching verification.
Run test_caching_verification.py to programmatically test cache behavior.

Manual testing:
1. First compile:
   python -m nuitka --module test_caching.py --remove-output
   Expected: "Source AST cache: 0 hits, 1 misses"

2. Second compile (unchanged):
   python -m nuitka --module test_caching.py --remove-output
   Expected: "Source AST cache: 1 hits, 0 misses (100.0% hit rate)"

Automated testing:
   python test_caching_verification.py

This script runs comprehensive cache verification tests:
1. Cache miss/hit behavior: First compile misses, second hits (100%)
2. Cache invalidation: Modified source triggers cache miss
3. Error handling: Corrupt cache files handled gracefully

All tests include concrete assertions and exit code reporting for CI/CD.

TODO: Integrate into Nuitka's test infrastructure (tests/basics/ or similar)
for full CI/CD pipeline execution.
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
