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


# nuitka-skip-unless-imports: jmespath

import jmespath

expression = jmespath.compile('foo.bar')
print(expression.search({'foo': {'bar': 'baz'}}))


from jmespath import functions

# 1. Create a subclass of functions.Functions.
#    The function.Functions base class has logic
#    that introspects all of its methods and automatically
#    registers your custom functions in its function table.
class CustomFunctions(functions.Functions):

    # 2 and 3.  Create a function that starts with _func_
    # and decorate it with @signature which indicates its
    # expected types.
    # In this example, we're creating a jmespath function
    # called "unique_letters" that accepts a single argument
    # with an expected type "string".
    @functions.signature({'types': ['string']})
    def _func_unique_letters(self, s):
        # Given a string s, return a sorted
        # string of unique letters: 'ccbbadd' ->  'abcd'
        return ''.join(sorted(set(s)))

    # Here's another example.  This is creating
    # a jmespath function called "my_add" that expects
    # two arguments, both of which should be of type number.
    @functions.signature({'types': ['number']}, {'types': ['number']})
    def _func_my_add(self, x, y):
        return x + y

# 4. Provide an instance of your subclass in a Options object.
options = jmespath.Options(custom_functions=CustomFunctions())

# Provide this value to jmespath.search:
# This will print 3
print(
    jmespath.search(
        'my_add(`1`, `2`)', {}, options=options)
)

# This will print "abcd"
print(
    jmespath.search(
        'foo.bar | unique_letters(@)',
        {'foo': {'bar': 'ccbbadd'}},
        options=options)
)
