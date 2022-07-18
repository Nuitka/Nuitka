#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
import rsa

# nuitka-skip-unless-imports: rsa

(tambe_pub, tambe_priv) = rsa.newkeys(512)
message = "beautiful Tambe!".encode("utf8")
encrypted_msg = rsa.encrypt(message, tambe_pub)
message = rsa.decrypt(encrypted_msg, tambe_priv)


def encryption_decryption():
    """Function to test encryption and decryption"""
    assert message.decode("utf8") == "beautiful Tambe!"


if __name__ == "__main__":
    encryption_decryption()
