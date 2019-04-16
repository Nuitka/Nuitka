import boto3
from moto import mock_s3

# nuitka-skip-unless-imports: boto3,moto

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



if __name__ == '__main__':
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
    print('All tests passed')
