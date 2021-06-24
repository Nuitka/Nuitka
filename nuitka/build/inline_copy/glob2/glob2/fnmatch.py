"""Filename matching with shell patterns.

fnmatch(FILENAME, PATTERN) matches according to the local convention.
fnmatchcase(FILENAME, PATTERN) always takes case in account.

The functions operate by translating the pattern into a regular
expression.  They cache the compiled regular expressions for speed.

The function translate(PATTERN) returns a regular expression
corresponding to PATTERN.  (It does not compile it.)
"""
import os
import re
try:
    from functools import lru_cache
except ImportError:
    from .compat import lru_cache

__all__ = ["filter", "fnmatch", "fnmatchcase", "translate"]


def _norm_paths(path, norm_paths, sep):
    if norm_paths is None:
        path = re.sub(r'\/', sep or os.sep, path)  # cached internally
    elif norm_paths:
        path = os.path.normcase(path)
    return path


def fnmatch(name, pat, norm_paths=True, case_sensitive=True, sep=None):
    """Test whether FILENAME matches PATTERN.

    Patterns are Unix shell style:

    *       matches everything
    ?       matches any single character
    [seq]   matches any character in seq
    [!seq]  matches any char not in seq

    An initial period in FILENAME is not special.
    Both FILENAME and PATTERN are first case-normalized
    if the operating system requires it.
    If you don't want this, use fnmatchcase(FILENAME, PATTERN).

    :param slashes:
    :param norm_paths:
        A tri-state boolean:
        when true, invokes `os.path,.normcase()` on both paths,
        when `None`, just equalize slashes/backslashes to `os.sep`,
        when false, does not touch paths at all.

        Note that a side-effect of `normcase()` on *Windows* is that
        it converts to lower-case all matches of `?glob()` functions.
    :param case_sensitive:
        defines the case-sensitiviness of regex doing the matches
    :param sep:
        in case only slahes replaced, what sep-char to substitute with;
        if false, `os.sep` is used.

    Notice that by default, `normcase()` causes insensitive matching
    on *Windows*, regardless of `case_insensitive` param.
    Set ``norm_paths=None, case_sensitive=False`` to preserve
    verbatim mathces.
    """
    name, pat = [_norm_paths(p, norm_paths, sep)
                 for p in (name, pat)]

    return fnmatchcase(name, pat, case_sensitive=case_sensitive)


@lru_cache(maxsize=256, typed=True)
def _compile_pattern(pat, case_sensitive):
    if isinstance(pat, bytes):
        pat_str = pat.decode('ISO-8859-1')
        res_str = translate(pat_str)
        res = res_str.encode('ISO-8859-1')
    else:
        res = translate(pat)
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(res, flags).match


def filter(names, pat, norm_paths=True, case_sensitive=True, sep=None):
    """Return the subset of the list NAMES that match PAT."""
    result = []
    pat = _norm_paths(pat, norm_paths, sep)
    match = _compile_pattern(pat, case_sensitive)
    for name in names:
        m = match(_norm_paths(name, norm_paths, sep))
        if m:
            result.append((name,
                           tuple(_norm_paths(p, norm_paths, sep) for p in m.groups())))
    return result


def fnmatchcase(name, pat, case_sensitive=True):
    """Test whether FILENAME matches PATTERN, including case.

    This is a version of fnmatch() which doesn't case-normalize
    its arguments.
    """
    match = _compile_pattern(pat, case_sensitive)
    return match(name) is not None


def translate(pat):
    """Translate a shell PATTERN to a regular expression.

    There is no way to quote meta-characters.
    """

    i, n = 0, len(pat)
    res = ''
    while i < n:
        c = pat[i]
        i = i+1
        if c == '*':
            res = res + '(.*)'
        elif c == '?':
            res = res + '(.)'
        elif c == '[':
            j = i
            if j < n and pat[j] == '!':
                j = j+1
            if j < n and pat[j] == ']':
                j = j+1
            while j < n and pat[j] != ']':
                j = j+1
            if j >= n:
                res = res + '\\['
            else:
                stuff = pat[i:j].replace('\\','\\\\')
                i = j+1
                if stuff[0] == '!':
                    stuff = '^' + stuff[1:]
                elif stuff[0] == '^':
                    stuff = '\\' + stuff
                res = '%s([%s])' % (res, stuff)
        else:
            res = res + re.escape(c)
    return '(?ms)' + res + '\Z'
