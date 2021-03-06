"""
This module will do the following:
- Connect to gmails api
- Check for new emails based on a query
- Read and decypher the message
- Update the ledger based on a project
- Create the directory strcuture for the project
- Write the message down locally to the graveyard
"""
# %%
import os
import pickle
import logging
import json
import warnings

from base64 import urlsafe_b64decode
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

import aws_utility
# for encoding/decoding messages in base64
# AWS

warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)

# %%
def gmail_authenticate(file_path="token.pickle"):
    """
    This function will simply read the local pickle file and authenticate you with Gmails API.
    As of now the function will give you the option to
        log in from a web browser if not token is found,
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
            creds =  aws_utility.get_pickle_s3("abdul-bullshit", "emailer/token.pickle")
        except:
            # Figure out the failure message when you cant find the file in s3 due to permission
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
    list(dict): A list of dictionaries which contain email ids
                based on the query used to find emails
    """
    result = service.users().messages().list(userId='me',q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me',
                                                 q=query,
                                                 pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages

def decode_msg(parts):
    """
    Utility function that parses the content of the email

    Parameter:
    parts (list): A list of dictionaries which contains msgs that need to be decoded

    return:
    str: Returns the decoded message from your email
    """
    if parts:
        for part in parts:
            mime_type = part.get("mimeType")
            body = part.get("body")
            data = body.get("data")
            if mime_type == "text/plain":
                if data:
                    text = urlsafe_b64decode(data).decode()
                    return text

def read_msg(service, message_id):
    """
    This function takes Gmail API `service` and the given `message_id` and does the following:
        - Downloads the content of the email
        - Prints email basic information (To, From, Subject & Date) and plain/text parts
        - Creates a folder for each email based on the subject
        - Downloads text/html content (if available) and saves it
            under the folder created as index.html
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
    message_output["raw_message"] = decode_msg(parts)
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
    The ledger will be responsible for keeping track of
        all projects that have occured, and versioning them.
    This way I will not have to keep track of the version myself
    This file might live on s3 and be versioned properly.
    This function will:
    - Check to see if the project is in the ledger
        - If it is not then it will add the project to the ledger
    - Add the current, entry to the ledger

    [Emailer][Hello_world] Say hello in python
    [Emailer][Project_Name] Some description

    Parameters:
    graveyard_path (str): The local path to the directory of the
        graveyard (help keep local and prod testing seperate)
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
            logging.warning("Your project description already exists, be warned")
            logging.warning(ledger_content[project_name])

        existing_projects = len(ledger_content[project_name].keys())
        project_version = project_name + "." +str(existing_projects + 1)
        ledger_content[project_name][project_version] = project_description
        logging.info(f"Updated the project {project_name}-{project_version}: {project_description}")
    else:
        project_version = project_name + ".1"
        ledger_content[project_name] = {project_version: project_description}
        logging.info(f"Created a new project: {project_name}")

    with open(file_path, "w") as ledger_write:
        json.dump(ledger_content, ledger_write)

    return project_version

def create_directory_structure(graveyard_path, project_version):
    """
    Create the directory for the new version of the project

    Parameters:
    graveyard_path (str): The local path to the directory of the
        graveyard (help keep local and prod testing seperate)
    project_version (str): The project name with its version

    Return:
    str: The path to the project_dir that was created
    """
    project_name = project_version.split(".")[0]
    project_directory_name = graveyard_path + "/" + project_name
    version_directory_name = graveyard_path + "/" + project_name + "/" + project_version

    try:
        os.mkdir(project_directory_name, mode = 0o755)
        logging.info(f"Created the parent dir for this new project: {project_directory_name}")
    except FileExistsError:
        pass

    os.mkdir(version_directory_name, mode = 0o755)
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
        json.dump(email_content, email_output)

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
    write_email_to_file(message_details, project_directory_creation)

    return message_details
