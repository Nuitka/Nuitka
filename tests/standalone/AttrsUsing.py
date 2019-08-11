#     Copyright 2019, Tommy Li, mailto:tommyli3318@gmail.com
#
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
#


# nuitka-skip-unless-imports: attr

import attr

@attr.s
class Empty(object):
    pass
print(Empty())
print(Empty() == Empty())
print(Empty() is Empty())


@attr.s
class Coordinates(object):
    x = attr.ib()
    y = attr.ib()

c1 = Coordinates(1, 2)
print(c1)
c2 = Coordinates(x=2, y=1)
print(c2)
print(c1 == c2)


from attr import attrs, attrib
@attrs
class SeriousCoordinates(object):
    x = attrib()
    y = attrib()
print(SeriousCoordinates(1, 2))
print(attr.fields(Coordinates) == attr.fields(SeriousCoordinates))


@attr.s
class A(object):
    a = attr.ib()
    def get_a(self):
        return self.a
@attr.s
class B(object):
    b = attr.ib()
@attr.s
class C(A, B):
    c = attr.ib()
i = C(1, 2, 3)

print(i)

print(i == C(1, 2, 3))

print(i.get_a())


import collections
@attr.s
class Connection(object):
    socket = attr.ib()
    @classmethod
    def connect(cls, db_string):
       # connect somehow to db_string ...
       return cls(socket=42)
@attr.s
class ConnectionPool(object):
    db_string = attr.ib()
    pool = attr.ib(default=attr.Factory(collections.deque))
    debug = attr.ib(default=False)
    def get_connection(self):
        try:
            return self.pool.pop()
        except IndexError:
            if self.debug:
                print("New connection!")
            return Connection.connect(self.db_string)
    def free_connection(self, conn):
        if self.debug:
            print("Connection returned!")
        self.pool.appendleft(conn)


cp = ConnectionPool("postgres://localhost")
print(cp)
conn = cp.get_connection()
print(conn)
cp.free_connection(conn)
print(cp)