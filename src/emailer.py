#!/usr/bin/env python3 
# %%
import os
import pickle
import boto3
import ast
import logging
import json
import datetime
import argparse
#from importlib import reload
#reload(logging)

# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode


# %%
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO, datefmt='%I:%M:%S')
# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
our_email = 'arabbani1225@gmail.com'
#GRAVEYARD_PATH = "/home/abdulrab/github/emailer/graveyard"

# %% [markdown]
# # Main Code
# 

# %%
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

    bucketname = "abdul-bullshit" 
    file_to_read = "emailer/token.pickle" 

    fileobj = s3client.get_object(
        Bucket=bucket_name,
        Key=file_to_read
        ) 

    filedata = fileobj['Body'].read()
    contents = pickle.loads(filedata)
    
    return contents

def gmail_authenticate(file_path="token.pickle"):
    """
    This function will simply read the local pickle file and authenticate you with Gmails API.
    As of now the function will give you the option to log in from a web browser if not token is found,
    but down the road that will not be the case.
    
    return:
    googleapiclient.discovery.Resource: API Access
    """
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    logging.info(f"Looking for {file_path} locally")
    if os.path.exists(file_path):
        with open(file_path, "rb") as token:
            creds = pickle.load(token)
            logging.info(f"Found {file_path} locally")
    else:
        try:
            logging.info("Looking for pickle file on s3")
            creds =  get_pickle_s3("abdul-bullshit", "emailer/token.pickle")
        except:
            logging.error("No Pickle file has been found.")
    # Keep the bottom code as the credentials might need to eventually change
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        #else:
        #    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        #    creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds, cache_discovery=False)

def search_messages(service, query):
    """
    This function will check the inbox in gmail based on a query
    The query language used is what is used when you filter an email on gmail
    
    Parameter:
    service (googleapiclient.discovery.Resource): API Access
    query (str): A query, the style is the same as gmail console
    
    Return:
    list(dict): A list of dictionaries which contain email ids based on the query used to find emails
    """
    result = service.users().messages().list(userId='me',q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages

def decode_msg(service, parts):
    """
    Utility function that parses the content of the email
    
    Parameter:
    service (googleapiclient.discovery.Resource): API Access
    parts (list): A list of dictionaries which contains msgs that need to be decoded
    
    return:
    str: Returns the decoded message from your email
    """
    if parts:
        for part in parts:
            mimeType = part.get("mimeType")
            body = part.get("body")
            data = body.get("data")
            if mimeType == "text/plain":
                if data:
                    text = urlsafe_b64decode(data).decode()
                    return text

def read_msg(service, message_id):
    """
    This function takes Gmail API `service` and the given `message_id` and does the following:
        - Downloads the content of the email
        - Prints email basic information (To, From, Subject & Date) and plain/text parts
        - Creates a folder for each email based on the subject
        - Downloads text/html content (if available) and saves it under the folder created as index.html
            * Change the output file name
        - Downloads any file that is attached to the email and saves it in the folder created
            * Remove this part as the emails will never have an attachment
            
    Parameter:
    service (googleapiclient.discovery.Resource): API Access
    message_id (str): The id of the message to read
    
    return:
    dict: contains a dictionary of the raw output 
    """
    msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    
    payload = msg['payload']
    headers = payload.get("headers")
    parts = payload.get("parts")
    
    message_output = {}
    if headers:
        for header in headers:
            name = header.get("name")
            value = header.get("value")
            if name == "Subject":
                message_output["Subject"] = value
            if name == "Date":
                message_output["Date"] = value
    message_output["raw_message"] = decode_msg(service, parts)
    return message_output

def sort_subject_name(subject_name):
    """
    This is a helper function which will sort the project name and description
    
    Parameters:
    subject_name(str):The subject of the email
    [Emailer][Hello_World] Some description
    
    return:
    dict: Contains the project and description name
    """
    subject_info = {}
    project_name = subject_name.split("]")[1].strip("[")
    project_name_no_space = project_name.replace(" ", "_")
    subject_info["project_name"] = project_name_no_space
    subject_info["project_description"] = subject_name.split("]")[2].lstrip(" ")
    
    return subject_info
    
def update_ledger(graveyard_path, subject_name):
    """
    There will be a ledger for the emailer project
    The ledger will be responsible for keeping track off all projects that have occured, and versioning them.
    This way I will not have to keep track of the version myself
    This file might live on s3 and be versioned properly.
    This function will:
    - Check to see if the project is in the ledger
        - If it is not then it will add the project to the ledger
    - Add the current, entry to the ledger
    
    [Emailer][Hello_world] Say hello in python
    [Emailer][Project_Name] Some description
    
    Parameters:
    graveyard_path (str): The local path to the directory of the graveyard (help keep local and prod testing seperate)
    subject_name (str): The subject title in the email
    
    Return:
    dict: The version of the project that has been updated
    """
    
    file_path = f"{graveyard_path}/ledger.json"
    with open(file_path, "r") as ledger_read:
        logging.info("Reading Ledger")
        ledger_content = json.load(ledger_read)
        
    subject_info = sort_subject_name(subject_name)
    project_name = subject_info["project_name"]
    project_description = subject_info["project_description"]
    
    if project_name in ledger_content.keys():
        if project_description in ledger_content[project_name].values():
            logging.warning(f"Your project description already exists, be warned")
            logging.warning(ledger_content[project_name])
        
        existing_projects = len(ledger_content[project_name].keys())
        project_version = project_name + "." +str(existing_projects + 1)
        ledger_content[project_name][project_version] = project_description
        logging.info(f"Updated the project {project_name}- {project_version}: {project_description}")
    else:
        project_version = project_name + ".1" 
        ledger_content[project_name] = {project_version: project_description}
        logging.info(f"Created a new project: {project_name}")
    
    with open(file_path, "w") as ledger_write:
        ledger_output = json.dump(ledger_content, ledger_write)
    
    return project_version

def create_directory_structure(graveyard_path, project_version):
    """
    Create the directory for the new version of the project
    
    Parameters:
    graveyard_path (str): The local path to the directory of the graveyard (help keep local and prod testing seperate)
    project_version (str): The project name with its version
    
    Return:
    None: Nothing is returned
    """
    project_name = project_version.split(".")[0]
    project_directory_name = graveyard_path + "/" + project_name
    version_directory_name = graveyard_path + "/" + project_name + "/" + project_version
    
    try:
        parent_dir = os.mkdir(project_directory_name, mode = 0o755)
        logging.info(f"Created the parent dir for this new project: {project_directory_name}")
    except FileExistsError:
        pass
    
    directory_created = os.mkdir(version_directory_name, mode = 0o755)
    logging.info(f"Created the project dir: {version_directory_name}")
    
    return version_directory_name

def write_email_to_file(email_content, directory, filename="raw.json"):
    """
    Write the 'massaged' email message to the a json file. 
    
    Parameter:
    email_content (dict): The content of the email, after being massaged
    directory (str): Where this email will be written
    
    Return:
    
    """
    file_path = f"{directory}/{filename}"
    with open(file_path, "w") as email_output:
        write_file = json.dump(email_content, email_output)
        
    return file_path

def handle_email(query, graveyard_path):
    """
    This function will handle the oldest new email
    - It will check to see if there are new emails
    - If there are:
        - It will grab the oldest one
        - It will decode the email
        
    Parameters:
    query (str): The query to filter emails, written in the same way as they would be in Gmail
    
    Return:
    dict(With all email characteristics)
    """
    service = gmail_authenticate()
    gmail_response = search_messages(service, query)
    oldest_email_id = gmail_response[-1]['id']
    message_details = read_msg(service, oldest_email_id)
    updated_version = update_ledger(graveyard_path, message_details['Subject'])
    project_directory_creation = create_directory_structure(graveyard_path, updated_version)
    raw_file = write_email_to_file(message_details, project_directory_creation)
    
    return message_details

def lambda_handler():
    """
    This is the main() function for our AWS lambda instance.
    It will:
    - Check to see if we have new mail
    - If we do:
        - It will turn on the AWS server (This will be written later)
        - It will call the emailer function (This will be written later)
    - If it doesnt:
        - It will do nothing.
    - If there are any errors:
        - It will capture the errors (This will be written later)
        - It will send an email output with them (This will be written later)
    """ 
    service = gmail_authenticate()
    new_mail = search_messages(service, "is: label:unread  [Emailer] ")
    
    if len(new_mail) > 0:
        logging.info("There is new mail")
    
def parse_args(local):
    """
    A function to parse the args that are passed through
    The local arg has been added because jupyter does not like arg parse, therefore it avoids it

    Parameter: 
    local (bool): Indicates if this code is running locally

    Return: (argparse.Namespace): The args that are returned

    """
    my_parser = argparse.ArgumentParser()

    # Add the arguments
    my_parser.add_argument('--graveyard_path', default='/apps/emailer/graveyard',
                           type=str, help='The path of the graveyard')

    if local:
        args = my_parser.parse_args(args=[])
    else:
        args = my_parser.parse_args()

    return args


# %%
def main(args, local):
    """
    Handles the email, by taking a query and a path to the graveyard

    Parameters:
    args (argparse.Namespace): The args for the script
    local (bool): Indicates if this code is running locally
    """
    # For Running locally
    if local:
        handle_email("is: label:unread  [Emailer]", "/home/abdulrab/github/emailer/graveyard")
    else:
        handle_email("is: label:unread  [Emailer]", args.graveyard_path)


# %%
if __name__ == "__main__":
    local = False 
    args = parse_args(local)
    main(args, local)

# %% [markdown]
# # Code from the Doc
# https://www.thepythoncode.com/article/use-gmail-api-in-python#Searching_for_Emails

# %%


