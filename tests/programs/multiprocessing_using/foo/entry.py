#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
from multiprocessing import Pipe, Process


class MyProcess(Process):
    def __init__(self, connection):
        super(MyProcess, self).__init__()
        self.connection = connection
        self.close_issued = False

    def run(self):
        while not self.close_issued:
            op, arg = self.connection.recv()
            if op == "add":
                self.connection.send(arg + 1)
            elif op == "close":
                self.close_issued = True
            elif op == "method":
                self.connection.send(repr(self.run))


def main():
    server_channel, client_channel = Pipe()
    my_process = MyProcess(client_channel)
    my_process.start()

    server_channel.send(("add", 4))
    print(server_channel.recv())

    server_channel.send(("add", 12))
    print(server_channel.recv())

    server_channel.send(("method", None))
    print(("compiled" in server_channel.recv()) == ("compiled" in repr(MyProcess.run)))

    server_channel.send(("close", 0))
