#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#

# From Issue#146, this has crashed in the past.

import threading

def some_generator():
    yield 1

def run():
    for i in range(10000):
        for j in some_generator():
            pass

def main():
    workers = [threading.Thread(target = run) for i in range(5)]
    for t in workers:
        t.start()
    for t in workers:
        t.join()

if __name__ == "__main__":
    main()
