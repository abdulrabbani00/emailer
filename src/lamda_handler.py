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

# %%
# Testing Starting and stopping AWS instances


#client = create_ec2_client()
#ec2_info = get_emailer_instance_info(client, "emailer-app-dev-1")
#start_ec2 = turn_server_on(client, ec2_info)
#ec2_info_post = get_emailer_instance_info(client, "emailer-app-dev-1")
#stop_ec2 = turn_server_off(client, ec2_info_post)