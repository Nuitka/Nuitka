import boto3

# nuitka-skip-unless-imports: boto3

session = boto3.Session(
    aws_access_key_id='Example',
    aws_secret_access_key='Example',
    )
s3 = boto3.resource('s3')

# test below requires credentials
'''
for bucket in s3.buckets.all():
    print(bucket.name)
'''
