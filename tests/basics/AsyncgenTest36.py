#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tests for asynchronous generator exception state."""

import asyncio
import sys


def current_exception():
    return sys.exc_info()[1]


def run_async(awaitable):
    if hasattr(asyncio, "run"):
        asyncio.run(awaitable)
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(awaitable)


# Async generator athrow context, and state restored on a later resume.
async def agen_context():
    try:
        raise KeyError("agen handled")
    except KeyError:
        yield 1


async def run_agen_context():
    agen = agen_context()
    await agen.__anext__()
    try:
        await agen.athrow(ValueError("agen thrown"))
    except ValueError as e:
        print("Async generator throw context: %r" % (e.__context__,))


run_async(run_agen_context())


async def agen_leak():
    yield 0
    try:
        raise KeyError("agen in generator")
    except KeyError:
        yield 1
    yield 2


async def caller_agen_leak():
    agen = agen_leak()
    await agen.__anext__()
    try:
        raise ValueError("agen caller")
    except ValueError:
        await agen.__anext__()
    await agen.__anext__()
    try:
        await agen.__anext__()
    except StopAsyncIteration:
        pass
    print("Async generator after handler: %r" % (current_exception(),))


run_async(caller_agen_leak())


async def check_invalid_asyncgen_iterables():
    try:
        _ = (x async for x in [1, 2, 3])
    except Exception as e:
        print("Asyncgen over list raised:", type(e).__name__)
    else:
        print("Asyncgen over list did not raise.")

    try:
        _ = ((x async for x in 42), 1)[1]
    except Exception as e:
        print("Asyncgen side effect over int raised:", type(e).__name__, e)
    else:
        print("Asyncgen side effect over int did not raise.")

    try:
        _ = (y async for y in (x async for x in agen_leak()))
    except Exception as e:
        print("Nested asyncgen expression raised:", type(e).__name__, e)
    else:
        print("Nested asyncgen expression created OK.")


run_async(check_invalid_asyncgen_iterables())


def check_asyncgen_athrow_genexit_nested_uncompiled():
    ns = {}
    exec(
        """
import types

class CustomLeafIter:
    def __init__(self, events):
        self.events = events

    def __iter__(self):
        return self

    def __await__(self):
        return self

    def __next__(self):
        self.events.append("custom:start")
        return "suspended"

    def throw(self, *args):
        self.events.append(("custom:throw", args[0].__name__))
        raise StopIteration("from-custom-throw")

    def close(self):
        self.events.append("custom:close")

@types.coroutine
def uncomp_leaf(events, behavior="normal"):
    events.append("leaf:start")
    try:
        yield "suspended"
    except GeneratorExit:
        events.append("leaf:genexit")
        if behavior == "ignore":
            yield "ignored"
        if behavior == "error":
            raise ValueError("leaf close error")
        if behavior == "catch":
            return "caught-in-leaf"
        raise

async def uncomp_coro_inner(events, behavior="normal"):
    events.append("coro_inner:start")
    try:
        if behavior == "custom":
            return await CustomLeafIter(events)
        return await uncomp_leaf(events, behavior)
    finally:
        events.append("coro_inner:finally")

async def uncomp_coro_mid(events, behavior="normal"):
    events.append("coro_mid:start")
    try:
        return await uncomp_coro_inner(events, behavior)
    finally:
        events.append("coro_mid:finally")

async def uncomp_coro_outer(events, behavior="normal", catch_genexit=False):
    events.append("coro_outer:start")
    try:
        return await uncomp_coro_mid(events, behavior)
    except GeneratorExit:
        events.append("coro_outer:genexit")
        if catch_genexit:
            return "caught-in-outer"
        raise
    finally:
        events.append("coro_outer:finally")

@types.coroutine
def uncomp_gen_inner(events, behavior="normal"):
    events.append("gen_inner:start")
    try:
        return (yield from uncomp_leaf(events, behavior))
    finally:
        events.append("gen_inner:finally")

@types.coroutine
def uncomp_gen_mid(events, behavior="normal"):
    events.append("gen_mid:start")
    try:
        return (yield from uncomp_gen_inner(events, behavior))
    finally:
        events.append("gen_mid:finally")

@types.coroutine
def uncomp_gen_outer(events, behavior="normal"):
    events.append("gen_outer:start")
    try:
        return (yield from uncomp_gen_mid(events, behavior))
    finally:
        events.append("gen_outer:finally")
""",
        ns,
    )

    async def comp_coro_catch(events):
        events.append("comp_coro:start")
        try:
            return await ns["uncomp_leaf"](events, "catch")
        except GeneratorExit:
            events.append("comp_coro:genexit")
            return "caught-in-comp-coro"
        finally:
            events.append("comp_coro:finally")

    async def comp_agen(factory, caught=None):
        try:
            res = await factory()
        except BaseException as exc:
            if caught is None:
                print("comp_agen caught:", type(exc).__name__, exc.args)
            else:
                caught.append((type(exc).__name__, exc.args))
            raise
        print("comp_agen await result:", res)
        yield ("yielded", res)

    for label, factory_fn, throw_arg in (
        (
            "coro-normal",
            lambda ev: ns["uncomp_coro_outer"](ev, "normal"),
            GeneratorExit,
        ),
        (
            "coro-caught",
            lambda ev: ns["uncomp_coro_outer"](ev, "normal", True),
            GeneratorExit,
        ),
        (
            "coro-leaf-caught",
            lambda ev: ns["uncomp_coro_outer"](ev, "catch"),
            GeneratorExit,
        ),
        (
            "coro-caught-instance",
            lambda ev: ns["uncomp_coro_outer"](ev, "normal", True),
            GeneratorExit("inst-msg"),
        ),
        ("comp-coro-caught", comp_coro_catch, GeneratorExit),
        ("custom-direct", lambda ev: ns["CustomLeafIter"](ev), GeneratorExit),
        (
            "coro-custom",
            lambda ev: ns["uncomp_coro_outer"](ev, "custom"),
            GeneratorExit,
        ),
        ("coro-error", lambda ev: ns["uncomp_coro_outer"](ev, "error"), GeneratorExit),
        (
            "coro-ignore",
            lambda ev: ns["uncomp_coro_outer"](ev, "ignore"),
            GeneratorExit,
        ),
        ("gen-normal", lambda ev: ns["uncomp_gen_outer"](ev, "normal"), GeneratorExit),
        ("gen-error", lambda ev: ns["uncomp_gen_outer"](ev, "error"), GeneratorExit),
        ("gen-ignore", lambda ev: ns["uncomp_gen_outer"](ev, "ignore"), GeneratorExit),
    ):
        events = []
        agen = comp_agen(lambda ev=events, fn=factory_fn: fn(ev))
        step = agen.asend(None)
        first = step.send(None)
        print(label, "first:", first)
        try:
            out = step.throw(throw_arg)
        except BaseException as exc:
            print(label, "raised:", type(exc).__name__, exc.args)
        else:
            print(label, "returned:", out)
        print(label, "events:", events)

    # athrow(ValueError).throw(GeneratorExit) and aclose().throw(GeneratorExit)
    # while suspended at an await whose coroutine catches GeneratorExit.
    async def comp_agen_athrow_await(events):
        try:
            yield "y1"
        except ValueError:
            try:
                res = await ns["uncomp_coro_outer"](events, "normal", True)
            except BaseException as exc:
                print("athrow-await caught:", type(exc).__name__, exc.args)
                raise
            yield ("yielded", res)

    events = []
    agen = comp_agen_athrow_await(events)
    try:
        agen.asend(None).send(None)
    except StopIteration as exc:
        print("athrow-await y1:", exc.value)
    athrow_step = agen.athrow(ValueError)
    print("athrow-await first:", athrow_step.send(None))
    try:
        out = athrow_step.throw(GeneratorExit)
    except BaseException as exc:
        print("athrow-await raised:", type(exc).__name__, exc.args)
    else:
        print("athrow-await returned:", out)
    print("athrow-await events:", events)

    async def comp_agen_aclose_await(events):
        try:
            yield "y1"
        except GeneratorExit:
            try:
                res = await ns["uncomp_coro_outer"](events, "normal", True)
            except BaseException as exc:
                print("aclose-await caught:", type(exc).__name__, exc.args)
                raise
            print("aclose-await res:", res)

    events = []
    agen = comp_agen_aclose_await(events)
    try:
        agen.asend(None).send(None)
    except StopIteration as exc:
        print("aclose-await y1:", exc.value)
    aclose_step = agen.aclose()
    print("aclose-await first:", aclose_step.send(None))
    try:
        out = aclose_step.throw(GeneratorExit)
    except BaseException as exc:
        print("aclose-await raised:", type(exc).__name__, exc.args)
    else:
        print("aclose-await returned:", out)
    print("aclose-await events:", events)

    # athrow(GeneratorExit).send(None) while suspended at yield:
    async def comp_agen_yield_athrow_genexit():
        try:
            yield "y1"
        except GeneratorExit:
            yield "y2-after-athrow-genexit"

    agen = comp_agen_yield_athrow_genexit()
    try:
        agen.asend(None).send(None)
    except StopIteration as exc:
        print("yield-athrow-genexit y1:", exc.value)
    try:
        out = agen.athrow(GeneratorExit).send(None)
    except BaseException as exc:
        print("yield-athrow-genexit raised:", type(exc).__name__, exc.args)
    else:
        print("yield-athrow-genexit returned:", out)
    try:
        agen.aclose().send(None)
    except StopIteration:
        pass

    # Compiled driver coroutine awaiting asend, then driver.throw(GeneratorExit)
    events = []
    # The async generator gets closed during the throw in CPython 3.13+ and only
    # when the exception traceback releases the driver frame before 3.13.
    caught = []
    driver_agen = comp_agen(
        lambda: ns["uncomp_coro_outer"](events, "normal", True), caught
    )

    async def comp_driver():
        return await driver_agen.asend(None)

    driver = comp_driver()
    print("driver first:", driver.send(None))
    try:
        out = driver.throw(GeneratorExit)
    except BaseException as exc:
        print("driver raised:", type(exc).__name__, exc.args)
    else:
        print("driver returned:", out)
    print("driver agen caught:", caught)
    print("driver events before aclose:", events)
    try:
        driver_agen.aclose().send(None)
    except BaseException as exc:
        print("driver aclose raised:", type(exc).__name__, exc.args)
    print("driver events after aclose:", events)


check_asyncgen_athrow_genexit_nested_uncompiled()

#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
