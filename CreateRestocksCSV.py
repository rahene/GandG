import ConfigParser
import smtplib
import datetime, time
import imaplib
import email
import csv
import os, sys
from collections import OrderedDict

#config = ConfigParser.ConfigParser()
#config.read("/etc/config.txt")

ORG_EMAIL   = "@gritandgrey.com"
FROM_EMAIL  = "hello" + ORG_EMAIL
FROM_PWD    = "Adex1Presley2!"   #config.get("configuration", "password")
SMTP_SERVER = "imap.gmail.com"
SMTP_PORT   = 993


def get_email_body_list(test_subject_search_text, test_timestamp, folder_name='inbox'):
    email_bodies_within_timeframe_dict = {}
    try:
        mail = imaplib.IMAP4_SSL(SMTP_SERVER)
        mail.login(FROM_EMAIL, FROM_PWD)

        print "\nSearching through {} folder\n".format(folder_name)
        mail.select(folder_name)
        #mail.list()    #get mailboxes available

        mail_type, data = mail.search(None, 'ALL')
        mail_ids = data[0]

        id_list = mail_ids.split()
        first_email_id = int(id_list[0])
        latest_email_id = int(id_list[-1])

        new_order_count = 0
        # valid_email_count = 0
        email_too_old = False
        for i in range(latest_email_id, first_email_id, -1):
            if not email_too_old:

                typ, data = mail.fetch(i, '(RFC822)')
                for response_part in data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_string(response_part[1])
                        email_subject = msg['subject']
                        email_from = msg['from']

                        if email_subject:
                            print 'Subject : {}'.format(email_subject)

                            if ((type(test_subject_search_text) == list) and any(
                                        s.lower() in email_subject.lower() for s in test_subject_search_text)) or ((
                                    type(test_subject_search_text) == str) and test_subject_search_text.lower() in email_subject.lower()):

                                for part in msg.walk():
                                    # each part is a either non-multipart, or another multipart message
                                    # that contains further parts... Message is organized like a tree
                                    if part.get_content_type() == 'text/plain':
                                        email_body = part.get_payload(decode=True)  # prints the raw text
                                        new_order_count = new_order_count + 1

                                        print "Relevant email count: {}".format(new_order_count)
                                        # print email_body

                                        email_date_tuple = email.utils.parsedate_tz(msg['Date'])
                                        email_timestamp = datetime.datetime.fromtimestamp(email.utils.mktime_tz(email_date_tuple))

                                        valid_email = is_valid_email_by_date(email_timestamp, test_timestamp)
                                        if valid_email:
                                            #valid_email_count = valid_email_count + 1
                                            email_bodies_within_timeframe_dict[email_timestamp] = email_body
                                            #print "Valid email count: {}\n".format(valid_email_count)
                                        else:
                                            print "Emails are now out of date. Break"
                                            email_too_old = True
                                            break
                            else:
                                print "Invalid email due to email subject"
                        else:
                            print "Invalid email due to NO subject"
            else:
                print "Breaking out of email searching"
                break

    except Exception as e:
        print "Error: {}".format(e.message)

    return email_bodies_within_timeframe_dict


def convert_timestamp(timestamp_str):
    #print "current str: {}".format(timestamp_str)

    if len(timestamp_str) > 8:
        timestamp = datetime.datetime.strptime(timestamp_str, "%m/%d/%y %I:%M %p")
    else:
        timestamp = datetime.datetime.strptime(timestamp_str,
                                               "{}/{}/{} %I:%M %p".format(datetime.datetime.today().month,
                                                                              datetime.datetime.today().day,
                                                                              datetime.datetime.today().year))
    print "Using timestamp: {}".format(timestamp)
    return timestamp


def is_valid_email_by_date(email_date, test_timestamp):
    #test_timestamp = convert_timestamp(test_timestamp_str)

    return (email_date >= test_timestamp)


def export_restock_requests(email_dict, restock_csv_path):
    for email_date, email_body in email_dict.items():
        results_dict = OrderedDict()
        column_names = ["NAME", "EMAIL", "ITEM", "SIZE", "COLOR"]
        email_body_list = email_body.replace('\n', '').split('\r')
        for line in email_body_list:
            for cname in column_names:
                if cname in line:
                    if line.split(":")[1].strip() == '':
                        results_dict[cname] = email_body_list[email_body_list.index(line) + 1].strip()
                    else:
                        results_dict[cname] = line.split(":")[1].strip()
                    break
        if not results_dict.has_key("COLOR"):
            results_dict["COLOR"] = ''
        results_dict["DATE"] = email_date
        write_line_to_csv(results_dict, restock_csv_path)
    print "\n\n***Finished writing to csv: {}\n\n".format(restock_csv_path)


def write_line_to_csv(results_dict, csv_path):
    if not os.path.exists(csv_path):
        print "*DEBUG* Writing new csv path"
        open_file_as = 'wb'
    else:
        print "*DEBUG* Appending to csv path"
        open_file_as = 'a'
    with open(csv_path, open_file_as) as csvfile:
        fieldnames = results_dict.keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
        if open_file_as == 'wb':
            writer.writeheader()

        writer.writerow(results_dict)


def clear_prev_csv_results(result_path):
    if os.path.exists(result_path):
        os.remove(result_path)


def merge_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def get_user_folder_path():
    if sys.platform == 'win32':
        home = os.getenv("USERPROFILE")
    elif sys.platform == 'darwin':
        home = os.getenv("HOME")
    else:
        raise AssertionError("Unsupported Operating System")

    assert home, "Unable to determine user home directory (missing environment variable)"
    return home


def get_order_summary(email_dict):
    total = float(0)
    for email_count, email_body in email_dict.items():
        prev_line = ""
        for line in email_body.split('\n'):
            if "blog" in line and "$" in prev_line:
                current_order = float(prev_line.strip().split('$')[1])
                print "Email {} Order total: {}".format(email_count, current_order)
                total = total + current_order
            prev_line = line
    print "Total from valid orders: ${}".format(total)


new_arrival_folder = "[Gmail]/NewArrivals"
trash_folder = "[Gmail]/Trash"

new_order_text = "new order has arrived"
restock_text = ["Form Submission - RESTOCK REQUEST", "Form submission error"]
restock_csv_path = os.path.join(get_user_folder_path(), "GGRestockRequests.csv")

#test_date = "May 27, 2018 at 8:00 pm"
valid_input = False
x = 5
test_date_timestamp = "unknown"
script_type = "unknown"
while not valid_input and x > 0:
    script_type = raw_input("Which script do you want to run? Your options are 'restock' or 'order summary' ")
    type(script_type)
    try:
        assert script_type in ['restock', 'order summary'], "Only input 'restock' or 'order summary' ya dingleberry."
    except Exception as e:
        print "Failure: {}".format(e.message)
        x -= 1

    test_date = raw_input("Search for restock request emails back until date:\nUse format 'mm/dd/yy 8:00 pm' ")
    type(test_date)
    try:
        assert script_type in ['restock', 'order summary'], "Only input 'restock' or 'order summary' ya dingleberry."
        test_date_timestamp = convert_timestamp(test_date)
        valid_input = True
    except Exception as e:
        print "Dummy, use the right format please: {}".format(e.message)
        x -= 1

if script_type == 'restock':
    trash_bodies_dict = get_email_body_list(restock_text, test_date_timestamp, trash_folder)
    inbox_bodies_dict = get_email_body_list(restock_text, test_date_timestamp)
    valid_email_bodies_dict = merge_dicts(trash_bodies_dict, inbox_bodies_dict)

    clear_prev_csv_results(restock_csv_path)

    export_restock_requests(valid_email_bodies_dict, restock_csv_path)
elif script_type == 'order summary':
    trash_bodies_dict = get_email_body_list(new_order_text, test_date_timestamp, trash_folder)
    inbox_bodies_dict = get_email_body_list(new_order_text, test_date_timestamp)
    valid_email_bodies_dict = merge_dicts(trash_bodies_dict, inbox_bodies_dict)

    print get_order_summary(valid_email_bodies_dict)
