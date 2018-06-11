import ConfigParser
import smtplib
import datetime, time
import imaplib
import email
import csv
import os, sys
import email_vars
import EmailObjClasses
from collections import OrderedDict

#config = ConfigParser.ConfigParser()
#config.read("/etc/config.txt")

ORG_EMAIL   = "@gritandgrey.com"
FROM_EMAIL  = "hello" + ORG_EMAIL
FROM_PWD    = "Adex1Presley2!"   #config.get("configuration", "password")
SMTP_SERVER = "imap.gmail.com"
SMTP_PORT   = 993


def sort_emails(test_time):
    email_bodies_within_timeframe_dict = {}
    try:
        mail = imaplib.IMAP4_SSL(SMTP_SERVER)
        mail.login(FROM_EMAIL, FROM_PWD)

        for folder_name in email_vars.email_folder_list:
            print "\nSearching through {} folder\n".format(folder_name)
            mail.select(folder_name)
            #mail.list()    #get mailboxes available

            mail_type, data = mail.search(None, 'ALL')
            mail_ids = data[0]

            id_list = mail_ids.split()
            first_email_id = int(id_list[0])
            latest_email_id = int(id_list[-1])

            relevant_email = 0
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

                                subject_type, valid_subject = test_email_subject(email_subject)
                                if valid_subject:

                                    for part in msg.walk():
                                        # each part is a either non-multipart, or another multipart message
                                        # that contains further parts... Message is organized like a tree
                                        if part.get_content_type() == 'text/plain':
                                            email_body = part.get_payload(decode=True)  # prints the raw text

                                            print "Relevant email count: {}".format(relevant_email)
                                            # print email_body

                                            email_date_tuple = email.utils.parsedate_tz(msg['Date'])
                                            email_timestamp = datetime.datetime.fromtimestamp(
                                                email.utils.mktime_tz(email_date_tuple))

                                            valid_email_by_date = is_valid_email_by_date(email_timestamp, test_time)
                                            if valid_email_by_date:
                                                if subject_type == email_vars.restock_order_type:
                                                    email_obj = EmailObjClasses.RestockEmailObj(email_subject,
                                                                                                email_from,
                                                                                                email_body,
                                                                                                email_timestamp)
                                                    email_vars.restock_email_list.append(email_obj)
                                                elif subject_type == email_vars.new_order_type:
                                                    email_obj = EmailObjClasses.NewOrderEmailObj(email_subject,
                                                                                                 email_from,
                                                                                                 email_body,
                                                                                                 email_timestamp)
                                                    email_vars.new_order_email_list.append(email_obj)
                                                else:
                                                    raise AssertionError("Unknown subject type: {}".format(subject_type))

                                                email_vars.email_obj_list.append(email_obj)

                                                relevant_email += 1

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
        return False

    return True


def test_email_subject(subject):
    if any(x.lower() in subject.lower() for x in email_vars.valid_subject_list):
        if email_vars.new_order_text.lower() in subject.lower():
            return email_vars.new_order_type, True
        elif any(x.lower() in subject.lower() for x in email_vars.restock_text_list):
            return email_vars.restock_order_type, True
        else:
            raise AssertionError(
                "Strange error here. The valid subject list doesn't line up with our verifications: {}".format(
                    email_vars.valid_subject_list))
    else:
        return "None", False

def convert_timestamp(timestamp_str):
    #print "current str: {}".format(timestamp_str)

    if "at" in timestamp_str:
        timestamp = datetime.datetime.strptime(timestamp_str, "%B %d, %Y at %I:%M %p")
    else:
        timestamp = datetime.datetime.strptime(timestamp_str,
                                               "{} {}, {} at %I:%M %p".format(datetime.datetime.today().month,
                                                                              datetime.datetime.today().day,
                                                                              datetime.datetime.today().year))
    print "Using timestamp: {}".format(timestamp)
    return timestamp


def is_valid_email_by_hours(email_date, hours_back):
    margin = datetime.timedelta(hours=hours_back)
    now = datetime.datetime.today()

    return (now - margin <= email_date)

def is_valid_email_by_date(email_date, test_timestamp_str):
    test_timestamp = convert_timestamp(test_timestamp_str)

    return (email_date >= test_timestamp)


def get_order_summary():
    total = float(0)
    for email_item in email_vars.email_obj_list:
        if email_item.subject_type != email_vars.new_order_type:
            continue
        prev_line = ""
        for line in email_item.body.split('\n'):
            if line.strip() == '':
                continue
            if "blog" in line and "$" in prev_line:
                current_order = float(prev_line.strip().split('$')[1])
                #print "Order total: {}".format(current_order)
                total = total + current_order

            prev_line = line
    print "Total from valid orders: ${}".format(total)
    return total

def export_restock_requests(restock_csv_path):
    for email_item in email_vars.email_obj_list:
        if email_item.subject_type != email_vars.restock_order_type:
            continue

        write_line_to_csv(email_item.order_info_dict, restock_csv_path)
    print "Finished writing to csv: {}".format(restock_csv_path)


def write_line_to_csv(results_dict, csv_path):
    if not os.path.exists(csv_path):
        #print "*DEBUG* Writing new csv path"
        open_file_as = 'wb'
    else:
        #print "*DEBUG* Appending to csv path"
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

new_arrival_folder = "[Gmail]/NewArrivals"
trash_folder = "[Gmail]/Trash"

new_order_text = "new order has arrived"
restock_text = ["Form Submission - RESTOCK REQUEST", "Form submission error"]
restock_csv_path = os.path.join(get_user_folder_path(), "GGRestockRequests.csv")


do_restock = False
do_order_summary = False
send_restock_email = True

test_restock_item = "Laurina Skinny Jeans"

test_date = "May 27, 2018 at 8:00 pm"

assert sort_emails(test_date), "Unable to sort emails properly"
print "\n\n\t\t\t\t*****\n\n"

if do_restock:
    clear_prev_csv_results(restock_csv_path)
    export_restock_requests(restock_csv_path)
elif do_order_summary:
    get_order_summary()
elif send_restock_email:
    print "If restock request item was not in a new order by that person, send the restock notification email"
    send_restock_list = []
    for restock_email in email_vars.restock_email_list:
        skip_restock = False
        if restock_email.item == test_restock_item:
            for new_order_email in email_vars.new_order_email_list:
                if new_order_email.person_name == restock_email.person_name:
                    print "Restock sender also has a new order"
                    if restock_email.item in new_order_email.item:
                        print "Don't send {} an email because they just ordered '{}'".format(new_order_email.person_name,
                                                                               restock_email.item)
                        skip_restock = True
                        break
                    else:
                        print "Restock sender ({}) order: {}. New order item: {}".format(new_order_email.person_name,
                                                                                         restock_email.item,
                                                                                         new_order_email.item)

            if not skip_restock:
                send_restock_list.append(restock_email.order_info_dict["EMAIL"])
    print "Current restock list: {}".format(send_restock_list)


