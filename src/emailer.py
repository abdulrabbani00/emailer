#!/usr/bin/env python3
"""
This script will call all the libaries. So far it can:
- Read/write incoming emails to the graveyard. See handle_new_mail.py
"""
# %%

import logging
import argparse
# Local scripts
import aws_utility
import handle_new_mail

# %%
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    level=logging.INFO, datefmt='%I:%M:%S')
# Request all access (permission to read/send/receive emails, manage the inbox, and more)
#SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
#our_email = 'arabbani1225@gmail.com'

# %%

def parse_args(is_local):
    """
    A function to parse the args that are passed through
    The local arg has been added because jupyter does not like arg parse, therefore it avoids it

    Parameter:
    is_local (bool): Indicates if this code is running locally

    Return: (argparse.Namespace): The args that are returned

    """
    my_parser = argparse.ArgumentParser()

    # Add the arguments
    my_parser.add_argument('--graveyard_path', default='/apps/emailer/graveyard',
                           type=str, help='The path of the graveyard')
    my_parser.add_argument('--gmail_query', default="is: label:unread  [Emailer]",
                           type=str, help='The query to seach emails by')

    if is_local:
        args = my_parser.parse_args(args=[])
    else:
        args = my_parser.parse_args()

    return args


# %%
def main(args, is_local):
    """
    Handles the email, by taking a query and a path to the graveyard

    Parameters:
    args (argparse.Namespace): The args for the script
    is_local (bool): Indicates if this code is running locally
    """
    # For Running locally
    if is_local:
        email_msg = handle_new_mail.handle_email("is: label:unread  [Emailer]",
                                                 "/home/abdulrab/github/emailer/graveyard")
        logging.info(email_msg)
    else:
        handle_new_mail.handle_email(args.gmail_query, args.graveyard_path)


# %%
if __name__ == "__main__":
    IS_LOCAL = True
    arguments = parse_args(IS_LOCAL)
    main(arguments, IS_LOCAL)

# %% [markdown]
# # Code from the Doc
# https://www.thepythoncode.com/article/use-gmail-api-in-python#Searching_for_Emails
