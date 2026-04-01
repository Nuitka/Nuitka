"""Walrus dictionary operation corner cases."""


def case1_pop3_unknown_key(key, **kwargs):
    """Walrus with 'kwargs.pop(key, None)' where key hashability is unknown."""

    if (value := kwargs.pop(key, None)) is not None:
        return value

    return None


def case2_pop3_union_key(flag, **kwargs):
    """Walrus pop with runtime key being hashable string or unhashable list."""

    key = [] if flag else "x"

    if (value := kwargs.pop(key, None)) is not None:
        return value

    return None


def case3_pop3_nested_walrus(key, **kwargs):
    """Nested walrus pop calls to stress short-circuit ordering and side effects."""

    if (left := kwargs.pop(key, None)) is not None and (
        right := kwargs.pop("y", None)
    ) is not None:
        return left, right

    return None


def case4_setdefault3_unknown_key(key, **kwargs):
    """Walrus with 'kwargs.setdefault(key, 123)' for unknown key hashability."""

    if (value := kwargs.setdefault(key, 123)) is not None:
        return value

    return None


def case5_pop3_in_try(key, **kwargs):
    """Walrus pop inside explicit try/except to exercise try node exception tracking."""

    try:
        if (value := kwargs.pop(key, None)) is not None:
            return value
    except TypeError:
        return "caught"

    return None


print("case1-hit", case1_pop3_unknown_key("x", x=1))
print("case1-miss", case1_pop3_unknown_key("x"))

print("case2-false", case2_pop3_union_key(False, x=1))

try:
    print("case2-true", case2_pop3_union_key(True, x=1))
except TypeError:
    print("case2-true", "TypeError")

print("case3-both", case3_pop3_nested_walrus("x", x=1, y=2))
print("case3-missing", case3_pop3_nested_walrus("x", x=1))

print("case4", case4_setdefault3_unknown_key("x"))

print("case5-hit", case5_pop3_in_try("x", x=1))
print("case5-miss", case5_pop3_in_try("x"))
print("case5-caught", case5_pop3_in_try([], x=1))
