#!/usr/bin/env python
"""Simple test script to verify source code caching works."""


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
