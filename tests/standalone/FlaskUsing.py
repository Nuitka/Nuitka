#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from flask import Flask

# nuitka-skip-unless-imports: flask

# nuitka-project: --mode=standalone


app = Flask(__name__)


@app.route("/")
def main():
    return "Welcome!"


if __name__ == "__main__":
    pass
    # TODO: Find something other meaningful to do.
    # app.run()

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
