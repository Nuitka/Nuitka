import botocore.session

# nuitka-skip-unless-imports: botocore

session = botocore.session.get_session()
client = session.create_client('ec2', region_name='us-west-2')
credentials = session.get_credentials()

# these tests below require credentials (botocore.exceptions.NoCredentialsError: Unable to locate credentials)
'''
for reservation in client.describe_instances()['Reservations']:
    for instance in reservation['Instances']:
        print(instance['InstanceId'])

# All instances that are in a state of pending.
reservations = client.describe_instances(
    Filters=[{"Name": "instance-state-name", "Values": ["pending"]}])
'''
