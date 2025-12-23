#!/usr/bin/env python
"""Automated verification script for AST caching behavior.

This script programmatically verifies that AST caching works correctly by:
1. Compiling test_caching.py twice
2. Parsing compilation output to extract cache statistics
3. Asserting expected cache hit/miss behavior

Run this with: python test_caching_verification.py
"""

import os
import re
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path


def run_nuitka_compile(test_file, remove_output=True):
    """Run Nuitka compilation and capture output.

    Returns:
        tuple: (returncode, stdout, stderr)
    """
    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--module",
        test_file,
    ]
    if remove_output:
        cmd.append("--remove-output")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def parse_cache_stats(output):
    """Parse cache statistics from Nuitka output.

    Returns:
        dict: {'hits': int, 'misses': int, 'hit_rate': float} or None if not found
    """
    # Look for: "Source AST cache: X hits, Y misses (Z% hit rate)"
    pattern = r"Source AST cache: (\d+) hits?, (\d+) misses? \(([\d.]+)% hit rate\)"
    match = re.search(pattern, output)

    if match:
        return {
            'hits': int(match.group(1)),
            'misses': int(match.group(2)),
            'hit_rate': float(match.group(3)),
        }
    return None


def test_cache_miss_then_hit():
    """Test that first compile misses cache, second compile hits cache."""
    test_file = "test_caching.py"

    if not os.path.exists(test_file):
        print(f"ERROR: {test_file} not found in current directory")
        return False

    # Clear AST cache to ensure clean state
    print("Clearing AST cache...")
    try:
        from nuitka.utils.AppDirs import getCacheDir
        cache_dir = getCacheDir("source-ast-cache")
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            print(f"  Cleared: {cache_dir}")
    except Exception as e:
        print(f"  Warning: Could not clear cache: {e}")

    # First compilation - expect cache miss
    print("\n1. First compilation (expecting cache miss)...")
    returncode, stdout, stderr = run_nuitka_compile(test_file)

    if returncode != 0:
        print(f"ERROR: First compilation failed with code {returncode}")
        print("STDERR:", stderr)
        return False

    output = stdout + stderr
    stats1 = parse_cache_stats(output)

    if stats1 is None:
        print("ERROR: Could not parse cache statistics from first compilation")
        print("Output:", output[-500:])
        return False

    print(f"  Cache stats: {stats1['hits']} hits, {stats1['misses']} misses")

    if stats1['misses'] == 0:
        print("ERROR: Expected at least 1 cache miss on first compilation")
        return False

    if stats1['hits'] != 0:
        print("WARNING: Expected 0 cache hits on first compilation, got", stats1['hits'])

    # Second compilation - expect cache hit
    print("\n2. Second compilation (expecting cache hit)...")
    returncode, stdout, stderr = run_nuitka_compile(test_file)

    if returncode != 0:
        print(f"ERROR: Second compilation failed with code {returncode}")
        print("STDERR:", stderr)
        return False

    output = stdout + stderr
    stats2 = parse_cache_stats(output)

    if stats2 is None:
        print("ERROR: Could not parse cache statistics from second compilation")
        print("Output:", output[-500:])
        return False

    print(f"  Cache stats: {stats2['hits']} hits, {stats2['misses']} misses")

    if stats2['hits'] == 0:
        print("ERROR: Expected at least 1 cache hit on second compilation")
        return False

    if stats2['misses'] != 0:
        print("WARNING: Expected 0 cache misses on second compilation, got", stats2['misses'])

    if stats2['hit_rate'] != 100.0:
        print("WARNING: Expected 100% hit rate on second compilation, got", stats2['hit_rate'])

    print("\n[PASS] Cache behavior verified successfully!")
    print(f"  - First run: {stats1['misses']} miss(es)")
    print(f"  - Second run: {stats2['hits']} hit(s), {stats2['hit_rate']}% hit rate")
    return True


def test_source_modification_invalidates_cache():
    """Test that modifying source code invalidates the cache."""
    test_file = "test_caching.py"

    if not os.path.exists(test_file):
        print(f"ERROR: {test_file} not found")
        return False

    # Create a backup
    backup_file = test_file + ".backup"
    shutil.copy2(test_file, backup_file)

    try:
        # First compilation
        print("\n3. First compilation of original source...")
        returncode, stdout, stderr = run_nuitka_compile(test_file)
        if returncode != 0:
            print(f"ERROR: Compilation failed")
            return False

        # Modify the source file
        print("\n4. Modifying source code...")
        with open(test_file, 'a', encoding='utf-8') as f:
            f.write('\n# Modified to test cache invalidation\n')

        # Compile modified version
        print("\n5. Compiling modified source (expecting cache miss)...")
        returncode, stdout, stderr = run_nuitka_compile(test_file)
        if returncode != 0:
            print(f"ERROR: Compilation of modified source failed")
            return False

        output = stdout + stderr
        stats = parse_cache_stats(output)

        if stats is None:
            print("ERROR: Could not parse cache statistics")
            return False

        print(f"  Cache stats: {stats['hits']} hits, {stats['misses']} misses")

        if stats['misses'] == 0:
            print("ERROR: Expected cache miss after source modification")
            return False

        print("\n[PASS] Source modification correctly invalidates cache")
        return True

    finally:
        # Restore original file
        shutil.move(backup_file, test_file)


def test_corrupt_cache_handling():
    """Test that corrupt cache files are handled gracefully."""
    test_file = "test_caching.py"

    if not os.path.exists(test_file):
        print(f"ERROR: {test_file} not found")
        return False

    try:
        from nuitka.utils.AppDirs import getCacheDir
        cache_dir = getCacheDir("source-ast-cache")
    except Exception as e:
        print(f"Warning: Could not get cache dir: {e}")
        return True  # Skip test if we can't access cache

    # First compilation to create cache
    print("\n6. Creating cache...")
    returncode, stdout, stderr = run_nuitka_compile(test_file)
    if returncode != 0:
        print(f"ERROR: Initial compilation failed")
        return False

    # Find cache files
    if not os.path.exists(cache_dir):
        print("Warning: Cache directory doesn't exist, skipping corrupt cache test")
        return True

    pkl_files = list(Path(cache_dir).glob("*.pkl"))
    json_files = list(Path(cache_dir).glob("*.json"))

    if not pkl_files:
        print("Warning: No cache files found, skipping corrupt cache test")
        return True

    # Corrupt a cache file
    print("\n7. Corrupting cache file...")
    corrupt_file = pkl_files[0]
    with open(corrupt_file, 'wb') as f:
        f.write(b"CORRUPTED DATA")

    # Try to compile again - should handle corruption gracefully
    print("\n8. Compiling with corrupt cache (expecting graceful handling)...")
    returncode, stdout, stderr = run_nuitka_compile(test_file)

    if returncode != 0:
        print(f"ERROR: Compilation with corrupt cache failed (should handle gracefully)")
        return False

    print("\n[PASS] Corrupt cache handled gracefully (compilation succeeded)")
    return True


def main():
    """Run cache verification tests."""
    print("=" * 70)
    print("AST Cache Verification Tests")
    print("=" * 70)

    # Change to Nuitka directory if script is run from there
    script_dir = Path(__file__).parent
    if (script_dir / "test_caching.py").exists():
        os.chdir(script_dir)

    # Run all tests
    all_passed = True

    all_passed &= test_cache_miss_then_hit()
    all_passed &= test_source_modification_invalidates_cache()
    all_passed &= test_corrupt_cache_handling()

    print("\n" + "=" * 70)
    if all_passed:
        print("RESULT: [PASS] All cache verification tests passed")
        print("=" * 70)
        return 0
    else:
        print("RESULT: [FAIL] Some cache verification tests FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
