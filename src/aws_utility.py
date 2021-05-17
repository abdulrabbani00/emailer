"""
This libary is used to interact with AWS for emailer
"""
# %%
import logging
import pickle
import boto3

from botocore.exceptions import ClientError

#%%
def get_pickle_s3(bucket_name="abdul-bullshit",
                  file_to_read="emailer/token.pickle"):
    """
    This function will try to get the pickle file from s3.
    You might need credentials for this ol boy

    Parameters:
    bucket_name (str): The name of the bucket that the file is in
    file_to_read (str): The path of where the pickle file is located
    """
    s3client = boto3.client(
        's3',
        region_name='us-east-1'
    )

    fileobj = s3client.get_object(
        Bucket=bucket_name,
        Key=file_to_read
        )

    filedata = fileobj['Body'].read()
    contents = pickle.loads(filedata)

    return contents

def create_ec2_client():
    """
    Create a client to connect with boto
    """
    ec2 = boto3.client("ec2", "us-east-1")
    return ec2

def get_emailer_instance_info(ec2, instance_name):
    """
    Given the environment, get the emailer instance ID

    Parameters:
    env (str): The environemtn of the instance you want to start or stop
                Shortname: develop --> dev
    ec2 (): ec2 client for making calls

    Return:
    dict: Containing instances information
    """
    instance_info = {}
    response = ec2.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                instance_name,
            ]
        },
    ],
    DryRun=False,
    )
    instance_count = len(response["Reservations"][0]["Instances"])
    if instance_count > 1:
        logging.error(f"Number of instances with this name: {instance_count}")

    instance_info["instance_id"] = response["Reservations"][0]["Instances"][0]["InstanceId"]
    instance_info["instance_name"] = instance_name
    instance_info['instance_state'] = response["Reservations"][0]["Instances"][0]["State"]["Name"]
    return instance_info

def turn_server_on(ec2, instance_info):
    """
    If the instance is stopped, turn it on.
    If it is on, do nothing

    Parameters:
    ec2 (): ec2 client for making calls
    instance_info (dict): Contains the instances id and state

    Return
    dict: Containing the output from starting the instance
    """
    if  instance_info["instance_state"] == "running":
        logging.warning("This instance is already running")

    # Do a dryrun first to verify permissions
    try:
        ec2.start_instances(InstanceIds=[instance_info["instance_id"]],
                                        DryRun=True)
    except ClientError as error:
        if 'DryRunOperation' not in str(error):
            raise

    # Dry run succeeded, run start_instances without dryrun
    try:
        response = ec2.start_instances(InstanceIds=[instance_info["instance_id"]], DryRun=False)
    except ClientError as error:
        logging.error(error)
    return response

def turn_server_off(ec2, instance_info):
    """
    If the instance is running, turn it off.
    If it is off, do nothing

    Parameters:
    ec2 (): ec2 client for making calls
    instance_info (dict): Contains the instances id and state

    Return
    dict: Containing the output from stopping the instance
    """

    try:
        ec2.stop_instances(InstanceIds=[instance_info["instance_id"]],
                           DryRun=True)
    except ClientError as error:
        if 'DryRunOperation' not in str(error):
            raise

    # Dry run succeeded, call stop_instances without dryrun
    try:
        response = ec2.stop_instances(InstanceIds=[instance_info["instance_id"]],
                                      DryRun=False)
    except ClientError as error:
        logging.error(error)

    return response

# %%
