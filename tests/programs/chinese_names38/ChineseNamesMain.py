# encoding: utf8
#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-project: --follow-import-to=测试
# nuitka-project: --follow-import-to=那里

from 测试 import 这里

# translate: from test import here
这里()
# here.test

from 那里 import 另一个测试

另一个测试()

from 测试.这边 import *

# not pass here
# trying to import everything from a unicode module

为什么呢()

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
