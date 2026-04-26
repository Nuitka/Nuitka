#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

"""Regression test for the Python 3.13 cancel/await bridge."""

# pylint: disable=exec-used,invalid-name

import asyncio
import sys

if sys.version_info < (3, 13):
    print("builtins int 42")
else:
    namespace = {}

    exec(
        "import asyncio\n"
        "\n"
        "async def run_inner():\n"
        "    current_task = asyncio.current_task()\n"
        "    loop = asyncio.get_running_loop()\n"
        "    result_future = loop.create_future()\n"
        "\n"
        "    async def request_cancel():\n"
        "        current_task.cancel()\n"
        "\n"
        "    cancel_task = asyncio.create_task(request_cancel())\n"
        "\n"
        "    def deliver_result(_task):\n"
        "        if not result_future.done():\n"
        "            result_future.set_result(42)\n"
        "\n"
        "    cancel_task.add_done_callback(deliver_result)\n"
        "\n"
        "    try:\n"
        "        await asyncio.sleep(3600)\n"
        "    except asyncio.CancelledError:\n"
        "        return await result_future\n",
        namespace,
    )

    async def run_entrypoint():
        """Run the uncompiled inner coroutine through the compiled entrypoint."""

        result = await namespace["run_inner"]()
        print(type(result).__module__, type(result).__name__, repr(result))

    asyncio.run(run_entrypoint())

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
