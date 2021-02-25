#!/usr/bin/env python3
import unittest
import shutil
import datetime
import sys
import os
import json
import ast

sys.path.append('../src')
import emailer

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
our_email = 'arabbani1225@gmail.com'
UNIT_TEST_GRAVEYARD = "../test"

class TestNotebook(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Copy the empty ledger
        # Set is as the ledger
        shutil.copy('raw_ledger.json', 'ledger.json')
        print("Starting auth")
        cls.service = emailer.gmail_authenticate("../src/token.pickle")
        cls.gmail_response = emailer.search_messages(cls.service,
                                             "[Emailer][Unit Test] File Used for unit test do not delete ")
        cls.message_details = emailer.read_msg(cls.service, cls.gmail_response[-1]['id'])
        cls.now_time = datetime.datetime.now().strftime("%Y-%m-%d-%M-%s")
        cls.project_dir = emailer.create_directory_structure(UNIT_TEST_GRAVEYARD, f"New_Project_{cls.now_time}" + ".1")

    @classmethod
    def tearDownClass(cls):
        """
        Tear shit down after using it
        """
        if os.path.exists("ledger.json"):
            os.remove("ledger.json")

    def test_gmail_auth(self):
        """
        Just check to see that you can create the service object
        """
        self.assertEqual(str(type(self.service)), "<class 'googleapiclient.discovery.Resource'>")

    def test_pickle_from_s3(self):
        """
        Check to make sure you can get the pickle file from s3
        """
        creds = emailer.get_pickle_s3("abdul-bullshit", "emailer/token.pickle")
        self.assertEqual(str(type(creds)), "<class 'google.oauth2.credentials.Credentials'>")

    def test_seach_msg(self):
        """
        This will make sure you can find the unit test email
        - Make sure the output is a list
        - Make sure the length is only 1
        - Make sure the response ID is what you expect
        """
        self.assertIs(type(self.gmail_response), list)
        self.assertEqual(len(self.gmail_response), 1)
        self.assertEqual(self.gmail_response[0]['id'], "177ca9bdc2f6ecbb")

    def test_read_msg(self):
        """
        This is going to decode and output the message
        - Make sure the output is dict
        - Make sure you cant decode the subject
        - Make sure the message can be turned to a dict
        """
        self.assertIs(type(self.message_details), dict)
        self.assertEqual(self.message_details["Subject"],
                         '[Emailer][Unit Test] File Used for unit test DO NOT DELETE')
        self.assertIs(type(ast.literal_eval(self.message_details["raw_message"])), list)

    def test_sort_subject_name(self):
        """
        Make sure that the subject can properly be split up
        """
        sorted_subject = emailer.sort_subject_name("[Emailer][Hello World] Some description")

        self.assertEqual(sorted_subject["project_name"], "Hello_World")
        self.assertEqual(sorted_subject['project_description'], "Some description")

    def test_update_ledger(self):
        """
        Update the ledger:
        - Update an existing project
            - Check to make sure the version number equals the number of version for the project
        - Create a new project
            - Create the first version of the project
        """
        existing_project = f"[Emailer][Existing_Project] Some existing project {self.now_time}"
        new_project = f"[Emailer][New_Project_{self.now_time}] Some new project again"

        existing_project_version = emailer.update_ledger(UNIT_TEST_GRAVEYARD, existing_project)
        with open(f"{UNIT_TEST_GRAVEYARD}/ledger.json", "r") as ledger_read:
            ledger_content = json.load(ledger_read)

        num_of_projects = len(ledger_content["Existing_Project"])
        version_num = int(existing_project_version.split(".")[-1])

        self.assertEqual(num_of_projects, version_num)

        new_project_version = emailer.update_ledger(UNIT_TEST_GRAVEYARD, new_project)
        self.assertEqual(new_project_version, f"New_Project_{self.now_time}" + ".1")

    def test_create_directory_structure(self):
        self.assertTrue(os.path.isdir(self.project_dir))

    def test_write_email_to_file(self):
        raw_file = emailer.write_email_to_file(self.message_details, self.project_dir)

        self.assertTrue(os.path.isfile(raw_file))

unittest.main(argv=[''], verbosity=2, exit=False)
