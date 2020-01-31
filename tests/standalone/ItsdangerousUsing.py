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


# nuitka-skip-unless-imports: itsdangerous

from itsdangerous import Signer
s = Signer('secret-key')
print(s.sign('my string'))
print(s.unsign('my string.wh6tMHxLgJqB6oY1uT73iMlyrOA'))

from itsdangerous import URLSafeSerializer
s = URLSafeSerializer('secret-key')
print(s.dumps([1, 2, 3, 4]))
print(s.loads('WzEsMiwzLDRd.wSPHqC0gR7VUqivlSukJ0IeTDgo'))

from itsdangerous import JSONWebSignatureSerializer
s = JSONWebSignatureSerializer('secret-key')
print(s.dumps({'x': 42}))
print(s.dumps(0, header_fields={'v': 1}))


s1 = URLSafeSerializer('secret-key', salt='activate-salt')
print(s1.dumps(42))

s2 = URLSafeSerializer('secret-key', salt='upgrade-salt')
print(s2.dumps(42))
