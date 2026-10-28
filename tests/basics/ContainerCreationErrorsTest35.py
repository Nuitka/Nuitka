#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Exceptions while building a container directly into the return value."""

import asyncio
import io
import logging


async def returnDict(value):
    return {"first": 0, "second": await value()}


async def returnList(value):
    return [0, await value()]


async def returnTuple(value):
    return (0, await value())


async def returnSet(value):
    return {0, await value()}


async def fail():
    await asyncio.sleep(0)
    raise RuntimeError("expected failure")


async def succeed():
    await asyncio.sleep(0)
    return 1


async def main():
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    logger = logging.getLogger("container_creation_errors")
    logger.addHandler(handler)
    logger.propagate = False

    try:
        for builder, expected in (
            (returnDict, {"first": 0, "second": 1}),
            (returnList, [0, 1]),
            (returnTuple, (0, 1)),
            (returnSet, {0, 1}),
        ):
            assert await builder(succeed) == expected

            for _ in range(100):
                try:
                    await builder(fail)
                except RuntimeError as exception:
                    assert str(exception) == "expected failure"
                    logger.exception("expected failure")
                    assert "RuntimeError: expected failure" in output.getvalue()
                    output.seek(0)
                    output.truncate()
                else:
                    assert False, "Container creation must propagate the exception"

            print(builder.__name__, "100 failures logged")
    finally:
        logger.removeHandler(handler)
        handler.close()


loop = asyncio.new_event_loop()
try:
    loop.run_until_complete(main())
finally:
    loop.close()

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
