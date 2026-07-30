#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Optional module frontend cache for compiled Python modules.

Caches generated module C sources and matching '.const' payloads so that
repeated compilations of unchanged non-main modules can skip C source
generation. Higher experimental levels also skip local optimize work and,
eventually, AST construction:

- '--enable-module-frontend-cache': L0 restore/store of module C/.const
- '--experimental=module-frontend-skip-optimize': L1/L2 skip computeModule
  with used-modules replay, process index, and global import verification
- '--experimental=module-frontend-stub': L3 no-AST stub modules that only
  register dependency edges and restore cached C

This feature is opt-in and must not change behavior when disabled.
"""

import os
import re
import sys

from nuitka.importing.Importing import locateModule, makeModuleUsageAttempt
from nuitka.options.Options import (
    getCompilationMode,
    getFileReferenceMode,
    isExperimental,
    isStandaloneMode,
    shallDisableCacheUsage,
    shallMakeModule,
)
from nuitka.plugins.Hooks import getPluginsCacheContributionValues
from nuitka.Tracing import cache_logger
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import (
    copyFile,
    copyFileIfChanged,
    getNormalizedPathJoin,
    makePath,
    replaceFileAtomic,
)
from nuitka.utils.Hashing import Hash, getStringHash
from nuitka.utils.Json import loadJsonFromFilename, writeJsonToFilename
from nuitka.utils.ModuleNames import ModuleName
from nuitka.Version import version_string

# Bump when meta schema or key ingredients change.
# v2: source+context key, used_modules in meta
# v3: index, helper arities, external symbol refs, stub support
# Note: call-helper replay for POS_ARGS/KW_SPLIT/VECTORCALL is fixed in
# _registerHelpersFromMetaOrC via C scan and is additive in meta; do not bump
# solely for that or warm cache keys will all miss.
_cache_format_version = 3

_CACHE_BASENAME = "module-frontend"

# Codegen path result -> count
_stats = {
    "hit": 0,
    "miss": 0,
    "store": 0,
    "bypass": 0,
    "invalid": 0,
    "stub": 0,
}

# Optimize-skip path result -> count
_optimize_stats = {
    "skip": 0,
    "full": 0,
    "probe_miss": 0,
    "probe_bypass": 0,
    "probe_invalid": 0,
    "feature_off": 0,
    "stub": 0,
}

# module_name(str) -> dict(result=, reason=) for codegen
_module_results = {}

# module_name(str) -> dict(result=, reason=) for optimize skip
_optimize_module_results = {}

# module_name(str) set: modules whose computeModule was skipped this run
_optimize_skipped_modules = set()

# module_name(str) set: modules built as L3 stubs (no AST)
_stub_modules = set()

# L1: memo of optimize-skip decisions for this process
# module_name(str) -> bool
_skip_decision_memo = {}

# L1: shared locate cache used during import verification
# module_name(str) -> (module_kind, finding)
_locate_cache = {}

# Side data for modules (they use __slots__, cannot attach attrs).
# module_name(str) -> meta dict / paths dict / cache_key
_module_meta = {}
_module_paths = {}
_module_cache_keys = {}

# L1: in-memory context index: module_name -> entry dict
_index_by_module = None
_index_context_hash = None
_index_dirty = False

# Short helper name -> factory callable. Built lazily once per process.
_internal_helper_factories = None

# Short names that could not be materialized during reconcile (hard error later).
_failed_internal_helpers = set()

# Regex helpers for scanning generated C.
# Order matters for ARGS*: match longer suffixes before bare WITH_ARGS{n}.
_re_call_args_kw_split = re.compile(r"\bCALL_FUNCTION_WITH_ARGS(\d+)_KW_SPLIT\b")
_re_call_args_vectorcall = re.compile(r"\bCALL_FUNCTION_WITH_ARGS(\d+)_VECTORCALL\b")
_re_call_args = re.compile(r"\bCALL_FUNCTION_WITH_ARGS(\d+)\b")
_re_call_pos_args_kw_split = re.compile(
    r"\bCALL_FUNCTION_WITH_POS_ARGS(\d+)_KW_SPLIT\b"
)
_re_call_pos_args = re.compile(r"\bCALL_FUNCTION_WITH_POS_ARGS(\d+)\b")
_re_call_no_args_kw_split = re.compile(r"\bCALL_FUNCTION_WITH_NO_ARGS_KW_SPLIT\b")
_re_instance_call_args = re.compile(r"\bCALL_METHOD_WITH_ARGS(\d+)\b")
_re_external_impl = re.compile(
    r"\b(_?impl_([A-Za-z0-9_]+?)\$\$\$(?:function|helper_function|class|generator|coroutine|asyncgen)_[A-Za-z0-9_]+)\b"
)


def getModuleFrontendCacheDir(create=True):
    """Return the module-frontend cache root directory.

    Args:
        create: If True, create the directory when missing.

    Returns:
        str: Absolute cache directory path.
    """
    return getCacheDir(_CACHE_BASENAME, create=create)


def getModuleFrontendCacheStats():
    """Return a copy of codegen-path cache counters."""
    return dict(_stats)


def getModuleFrontendCacheModuleResults():
    """Return per-module codegen cache results for this process."""
    return dict(_module_results)


def getModuleFrontendOptimizeSkipStats():
    """Return a copy of optimize-skip path counters."""
    return dict(_optimize_stats)


def getModuleFrontendOptimizeSkipModuleResults():
    """Return per-module optimize-skip results for this process."""
    return dict(_optimize_module_results)


def wasModuleOptimizeSkipped(module):
    """Return whether local optimize was skipped for 'module' this run.

    Args:
        module: Compiled module node.
    """
    return module.getFullName().asString() in _optimize_skipped_modules


def isModuleFrontendStub(module):
    """Return whether 'module' was built as an L3 no-AST stub.

    Args:
        module: Compiled module node.
    """
    return module.getFullName().asString() in _stub_modules


def markModuleFrontendStub(module):
    """Record 'module' as an L3 stub and mark it optimize-skipped.

    Args:
        module: Compiled module node.
    """
    _stub_modules.add(module.getFullName().asString())
    # Stubs always count as optimize-skipped for store guards.
    _optimize_skipped_modules.add(module.getFullName().asString())


def _setModuleCacheData(module_name_str, meta, paths, cache_key):
    """Attach cache side data for a module name.

    Args:
        module_name_str: Module full name as string.
        meta: Validated meta dict.
        paths: Cache path dict for this entry.
        cache_key: Opaque cache key string.
    """
    _module_meta[module_name_str] = meta
    _module_paths[module_name_str] = paths
    if cache_key is not None:
        _module_cache_keys[module_name_str] = cache_key


def _getModuleMeta(module):
    """Return attached meta for 'module', or None."""
    return _module_meta.get(module.getFullName().asString())


def _getModulePaths(module):
    """Return attached cache paths for 'module', or None."""
    return _module_paths.get(module.getFullName().asString())


def resetModuleFrontendCacheStats():
    """Clear process-local MCC stats, memos, and side tables."""
    for key in _stats:
        _stats[key] = 0
    for key in _optimize_stats:
        _optimize_stats[key] = 0
    _module_results.clear()
    _optimize_module_results.clear()
    _optimize_skipped_modules.clear()
    _stub_modules.clear()
    _skip_decision_memo.clear()
    _locate_cache.clear()
    _module_meta.clear()
    _module_paths.clear()
    _module_cache_keys.clear()
    _failed_internal_helpers.clear()

    global _index_by_module, _index_context_hash, _index_dirty
    global _internal_helper_factories
    _index_by_module = None
    _index_context_hash = None
    _index_dirty = False
    _internal_helper_factories = None


def _record(module_name, result, reason):
    """Record a codegen-path cache outcome.

    Args:
        module_name: ModuleName instance.
        result: Outcome key such as 'hit' or 'miss'.
        reason: Short reason string.
    """
    _stats[result] = _stats.get(result, 0) + 1
    _module_results[module_name.asString()] = {
        "result": result,
        "reason": reason,
    }


def _recordOptimize(module_name, result, reason):
    """Record an optimize-skip path outcome.

    Args:
        module_name: ModuleName instance.
        result: Outcome key such as 'skip' or 'probe_miss'.
        reason: Short reason string.
    """
    _optimize_stats[result] = _optimize_stats.get(result, 0) + 1
    _optimize_module_results[module_name.asString()] = {
        "result": result,
        "reason": reason,
    }


def _isFeatureEnabled():
    """Return whether the module-frontend cache feature is active."""
    from nuitka.options.Options import shallUseModuleFrontendCache

    if not shallUseModuleFrontendCache():
        return False

    # Honors both "module-frontend" and "all".
    if shallDisableCacheUsage(_CACHE_BASENAME):
        return False

    return True


def _isSkipOptimizeEnabled():
    """Return whether skip-optimize or stub experimental mode is active."""
    return _isFeatureEnabled() and (
        isExperimental("module-frontend-skip-optimize")
        or isExperimental("module-frontend-stub")
    )


def _isStubEnabled():
    """Return whether L3 stub experimental mode is active."""
    return _isFeatureEnabled() and isExperimental("module-frontend-stub")


def _getContextHash(module_name):
    """Hash of toolchain / options / plugins that affect module frontend output.

    Args:
        module_name: ModuleName used for plugin cache contributions.
    """
    hash_value = Hash()

    hash_value.updateFromValues(
        version_string,
        sys.version,
        str(sys.version_info),
        getCompilationMode(),
        "standalone" if isStandaloneMode() else "not-standalone",
        "module-mode" if shallMakeModule() else "not-module-mode",
        getFileReferenceMode() or "",
    )

    hash_value.updateFromValues(*getPluginsCacheContributionValues(module_name))

    return hash_value.asHexDigest()


def _getSharedContextHash():
    """Context hash without per-module plugin contribution (for index file)."""
    hash_value = Hash()
    hash_value.updateFromValues(
        version_string,
        sys.version,
        str(sys.version_info),
        getCompilationMode(),
        "standalone" if isStandaloneMode() else "not-standalone",
        "module-mode" if shallMakeModule() else "not-module-mode",
        getFileReferenceMode() or "",
        _cache_format_version,
    )
    return hash_value.asHexDigest()


def _indexPath():
    """Return the on-disk path of the context-specific MCC index."""
    return getNormalizedPathJoin(
        getModuleFrontendCacheDir(create=True),
        "index-%s.json" % _getSharedContextHash(),
    )


def _ensureIndexLoaded():
    """Load the process index for the current shared context if needed."""
    global _index_by_module, _index_context_hash

    context_hash = _getSharedContextHash()
    if _index_by_module is not None and _index_context_hash == context_hash:
        return

    _index_context_hash = context_hash
    _index_by_module = {}

    path = _indexPath()
    if not os.path.isfile(path):
        return

    data = loadJsonFromFilename(filename=path)
    if data is None:
        return

    if data.get("file_format_version") != _cache_format_version:
        return

    if data.get("context_hash") != context_hash:
        return

    modules = data.get("modules") or {}
    if type(modules) is dict:
        _index_by_module = modules


def _updateIndexEntry(module_name_str, entry):
    """Update the in-memory index entry and mark the index dirty.

    Args:
        module_name_str: Module full name as string.
        entry: Serializable index entry dict.
    """
    global _index_dirty

    _ensureIndexLoaded()
    _index_by_module[module_name_str] = entry
    _index_dirty = True


def flushModuleFrontendCacheIndex():
    """Persist the in-memory module-frontend index if dirty."""
    global _index_dirty

    if not _index_dirty or _index_by_module is None:
        return

    path = _indexPath()
    tmp = path + ".tmp"
    data = {
        "file_format_version": _cache_format_version,
        "context_hash": _getSharedContextHash(),
        "modules": _index_by_module,
    }

    try:
        writeJsonToFilename(filename=tmp, contents=data)
        replaceFileAtomic(source_path=tmp, dest_path=path)
        _index_dirty = False
    except (OSError, IOError) as e:
        cache_logger.warning("Failed to write module frontend index: %s" % e)


def _serializeUsedModules(module):
    """Return a stable list describing modules this module decided to use.

    Args:
        module: Compiled module node after usage collection.
    """
    result = []

    for used_module in module.getUsedModules():
        result.append(
            {
                "module_name": used_module.module_name.asString(),
                "finding": used_module.finding,
                "module_kind": used_module.module_kind,
                "reason": used_module.reason,
                "source_ref_line": used_module.source_ref.getLineNumber(),
                "level": used_module.level,
            }
        )

    # Deterministic order for hashing / stable meta.
    result.sort(
        key=lambda item: (
            item["module_name"],
            item["finding"] or "",
            item["module_kind"] or "",
            item["reason"] or "",
            item["source_ref_line"],
            item.get("level") or 0,
        )
    )
    return result


def _locateModuleCached(module_name):
    """Locate a module with process-local caching.

    Args:
        module_name: ModuleName to resolve.

    Returns:
        tuple: (module_kind, finding, filename)
    """
    key = module_name.asString()
    if key in _locate_cache:
        return _locate_cache[key]

    _name, _filename, module_kind, finding = locateModule(
        module_name=module_name,
        parent_package=None,
        level=0,
    )
    result = (module_kind, finding, _filename)
    _locate_cache[key] = result
    return result


def _verifyUsedModulesStillValid(used_modules_data):
    """Re-locate imports; return True only if resolution is unchanged.

    Notes:
        Used-module entries may have been discovered as relative imports. The
        stored module name is already the resolved absolute name, so re-check
        with absolute lookup (level=0). Attribute imports stored as not-found
        are kept for completeness but must not fail verification.
    """
    seen = set()

    for item in used_modules_data:
        used_module_name = ModuleName(item["module_name"])
        key = used_module_name.asString()

        # Duplicates are common (parent path edges); verify once per name.
        if key in seen:
            continue
        seen.add(key)

        # Attribute imports (e.g. "from fastapi import FastAPI") are recorded as
        # not-found / module_kind=None usage attempts.
        if item["finding"] in (None, "not-found") or item["module_kind"] is None:
            continue

        module_kind, finding, _filename = _locateModuleCached(
            module_name=used_module_name
        )

        # A previously resolvable import disappearing is a real miss.
        if finding in (None, "not-found") or module_kind is None:
            return False

        if module_kind != item["module_kind"]:
            return False

    return True


def _rebuildUsedModuleAttempts(module, used_modules_data):
    """Rebuild ModuleUsageAttempt objects from cached meta and re-locate files."""
    result = []
    source_ref = module.source_ref

    for item in used_modules_data:
        used_module_name = ModuleName(item["module_name"])
        finding = item["finding"]
        module_kind = item["module_kind"]

        filename = None
        if finding not in (None, "not-found") and module_kind is not None:
            located_kind, located_finding, located_filename = _locateModuleCached(
                used_module_name
            )
            if located_finding in (None, "not-found") or located_kind is None:
                # Keep not-found shape; considerUsedModules will skip filename=None.
                finding = "not-found"
                module_kind = None
                filename = None
            else:
                finding = located_finding
                module_kind = located_kind
                filename = located_filename

        line_number = item.get("source_ref_line") or 1
        attempt_ref = source_ref.atLineNumber(line_number)

        result.append(
            makeModuleUsageAttempt(
                module_name=used_module_name,
                filename=filename,
                module_kind=module_kind,
                finding=finding,
                level=item.get("level") or 0,
                source_ref=attempt_ref,
                reason=item.get("reason") or "import",
            )
        )

    return result


def _getModuleSourceForCacheKey(module):
    """Return source text for keying, or None if the module cannot be keyed safely.

    Notes:
        Some synthetic modules still look like compiled modules but do not have a
        readable on-disk source (e.g. generated helper modules). Those must bypass
        the frontend cache rather than crash while hashing.
    """
    # Prefer already-captured source if present on the node.
    source_code = getattr(module, "source_code", None)
    if source_code is not None:
        return source_code

    try:
        source_filename = module.getCompileTimeFilename()
    except Exception:  # pylint: disable=broad-except
        return None

    if not source_filename or not os.path.isfile(source_filename):
        return None

    try:
        return module.getSourceCode()
    except (OSError, IOError, ValueError):
        return None


def _eligibilityReason(module):
    """Return None if eligible for MCC, else a short reason string.

    Args:
        module: Compiled module node.
    """
    if not module.isCompiledPythonModule():
        return "not-compiled-python"

    if module.isMainModule() or module.isTopModule():
        return "main-or-top"

    if module.getCompilationMode() != "compiled":
        return "mode-%s" % module.getCompilationMode()

    # Note: modules with cross-used functions are still eligible. Cached C already
    # contains the needed cross-module decls from a prior full codegen. Skipping
    # them was the main reason expensive library modules never entered the cache.

    if not _getModuleSourceForCacheKey(module=module):
        return "no-source"

    return None


def _eligibilityReasonFromParts(module_name, is_top, is_main, source_code, mode):
    """Return eligibility failure reason from parts, or None if eligible.

    Args:
        module_name: ModuleName (unused, for symmetry/debug).
        is_top: Whether the module is a top module.
        is_main: Whether the module is the main module.
        source_code: Source text or empty.
        mode: Compilation mode string.
    """
    if is_main or is_top:
        return "main-or-top"
    if mode != "compiled":
        return "mode-%s" % mode
    if not source_code:
        return "no-source"
    return None


def makeModuleFrontendCacheKey(module):
    """Return cache key for a module based on source+context only.

    Args:
        module: Compiled module node.

    Returns:
        str or None: Opaque cache key, or None if ineligible.
    """
    if _eligibilityReason(module=module) is not None:
        return None

    module_name = module.getFullName()
    source_code = _getModuleSourceForCacheKey(module=module)

    return _makeCacheKeyFromSource(
        module_name=module_name,
        source_code=source_code,
        reason=module.reason or "",
    )


def _makeCacheKeyFromSource(module_name, source_code, reason):
    """Build an opaque cache key from source and compilation context.

    Args:
        module_name: ModuleName of the module.
        source_code: Full source text used for the key hash.
        reason: Module inclusion reason string.

    Returns:
        str: Cache key basename for the module entry.
    """
    key_hash = Hash()
    key_hash.updateFromValues(
        _cache_format_version,
        module_name.asString(),
        getStringHash(source_code),
        _getContextHash(module_name=module_name),
        reason or "",
    )
    return module_name.asLegalFilename() + "@" + key_hash.asHexDigest()


def _cachePaths(cache_key):
    """Return the on-disk path layout for a cache key.

    Args:
        cache_key: Opaque cache key string.

    Returns:
        dict: Paths for dir/meta/module_c/module_const.
    """
    cache_dir = getNormalizedPathJoin(getModuleFrontendCacheDir(create=True), cache_key)
    return {
        "dir": cache_dir,
        "meta": getNormalizedPathJoin(cache_dir, "meta.json"),
        "module_c": getNormalizedPathJoin(cache_dir, "module.c"),
        "module_const": getNormalizedPathJoin(cache_dir, "module.const"),
    }


def _loadValidatedMeta(module, cache_key):
    """Load meta.json and validate format/name/key/hashes/imports.

    Args:
        module: Compiled module node being validated.
        cache_key: Opaque cache key string.

    Returns:
        tuple(meta_dict, paths_dict) or (None, reason_str)
    """
    return _loadValidatedMetaForName(
        module_name=module.getFullName(),
        cache_key=cache_key,
        expected_module_name=module.getFullName().asString(),
    )


def _loadValidatedMetaForName(module_name, cache_key, expected_module_name):
    """Load and validate meta for a module name and cache key.

    Args:
        module_name: ModuleName used for context-sensitive checks.
        cache_key: Opaque cache key string.
        expected_module_name: Expected 'module_name' field in meta.

    Returns:
        tuple: (meta_dict, paths_dict) or (None, reason_str)
    """
    paths = _cachePaths(cache_key=cache_key)

    if not (
        os.path.isfile(paths["meta"])
        and os.path.isfile(paths["module_c"])
        and os.path.isfile(paths["module_const"])
    ):
        return None, "not-present"

    meta = loadJsonFromFilename(filename=paths["meta"])
    if meta is None:
        return None, "meta-unreadable"

    # Accept current format; older entries will rebuild on store.
    if meta.get("file_format_version") not in (2, 3, _cache_format_version):
        return None, "format-version"

    if meta.get("module_name") != expected_module_name:
        return None, "module-name"

    if meta.get("cache_key") != cache_key:
        return None, "key-mismatch"

    c_hash = Hash()
    c_hash.updateFromFile(paths["module_c"])
    if meta.get("c_hash") != c_hash.asHexDigest():
        return None, "c-hash"

    const_hash = Hash()
    const_hash.updateFromFile(paths["module_const"])
    if meta.get("const_hash") != const_hash.asHexDigest():
        return None, "const-hash"

    used_modules_data = meta.get("used_modules") or []
    if not _verifyUsedModulesStillValid(used_modules_data=used_modules_data):
        return None, "imports-changed"

    return meta, paths


def _scanModuleCArtifacts(module_c_path):
    """Extract helper arities and external impl symbol refs from module C.

    Notes:
        Call helper families map to CallCodes tracking sets:

        - 'CALL_FUNCTION_WITH_ARGS{n}' -> quick_calls_used
        - 'CALL_METHOD_WITH_ARGS{n}' -> quick_instance_calls_used
        - 'CALL_FUNCTION_WITH_POS_ARGS{n}' -> quick_tuple_calls_used
        - 'CALL_FUNCTION_WITH_ARGS{n}_KW_SPLIT' -> mixed (n, False, True)
        - 'CALL_FUNCTION_WITH_POS_ARGS{n}_KW_SPLIT' -> mixed (n, True, True)
        - 'CALL_FUNCTION_WITH_ARGS{n}_VECTORCALL' -> mixed (n, False, False)
        - 'CALL_FUNCTION_WITH_NO_ARGS_KW_SPLIT' -> mixed (0, False, True)

    Args:
        module_c_path: Path to module C source to scan.

    Returns:
        dict: Helper arity lists, mixed calls, and external impl symbols.
    """
    empty = {
        "quick_call_arities": [],
        "quick_instance_call_arities": [],
        "quick_tuple_call_arities": [],
        "quick_mixed_calls": [],
        "external_impl_symbols": [],
    }
    try:
        with open(module_c_path, "rb") as module_c_file:
            text = module_c_file.read().decode("latin1", "replace")
    except (OSError, IOError):
        return empty

    quick_calls = set()
    for match in _re_call_args.finditer(text):
        # Bare WITH_ARGS{n} only; KW_SPLIT/VECTORCALL suffixes also match
        # the prefix pattern but are owned by mixed-call tracking.
        start = match.start()
        end = match.end()
        suffix = text[end : end + 16]
        if suffix.startswith("_KW_SPLIT") or suffix.startswith("_VECTORCALL"):
            continue
        quick_calls.add(int(match.group(1)))

    instance_calls = set()
    for match in _re_instance_call_args.finditer(text):
        instance_calls.add(int(match.group(1)))

    tuple_calls = set()
    for match in _re_call_pos_args.finditer(text):
        end = match.end()
        suffix = text[end : end + 16]
        if suffix.startswith("_KW_SPLIT"):
            continue
        tuple_calls.add(int(match.group(1)))

    # (args_count, has_tuple_arg, has_dict_values) for getCallsCode()
    mixed_calls = set()
    for match in _re_call_args_kw_split.finditer(text):
        mixed_calls.add((int(match.group(1)), False, True))
    for match in _re_call_pos_args_kw_split.finditer(text):
        mixed_calls.add((int(match.group(1)), True, True))
    for match in _re_call_args_vectorcall.finditer(text):
        mixed_calls.add((int(match.group(1)), False, False))
    if _re_call_no_args_kw_split.search(text):
        # Template: args_count==0 and has_dict_values (tuple flag unused).
        mixed_calls.add((0, False, True))

    external = set()
    for match in _re_external_impl.finditer(text):
        symbol = match.group(1)
        owner_code = match.group(2)
        # Drop self-module symbols later; store all for consumers to filter.
        external.add((symbol, owner_code))

    return {
        "quick_call_arities": sorted(quick_calls),
        "quick_instance_call_arities": sorted(instance_calls),
        "quick_tuple_call_arities": sorted(tuple_calls),
        "quick_mixed_calls": [
            [args_count, has_tuple_arg, has_dict_values]
            for (args_count, has_tuple_arg, has_dict_values) in sorted(mixed_calls)
        ],
        "external_impl_symbols": [
            {"symbol": symbol, "owner_code_name": owner_code}
            for (symbol, owner_code) in sorted(external)
        ],
    }


def _metaHasCompleteCallHelperInfo(meta):
    """Return whether meta alone can replay all call-helper families.

    Notes:
        Older v3 entries only stored bare WITH_ARGS / METHOD arities and must
        still scan module C. Empty lists are valid (module needs no such
        helpers); missing keys mean incomplete.

    Args:
        meta: Cache meta dict or None.

    Returns:
        bool: True if all four helper-family keys are present.
    """
    if meta is None:
        return False

    return (
        meta.get("quick_call_arities") is not None
        and meta.get("quick_instance_call_arities") is not None
        and meta.get("quick_tuple_call_arities") is not None
        and meta.get("quick_mixed_calls") is not None
    )


def _applyCallHelpersToCodegen(arities, instance_arities, tuple_arities, mixed_calls):
    """Register high-arity call helpers into CallCodes tracking sets.

    Args:
        arities: Iterable of CALL_FUNCTION_WITH_ARGS arities.
        instance_arities: Iterable of CALL_METHOD_WITH_ARGS arities.
        tuple_arities: Iterable of CALL_FUNCTION_WITH_POS_ARGS arities.
        mixed_calls: Iterable of [args_count, has_tuple_arg, has_dict_values]
            or matching tuples for mixed/KW_SPLIT/VECTORCALL helpers.
    """
    from nuitka.code_generation.CallCodes import (
        max_quick_call,
        quick_calls_used,
        quick_instance_calls_used,
        quick_mixed_calls_used,
        quick_tuple_calls_used,
    )

    for arity in arities or ():
        arity = int(arity)
        if arity > max_quick_call:
            quick_calls_used.add(arity)

    for arity in instance_arities or ():
        arity = int(arity)
        if arity > max_quick_call:
            quick_instance_calls_used.add(arity)

    for arity in tuple_arities or ():
        arity = int(arity)
        if arity > max_quick_call:
            quick_tuple_calls_used.add(arity)

    for item in mixed_calls or ():
        args_count = int(item[0])
        has_tuple_arg = bool(item[1])
        has_dict_values = bool(item[2])
        if args_count > max_quick_call:
            quick_mixed_calls_used.add((args_count, has_tuple_arg, has_dict_values))


def _upgradeMetaCallHelpers(meta, paths, scanned):
    """Persist full helper families into meta after a C scan.

    Notes:
        Best-effort only: restore already succeeded. Uses atomic replace so a
        crashed upgrade cannot leave a truncated meta.json. Lets the next warm
        restore skip scanning this module's C.

    Args:
        meta: Mutable meta dict already used for this restore.
        paths: Cache path dict that must include 'meta'.
        scanned: Dict with the four helper-family lists to store.
    """
    if meta is None or paths is None:
        return

    meta_path = paths.get("meta")
    if not meta_path:
        return

    meta["quick_call_arities"] = scanned["quick_call_arities"]
    meta["quick_instance_call_arities"] = scanned["quick_instance_call_arities"]
    meta["quick_tuple_call_arities"] = scanned["quick_tuple_call_arities"]
    meta["quick_mixed_calls"] = scanned["quick_mixed_calls"]

    tmp_meta = meta_path + ".tmp"
    try:
        writeJsonToFilename(filename=tmp_meta, contents=meta)
        replaceFileAtomic(source_path=tmp_meta, dest_path=meta_path)
    except (OSError, IOError):
        # Restore already succeeded; upgrade is only a speed optimization.
        try:
            if os.path.isfile(tmp_meta):
                os.unlink(tmp_meta)
        except (OSError, IOError):
            pass


def _registerHelpersFromMetaOrC(meta, module_c_path, paths):
    """Replay high-arity call helper needs into codegen globals.

    Notes:
        Prefer complete meta (all four helper families) so warm restores do not
        re-read and regex-scan every cached 'module.c'. Incomplete or missing
        meta still scans C and best-effort upgrades meta so POS_ARGS / KW_SPLIT
        / VECTORCALL helpers are never dropped from '__helpers.c'.

    Args:
        meta: Cache meta dict, or None to force a C scan.
        module_c_path: Path to cached or restored module C source.
        paths: Cache path dict for optional meta upgrade, or None to skip
            upgrade writes.
    """
    if _metaHasCompleteCallHelperInfo(meta=meta):
        _applyCallHelpersToCodegen(
            arities=meta.get("quick_call_arities"),
            instance_arities=meta.get("quick_instance_call_arities"),
            tuple_arities=meta.get("quick_tuple_call_arities"),
            mixed_calls=meta.get("quick_mixed_calls"),
        )
        return

    scanned = _scanModuleCArtifacts(module_c_path=module_c_path)

    # Union partial meta + scan so incomplete meta cannot under-declare.
    arity_set = set()
    for arity in scanned["quick_call_arities"] or ():
        arity_set.add(int(arity))
    instance_set = set()
    for arity in scanned["quick_instance_call_arities"] or ():
        instance_set.add(int(arity))
    tuple_set = set()
    for arity in scanned["quick_tuple_call_arities"] or ():
        tuple_set.add(int(arity))
    mixed_list = list(scanned["quick_mixed_calls"] or ())

    if meta is not None:
        for arity in meta.get("quick_call_arities") or ():
            arity_set.add(int(arity))
        for arity in meta.get("quick_instance_call_arities") or ():
            instance_set.add(int(arity))
        if meta.get("quick_tuple_call_arities") is not None:
            for arity in meta.get("quick_tuple_call_arities") or ():
                tuple_set.add(int(arity))
        for item in meta.get("quick_mixed_calls") or ():
            mixed_list.append(item)

    # Dedup mixed while preserving list form for apply/upgrade.
    mixed_set = set()
    mixed_normalized = []
    for item in mixed_list:
        key = (int(item[0]), bool(item[1]), bool(item[2]))
        if key not in mixed_set:
            mixed_set.add(key)
            mixed_normalized.append([key[0], key[1], key[2]])

    arities = sorted(arity_set)
    instance_arities = sorted(instance_set)
    tuple_arities = sorted(tuple_set)
    mixed_for_meta = sorted(
        mixed_normalized, key=lambda item: (item[0], item[1], item[2])
    )

    _applyCallHelpersToCodegen(
        arities=arities,
        instance_arities=instance_arities,
        tuple_arities=tuple_arities,
        mixed_calls=mixed_for_meta,
    )

    # Make the next hit cheap if we had to scan.
    if meta is not None:
        scanned_for_meta = {
            "quick_call_arities": arities,
            "quick_instance_call_arities": instance_arities,
            "quick_tuple_call_arities": tuple_arities,
            "quick_mixed_calls": mixed_for_meta,
        }
        _upgradeMetaCallHelpers(meta=meta, paths=paths, scanned=scanned_for_meta)


def _registerHelpersFromCachedModuleC(module_c_path):
    """Register helpers by scanning module C when no meta is available.

    Args:
        module_c_path: Path to module C source to scan.
    """
    _registerHelpersFromMetaOrC(meta=None, module_c_path=module_c_path, paths=None)


def _prepareUsageTraceCollection(module, used_modules_data):
    """Attach a usage-only trace collection replayed from cached meta.

    Args:
        module: Compiled module node.
        used_modules_data: Serialized used-module list from meta.

    Returns:
        list: Rebuilt module usage attempts.
    """
    from nuitka.optimizations.TraceCollections import TraceCollectionModule

    module.trace_collection = TraceCollectionModule(
        module=module,
        very_trusted_module_variables={},
        old_collection=None,
    )
    attempts = _rebuildUsedModuleAttempts(
        module=module, used_modules_data=used_modules_data
    )
    module.trace_collection.onModuleUsageAttempts(attempts)
    return attempts


def _getInternalHelperFactories():
    """Return the registry of root-module internal helper factories.

    Notes:
        Keys are the Python helper short names used in generated C as
        'helper_function_<short_name>'. Values are the '@once_decorator'
        singleton factories that attach the body to the root module.
    """
    global _internal_helper_factories

    if _internal_helper_factories is not None:
        return _internal_helper_factories

    factories = {}

    # Import lazily so tree modules load after options are ready.
    from nuitka.tree.ComplexCallHelperFunctions import (
        getCallableNameDescBody,
        getFunctionCallHelperDictionaryUnpacking,
        getFunctionCallHelperKeywordsStarDict,
        getFunctionCallHelperKeywordsStarList,
        getFunctionCallHelperKeywordsStarListStarDict,
        getFunctionCallHelperPosKeywordsStarDict,
        getFunctionCallHelperPosKeywordsStarList,
        getFunctionCallHelperPosKeywordsStarListStarDict,
        getFunctionCallHelperPosStarDict,
        getFunctionCallHelperPosStarList,
        getFunctionCallHelperPosStarListStarDict,
        getFunctionCallHelperStarDict,
        getFunctionCallHelperStarList,
        getFunctionCallHelperStarListStarDict,
    )
    from nuitka.tree.ReformulationClasses3 import (
        getClassBasesMroConversionHelper,
        getClassSelectMetaClassHelper,
    )
    from nuitka.tree.ReformulationDictionaryCreation import (
        _getDictUnpackingHelper,
    )
    from nuitka.tree.ReformulationSequenceCreation import (
        getListUnpackingHelper,
        getSetUnpackingHelper,
    )

    factories.update(
        {
            "_mro_entries_conversion": getClassBasesMroConversionHelper,
            "_select_metaclass": getClassSelectMetaClassHelper,
            "_unpack_dict": _getDictUnpackingHelper,
            "_unpack_list": getListUnpackingHelper,
            "_unpack_set": getSetUnpackingHelper,
            "get_callable_name_desc": getCallableNameDescBody,
            "complex_call_helper_star_list": getFunctionCallHelperStarList,
            "complex_call_helper_keywords_star_list": getFunctionCallHelperKeywordsStarList,
            "complex_call_helper_pos_star_list": getFunctionCallHelperPosStarList,
            "complex_call_helper_pos_keywords_star_list": getFunctionCallHelperPosKeywordsStarList,
            "complex_call_helper_star_dict": getFunctionCallHelperStarDict,
            "complex_call_helper_pos_star_dict": getFunctionCallHelperPosStarDict,
            "complex_call_helper_keywords_star_dict": getFunctionCallHelperKeywordsStarDict,
            "complex_call_helper_pos_keywords_star_dict": getFunctionCallHelperPosKeywordsStarDict,
            "complex_call_helper_star_list_star_dict": getFunctionCallHelperStarListStarDict,
            "complex_call_helper_pos_star_list_star_dict": getFunctionCallHelperPosStarListStarDict,
            "complex_call_helper_keywords_star_list_star_dict": getFunctionCallHelperKeywordsStarListStarDict,
            "complex_call_helper_pos_keywords_star_list_star_dict": getFunctionCallHelperPosKeywordsStarListStarDict,
            "complex_call_helper_dict_unpacking_checks": getFunctionCallHelperDictionaryUnpacking,
        }
    )

    _internal_helper_factories = factories
    return factories


def _helperShortNameFromCodeName(function_code_name):
    """Convert 'helper_function_<name>' code name to short helper name.

    Args:
        function_code_name: Full function code name string.

    Returns:
        str or None: Short helper name, or None if not a helper code name.
    """
    if not function_code_name.startswith("helper_function_"):
        return None

    return function_code_name[len("helper_function_") :]


def _findFunctionBodyByCodeName(owner_module, function_code_name):
    """Locate a function body on owner by exact or suffix code-name match.

    Args:
        owner_module: Module that may own the function body.
        function_code_name: Exact or suffix code name to match.

    Returns:
        function body node or None
    """
    function_body = owner_module.getFunctionFromCodeName(function_code_name)
    if function_body is not None:
        return function_body

    for candidate_function in owner_module.subnode_functions:
        candidate_name = candidate_function.getCodeName()
        if (
            candidate_name == function_code_name
            or candidate_name.endswith(function_code_name)
            or function_code_name.endswith(candidate_name)
        ):
            return candidate_function

    return None


def _materializeInternalHelper(owner_module, helper_code_name):
    """Create a known internal helper on the root module if missing.

    Notes:
        Helpers such as '_mro_entries_conversion' live on the root/top module
        (code name '__main__') but are only constructed when some module's
        reformulation references them. L3 stubs never reformulate, so cached C
        may still reference helpers that were never built in this run.

        Factories are '@once_decorator' singletons and attach via
        'addFunction' on the root module. Unknown short names are recorded
        and later force a hard failure instead of an undefined-symbol link error.
    """
    short_name = _helperShortNameFromCodeName(function_code_name=helper_code_name)
    if short_name is None:
        return None

    # Already present under the Python helper name?
    for candidate_function in owner_module.subnode_functions:
        if candidate_function.getFunctionName() == short_name:
            return candidate_function

    factory = _getInternalHelperFactories().get(short_name)
    if factory is None:
        _failed_internal_helpers.add(short_name)
        cache_logger.warning(
            "Module frontend cache cannot materialize unknown internal helper "
            "'%s' on '%s'; disable stub/skip or report missing factory."
            % (short_name, owner_module.getFullName().asString())
        )
        return None

    helper_body = factory()
    return helper_body


def _collectNeededInternalHelperShortNames():
    """Collect root-module helper short names referenced by cached modules.

    Returns:
        set: Short helper names that must exist on the root module.
    """
    needed = set()

    for meta in _module_meta.values():
        if not meta:
            continue

        # Explicit list written at store time (preferred).
        for short_name in meta.get("internal_helpers_needed") or ():
            needed.add(short_name)

        # Fallback: derive from external symbol table.
        self_code = meta.get("module_code_name")
        for item in meta.get("external_impl_symbols") or ():
            owner_code_name = item.get("owner_code_name")
            symbol = item.get("symbol") or ""
            if owner_code_name in (None, self_code):
                continue

            # Root helpers always use code name owner '__main__' (and rarely
            # other top modules). Materialize only helper_function_* symbols.
            if "$$$helper_function_" not in symbol:
                continue

            short_name = symbol.rsplit("helper_function_", 1)[-1]
            if short_name:
                needed.add(short_name)

    return needed


def _materializeAllNeededInternalHelpers():
    """Ensure every cached external root helper exists before codegen.

    Notes:
        Uses the factory registry and marks helpers used/cross-used on the
        root module so later pruning keeps them.
    """
    from nuitka import ModuleRegistry

    needed = _collectNeededInternalHelperShortNames()
    if not needed:
        return

    # Internal helpers attach to the root/top module.
    owner_module = ModuleRegistry.getRootTopModule()
    if owner_module is None or not owner_module.isCompiledPythonModule():
        return

    for short_name in sorted(needed):
        helper_code_name = "helper_function_" + short_name
        if (
            _findFunctionBodyByCodeName(
                owner_module=owner_module, function_code_name=helper_code_name
            )
            is not None
        ):
            continue

        helper_body = _materializeInternalHelper(
            owner_module=owner_module,
            helper_code_name=helper_code_name,
        )
        if helper_body is None:
            continue

        owner_module.addUsedFunction(helper_body)
        helper_body.markAsCrossModuleUsed()
        helper_body.markAsDirectlyCalled()


def checkModuleFrontendHelperMaterialization():
    """Abort if stub/skip needed an internal helper we cannot build.

    Notes:
        Turns unresolved root helpers into a hard frontend error instead of
        an undefined-symbol link failure later.
    """
    if not _failed_internal_helpers:
        return

    names = ", ".join(sorted(_failed_internal_helpers))
    cache_logger.sysexit(
        "Error, module frontend cache could not materialize internal helper(s): "
        "%s. Recompile without '--experimental=module-frontend-stub' / "
        "'module-frontend-skip-optimize', or extend the helper factory registry."
        % names
    )


def reconcileCrossModuleFunctionUses():
    """Mark functions used via ExpressionFunctionRef across modules.

    Notes:
        Full optimize walks these refs while computing modules. Skip-optimize
        modules never do that, so owner modules (often '__main__' helpers)
        would not get 'addUsedFunction' and later pruning would drop the
        definitions, causing link failures. Newly marked functions that never
        ran 'computeFunctionRaw' also need a trace collection before codegen.

        L3 stubs have no AST; their external symbol needs are reconciled from
        cached meta, and missing root internal helpers are materialized from
        the known factory registry first.
    """
    from nuitka import ModuleRegistry
    from nuitka.optimizations.TraceCollections import withChangeIndicationsTo
    from nuitka.tree.Operations import visitTree

    # Materialize every root helper referenced by cached C before walking trees
    # or pruning unused functions.
    _materializeAllNeededInternalHelpers()

    # Collect first so tree mutation during computeFunctionRaw cannot disturb
    # visitTree.
    discovered = []

    class _FunctionRefCollectVisitor(object):
        def __init__(self, consumer_module):
            self.consumer_module = consumer_module

        def onEnterNode(self, node):
            if node.isExpressionFunctionRef():
                discovered.append((self.consumer_module, node.getFunctionBody()))

        def onLeaveNode(self, node):
            pass

    # Code name -> compiled module for O(1) owner lookup from meta symbols.
    modules_by_code_name = {}
    for module in ModuleRegistry.getDoneModules():
        if module.isCompiledPythonModule():
            modules_by_code_name[module.getCodeName()] = module

    for module in ModuleRegistry.getDoneModules():
        if not module.isCompiledPythonModule():
            continue

        # Stubs have no function-ref nodes worth walking.
        if isModuleFrontendStub(module=module):
            continue

        visitTree(tree=module, visitor=_FunctionRefCollectVisitor(module))

    pending_compute = []
    seen_bodies = set()

    def _markUsed(consumer_module, owner_module, function_body):
        owner_module.addUsedFunction(function_body)

        if owner_module is not consumer_module:
            function_body.markAsCrossModuleUsed()
            function_body.markAsDirectlyCalled()
            consumer_module.addCrossUsedFunction(function_body)

        if (
            function_body not in seen_bodies
            and getattr(function_body, "trace_collection", None) is None
        ):
            seen_bodies.add(function_body)
            pending_compute.append((owner_module, function_body))

    for consumer_module, function_body in discovered:
        owner_module = function_body.getParentModule()
        _markUsed(
            consumer_module=consumer_module,
            owner_module=owner_module,
            function_body=function_body,
        )

    # External impl symbols from cached stub/skip modules.
    for module in ModuleRegistry.getDoneModules():
        if not module.isCompiledPythonModule():
            continue

        meta = _getModuleMeta(module=module)
        if not meta:
            continue

        self_code_name = module.getCodeName()
        for item in meta.get("external_impl_symbols") or ():
            owner_code_name = item.get("owner_code_name")
            symbol = item.get("symbol")
            if not owner_code_name or not symbol:
                continue

            # Skip symbols that belong to the consumer itself.
            if owner_code_name == self_code_name:
                continue

            owner_module = modules_by_code_name.get(owner_code_name)
            if owner_module is None:
                continue

            # Stub owners already restore complete C that contains their helpers.
            if isModuleFrontendStub(module=owner_module):
                continue

            # Symbol form: impl_<owner>$$$helper_function_<name> or function_
            parts = symbol.split("$$$", 1)
            if len(parts) != 2:
                continue
            function_code_name = parts[1]

            function_body = _findFunctionBodyByCodeName(
                owner_module=owner_module,
                function_code_name=function_code_name,
            )

            # L3: consumer stubs never ran reformulation, so internal helpers on
            # the root module may not exist yet.
            if function_body is None and function_code_name.startswith(
                "helper_function_"
            ):
                function_body = _materializeInternalHelper(
                    owner_module=owner_module,
                    helper_code_name=function_code_name,
                )

            if function_body is None:
                continue

            _markUsed(
                consumer_module=module,
                owner_module=owner_module,
                function_body=function_body,
            )

    def _ignoreSignal(tags, source_ref, message):
        # Reconcile runs after optimize passes; change tracking is not needed.
        pass

    with withChangeIndicationsTo(signal_change=_ignoreSignal):
        for owner_module, function_body in pending_compute:
            parent_collection = owner_module.trace_collection
            if parent_collection is None:
                continue

            # Nested functions may appear while computing another body.
            if getattr(function_body, "trace_collection", None) is None:
                function_body.computeFunctionRaw(parent_collection)

    checkModuleFrontendHelperMaterialization()


def tryProbeAndPrepareOptimizeSkip(module):
    """Probe frontend cache and prepare module to skip local optimize micro-passes.

    Notes:
        On success, injects cached used-module attempts into a fresh
        'TraceCollectionModule' so 'considerUsedModules' still closes the
        dependency graph. Does not skip dependency discovery.

    Returns:
        bool: True if local 'computeModule' loop may be skipped.
    """
    module_name = module.getFullName()
    module_name_str = module_name.asString()

    if not _isSkipOptimizeEnabled():
        return False

    # L1: memoize decision so later optimization passes do not re-probe.
    if module_name_str in _skip_decision_memo:
        return _skip_decision_memo[module_name_str]

    # L3 stubs are always skipped.
    if isModuleFrontendStub(module=module):
        meta = _getModuleMeta(module=module)
        used_modules_data = (meta or {}).get("used_modules") or []
        if module.trace_collection is None:
            _prepareUsageTraceCollection(
                module=module, used_modules_data=used_modules_data
            )
        _optimize_skipped_modules.add(module_name_str)
        _recordOptimize(module_name=module_name, result="stub", reason="stub-module")
        _skip_decision_memo[module_name_str] = True
        return True

    reason = _eligibilityReason(module=module)
    if reason is not None:
        _recordOptimize(module_name=module_name, result="probe_bypass", reason=reason)
        _skip_decision_memo[module_name_str] = False
        return False

    cache_key = makeModuleFrontendCacheKey(module=module)
    if cache_key is None:
        _recordOptimize(module_name=module_name, result="probe_bypass", reason="no-key")
        _skip_decision_memo[module_name_str] = False
        return False

    meta, paths_or_reason = _loadValidatedMeta(module=module, cache_key=cache_key)
    if meta is None:
        reason = paths_or_reason
        if reason == "not-present":
            _recordOptimize(module_name=module_name, result="probe_miss", reason=reason)
        else:
            _recordOptimize(
                module_name=module_name, result="probe_invalid", reason=reason
            )
            cache_logger.info(
                "Module frontend optimize-skip invalid for '%s' (%s)."
                % (module_name.asString(), reason)
            )
        _skip_decision_memo[module_name_str] = False
        return False

    used_modules_data = meta.get("used_modules") or []
    _prepareUsageTraceCollection(module=module, used_modules_data=used_modules_data)

    # Keep meta/paths for later external-symbol reconcile / helpers.
    _setModuleCacheData(
        module_name_str=module_name_str,
        meta=meta,
        paths=paths_or_reason,
        cache_key=cache_key,
    )

    _optimize_skipped_modules.add(module_name_str)
    _recordOptimize(module_name=module_name, result="skip", reason="probe-hit")
    _skip_decision_memo[module_name_str] = True
    cache_logger.info(
        "Module frontend optimize-skip for '%s'." % module_name.asString()
    )
    return True


def tryBuildCachedFrontendModule(
    module_name,
    module_filename,
    reason,
    source_code,
    source_ref,
    is_package,
    is_top,
    is_main,
    mode,
):
    """L3: build a no-AST stub module when a validated frontend cache exists.

    Args:
        module_name: ModuleName of the module being built.
        module_filename: Source filename for the module.
        reason: Inclusion reason string.
        source_code: Full module source text.
        source_ref: Source reference for the module node.
        is_package: Whether this is a package module.
        is_top: Whether this is a top-level module.
        is_main: Whether this is the main module.
        mode: Compilation mode string.

    Returns:
        module instance or None
    """
    if not _isStubEnabled():
        return None

    if is_main or is_top:
        return None

    if mode != "compiled":
        return None

    if not source_code:
        return None

    cache_key = _makeCacheKeyFromSource(
        module_name=module_name,
        source_code=source_code,
        reason=reason or "",
    )

    meta, paths_or_reason = _loadValidatedMetaForName(
        module_name=module_name,
        cache_key=cache_key,
        expected_module_name=module_name.asString(),
    )
    if meta is None:
        return None

    paths = paths_or_reason

    from nuitka.nodes.FutureSpecs import FutureSpec
    from nuitka.nodes.ModuleNodes import (
        CompiledPythonModule,
        CompiledPythonPackage,
    )

    if is_package:
        module = CompiledPythonPackage(
            module_name=module_name,
            reason=reason,
            is_top=is_top,
            mode=mode,
            future_spec=FutureSpec(use_annotations=False),
            source_ref=source_ref,
        )
    else:
        module = CompiledPythonModule(
            module_name=module_name,
            reason=reason,
            is_top=is_top,
            mode=mode,
            future_spec=FutureSpec(use_annotations=False),
            source_ref=source_ref,
        )

    # Keep source for later keying / reports.
    module.source_code = source_code
    _setModuleCacheData(
        module_name_str=module_name.asString(),
        meta=meta,
        paths=paths,
        cache_key=cache_key,
    )

    # Empty body: no AST, no functions.
    module.setChildBody(None)
    module.setChildFunctions(())

    used_modules_data = meta.get("used_modules") or []
    _prepareUsageTraceCollection(module=module, used_modules_data=used_modules_data)

    markModuleFrontendStub(module=module)
    _stats["stub"] = _stats.get("stub", 0) + 1
    _record(module_name=module_name, result="stub", reason="no-ast")

    cache_logger.info(
        "Module frontend stub (no AST) for '%s'." % module_name.asString()
    )
    return module


def _restoreCachedArtifacts(source_c, source_const, c_filename, const_filename):
    """Restore C/.const into the build tree, optionally preserving mtime.

    Notes:
        With '--keep-backend-objects', identical content keeps the existing
        file mtime so Scons can reuse object files.

    Args:
        source_c: Cached module C path.
        source_const: Cached module const path.
        c_filename: Destination module C path in the build tree.
        const_filename: Destination module const path in the build tree.
    """
    from nuitka.options.Options import shallKeepBackendObjects

    if shallKeepBackendObjects():
        copyFileIfChanged(source_path=source_c, dest_path=c_filename)
        copyFileIfChanged(source_path=source_const, dest_path=const_filename)
    else:
        copyFile(source_path=source_c, dest_path=c_filename)
        copyFile(source_path=source_const, dest_path=const_filename)


def tryRestoreModuleFrontendCache(module, c_filename, const_filename):
    """Try to restore generated C and const files for module.

    Args:
        module: Compiled module node to restore for.
        c_filename: Destination path for module C.
        const_filename: Destination path for module const blob.

    Returns:
        bool: True if restored successfully.
    """
    if not _isFeatureEnabled():
        return False

    module_name = module.getFullName()

    # L3 stubs always restore from the paths captured at build time.
    if isModuleFrontendStub(module=module):
        paths = _getModulePaths(module=module)
        meta = _getModuleMeta(module=module)
        if paths is None or meta is None:
            _record(
                module_name=module_name, result="invalid", reason="stub-missing-paths"
            )
            return False

        try:
            _restoreCachedArtifacts(
                source_c=paths["module_c"],
                source_const=paths["module_const"],
                c_filename=c_filename,
                const_filename=const_filename,
            )
        except (OSError, IOError):
            _record(module_name=module_name, result="invalid", reason="restore-io")
            return False

        _registerHelpersFromMetaOrC(
            meta=meta, module_c_path=paths["module_c"], paths=paths
        )
        _record(module_name=module_name, result="hit", reason="stub-restored")
        cache_logger.info(
            "Module frontend cache hit (stub) for '%s'." % module_name.asString()
        )
        return True

    reason = _eligibilityReason(module=module)
    if reason is not None:
        _record(module_name=module_name, result="bypass", reason=reason)
        return False

    cache_key = makeModuleFrontendCacheKey(module=module)
    if cache_key is None:
        _record(module_name=module_name, result="bypass", reason="no-key")
        return False

    meta, paths_or_reason = _loadValidatedMeta(module=module, cache_key=cache_key)
    if meta is None:
        reason = paths_or_reason
        if reason == "not-present":
            _record(module_name=module_name, result="miss", reason=reason)
            cache_logger.info(
                "Module frontend cache miss for '%s' (not present)."
                % module_name.asString()
            )
        else:
            _record(module_name=module_name, result="invalid", reason=reason)
            cache_logger.info(
                "Module frontend cache invalid for '%s' (%s)."
                % (module_name.asString(), reason)
            )
        return False

    paths = paths_or_reason

    # Restore into build directory.
    try:
        _restoreCachedArtifacts(
            source_c=paths["module_c"],
            source_const=paths["module_const"],
            c_filename=c_filename,
            const_filename=const_filename,
        )
    except (OSError, IOError):
        _record(module_name=module_name, result="invalid", reason="restore-io")
        return False

    # Ensure __helpers generation still emits high-arity calls used by this C.
    _registerHelpersFromMetaOrC(meta=meta, module_c_path=paths["module_c"], paths=paths)

    _setModuleCacheData(
        module_name_str=module_name.asString(),
        meta=meta,
        paths=paths,
        cache_key=cache_key,
    )

    _record(module_name=module_name, result="hit", reason="restored")
    cache_logger.info("Module frontend cache hit for '%s'." % module_name.asString())
    return True


def storeModuleFrontendCache(module, c_filename, const_filename):
    """Store generated C and const files for a module if eligible.

    Args:
        module: Compiled module node after successful codegen.
        c_filename: Path of the generated module C file.
        const_filename: Path of the generated module const blob.
    """
    if not _isFeatureEnabled():
        return False

    module_name = module.getFullName()

    # Do not store C produced from an optimize-skipped tree unless we also
    # restored (which would not call store). If generate ran after skip, the
    # tree may be under-optimized - refuse to poison the cache.
    if wasModuleOptimizeSkipped(module=module) or isModuleFrontendStub(module=module):
        cache_logger.info(
            "Module frontend cache store skipped for '%s' (optimize was skipped; "
            "codegen should have restored)." % module_name.asString()
        )
        return False

    reason = _eligibilityReason(module=module)
    if reason is not None:
        if module_name.asString() not in _module_results:
            _record(module_name=module_name, result="bypass", reason=reason)
        return False

    cache_key = makeModuleFrontendCacheKey(module=module)
    if cache_key is None:
        if module_name.asString() not in _module_results:
            _record(module_name=module_name, result="bypass", reason="no-key")
        return False

    used_modules_data = _serializeUsedModules(module=module)
    paths = _cachePaths(cache_key=cache_key)
    makePath(path=paths["dir"])

    if not os.path.isfile(c_filename) or not os.path.isfile(const_filename):
        return False

    # Atomic write via temp files then replace.
    tmp_c = paths["module_c"] + ".tmp"
    tmp_const = paths["module_const"] + ".tmp"
    tmp_meta = paths["meta"] + ".tmp"

    try:
        copyFile(source_path=c_filename, dest_path=tmp_c)
        copyFile(source_path=const_filename, dest_path=tmp_const)

        c_hash = Hash()
        c_hash.updateFromFile(tmp_c)
        const_hash = Hash()
        const_hash.updateFromFile(tmp_const)

        scanned = _scanModuleCArtifacts(module_c_path=tmp_c)

        # Prefer explicit short names for root helpers this module's C needs.
        self_code_name = module.getCodeName()
        internal_helpers_needed = []
        seen_helpers = set()
        for item in scanned["external_impl_symbols"]:
            owner_code_name = item.get("owner_code_name")
            symbol = item.get("symbol") or ""
            if owner_code_name == self_code_name:
                continue
            if "$$$helper_function_" not in symbol:
                continue
            short_name = symbol.rsplit("helper_function_", 1)[-1]
            if short_name and short_name not in seen_helpers:
                seen_helpers.add(short_name)
                internal_helpers_needed.append(short_name)

        meta = {
            "file_format_version": _cache_format_version,
            "module_name": module_name.asString(),
            "cache_key": cache_key,
            "nuitka_version": version_string,
            "python_version": list(sys.version_info),
            "compilation_mode": getCompilationMode(),
            "c_hash": c_hash.asHexDigest(),
            "const_hash": const_hash.asHexDigest(),
            "used_modules": used_modules_data,
            "had_cross_used": bool(module.getCrossUsedFunctions()),
            "module_code_name": module.getCodeName(),
            "quick_call_arities": scanned["quick_call_arities"],
            "quick_instance_call_arities": scanned["quick_instance_call_arities"],
            "quick_tuple_call_arities": scanned["quick_tuple_call_arities"],
            "quick_mixed_calls": scanned["quick_mixed_calls"],
            "external_impl_symbols": scanned["external_impl_symbols"],
            "internal_helpers_needed": sorted(internal_helpers_needed),
            "source_hash": getStringHash(
                _getModuleSourceForCacheKey(module=module) or ""
            ),
        }

        writeJsonToFilename(filename=tmp_meta, contents=meta)

        replaceFileAtomic(source_path=tmp_c, dest_path=paths["module_c"])
        replaceFileAtomic(source_path=tmp_const, dest_path=paths["module_const"])
        replaceFileAtomic(source_path=tmp_meta, dest_path=paths["meta"])
    except (OSError, IOError) as e:
        cache_logger.warning(
            "Failed to store module frontend cache for '%s': %s"
            % (module_name.asString(), e)
        )
        return False

    # L1/L2: update process index for faster future lookups.
    _updateIndexEntry(
        module_name_str=module_name.asString(),
        entry={
            "cache_key": cache_key,
            "source_hash": meta["source_hash"],
            "module_code_name": meta["module_code_name"],
            "used_module_names": [
                item["module_name"]
                for item in used_modules_data
                if item.get("module_kind") is not None
            ],
        },
    )

    _stats["store"] = _stats.get("store", 0) + 1
    cache_logger.info("Module frontend cache store for '%s'." % module_name.asString())
    return True


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
