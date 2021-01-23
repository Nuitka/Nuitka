#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
import boto3
from moto import mock_s3

# nuitka-skip-unless-imports: boto3,moto

# TODO
# mocking is incompatbile with nuitka

def getClient():
    """
    returns the boto3 client
    """
    return boto3.client('s3')

def listS3Buckets():
    """
    lists s3 bucket names
    """
    s3 = getClient()

    response = s3.list_buckets()
    if response:
        for bucket in response.get('Buckets', []):
            yield bucket['Name']

def listS3Objects(bucket):
    """
    lists s3 objects in a bucket
    """
    s3 = getClient()

    response = s3.list_objects(Bucket=bucket)
    if response:
        for _object in response.get('Contents', []):
            yield _object['Key']

def readS3Object(bucket,key):
    """
    returns the content of a s3 file
    """
    s3 = getClient()

    response = s3.get_object(Bucket=bucket, Key=key)
    if response:
        return response['Body'].read()



# script for testing, mocks uploading files to AWS with moto

bucket = 'static'
key = 'style.css'
value = b'value'

@mock_s3
def __motoSetup():
    """
    simulate s3 file upload
    """
    s3 = getClient()
    s3.create_bucket(Bucket=bucket)
    s3.put_object(Bucket=bucket, Key=key, Body=value)

@mock_s3
def testGetClient():
    """
    checks that getClient has a valid endpoint
    """
    s3 = getClient()
    assert s3._endpoint.host == "https://s3.amazonaws.com"

@mock_s3
def testListS3Buckets():
    """
    checks that our bucket shows correctly
    """
    __motoSetup()

    buckets = list(listS3Buckets())
    assert bucket in buckets

@mock_s3
def testListS3Objects():
    """
    checks that object is in bucket as expected
    """
    __motoSetup()

    objects = list(listS3Objects(bucket))
    assert key in objects

@mock_s3
def testReadS3Object():
    """
    checks that object contents are corrent
    """
    __motoSetup()

    content = readS3Object(bucket, key)
    assert value == content

testGetClient()
testListS3Buckets()
testListS3Objects()
testReadS3Object()
print('OK.')
