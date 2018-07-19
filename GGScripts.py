import GetCSVItemInfo, g
import datetime, time
import imaplib
import smtplib
import email
import csv
import os, sys
import email_vars
import EmailObjClasses
import traceback
import cPickle as pickle

# config = ConfigParser.ConfigParser()
# config.read("/etc/config.txt")

ORG_EMAIL = "@gritandgrey.com"
FROM_EMAIL = "hello" + ORG_EMAIL
FROM_PWD = "Adex1Presley2!"  # config.get("configuration", "password")
SMTP_SERVER = "imap.gmail.com"
SMTP_PORT = 993


def sort_emails(test_time):
    print "Update stored info from emails. Last search: {}".format(test_time)
    try:
        # mail = smtplib.SMTP_SSL(SMTP_SERVER)
        mail = imaplib.IMAP4_SSL(SMTP_SERVER)
        mail.login(FROM_EMAIL, FROM_PWD)

        for folder_name in email_vars.email_folder_list:
            print "\nSearching through {} folder\n".format(folder_name)
            mail.select(folder_name)
            # mail.list()    #get mailboxes available

            mail_type, data = mail.search(None, 'ALL')
            mail_ids = data[0]

            id_list = mail_ids.split()
            first_email_id = int(id_list[0])
            latest_email_id = int(id_list[-1])

            new_order_count = 0
            restock_request_count = 0
            # valid_email_count = 0
            email_too_old = False
            for i in range(latest_email_id, first_email_id - 1, -1):
                if not email_too_old:

                    typ, data = mail.fetch(i, '(RFC822)')
                    for response_part in data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_string(response_part[1])

                            email_date_tuple = email.utils.parsedate_tz(msg['Date'])
                            email_timestamp = datetime.datetime.fromtimestamp(
                                email.utils.mktime_tz(email_date_tuple))

                            valid_email_by_date = is_valid_email_by_date(email_timestamp, test_time)
                            if valid_email_by_date:

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


                                                if subject_type == email_vars.restock_order_type:
                                                    restock_request_count += 1
                                                    email_obj = EmailObjClasses.RestockEmailObj(email_subject,
                                                                                                email_from,
                                                                                                email_body,
                                                                                                email_timestamp)
                                                    email_vars.restock_email_list.append(email_obj)
                                                elif subject_type == email_vars.new_order_type:
                                                    new_order_count += 1
                                                    email_obj = EmailObjClasses.NewOrderEmailObj(email_subject,
                                                                                                 email_from,
                                                                                                 email_body,
                                                                                                 email_timestamp)
                                                    email_vars.new_order_email_list.append(email_obj)
                                                else:
                                                    raise AssertionError(
                                                        "Unknown subject type: {}".format(subject_type))

                                                # print "Restock email count: {}. New order count: {}".format(
                                                     # restock_request_count, new_order_count)

                            else:
                                print "Emails are now out of date. Break"
                                email_too_old = True
                                break
                else:
                    print "Breaking out of email searching"
                    break

    except Exception as e:
        print "Error: {}".format(e.message)
        traceback.print_exc()
        return False

    return True


def test_email_subject(subject):
    if "900" in subject:
        print "break"

    if any(x.lower() in subject.lower() for x in email_vars.valid_subject_list) and "Fwd: " not in subject:
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
    # print "current str: {}".format(timestamp_str)

    if len(timestamp_str) > 8:
        timestamp = datetime.datetime.strptime(timestamp_str, "%m/%d/%y %I:%M %p")
    else:
        timestamp = datetime.datetime.strptime(timestamp_str,
                                               "{}/{}/{} %I:%M %p".format(datetime.datetime.today().month,
                                                                          datetime.datetime.today().day,
                                                                          datetime.datetime.today().year))
    print "Using timestamp: {}".format(timestamp)
    return timestamp


def is_valid_email_by_hours(email_date, hours_back):
    margin = datetime.timedelta(hours=hours_back)
    now = datetime.datetime.today()

    return (now - margin <= email_date)


def is_valid_email_by_date(email_date, test_timestamp):
    # test_timestamp = convert_timestamp(test_timestamp_str)
    return (email_date >= test_timestamp)


def get_order_summary(test_timestamp):
    total = float(0)
    email_total = float(0)
    csv_total = float(0)

    email_vars.new_order_email_list.sort(key=lambda x: x.order_id)
    g.new_order_csv_item_list.sort(key=lambda x: x.order_id)

    if type(test_timestamp) == datetime.datetime:
        for email_item in email_vars.new_order_email_list:
            if email_item.timestamp >= test_timestamp:  # email item is after test timestamp
                email_total = email_total + email_item.order_total

        for item in g.new_order_csv_item_list:
            if item.timestamp >= test_timestamp:  # email item is after test timestamp
                csv_total = csv_total + item.order_total

        for new_order_item in g.new_order_obj_list:
            if new_order_item.timestamp >= test_timestamp:
                total = total + float(new_order_item.order_total)
    elif type(test_timestamp) == list:
        for email_item in email_vars.new_order_email_list:
            if test_timestamp[0] <= email_item.timestamp <= test_timestamp[1]:
                email_total = email_total + email_item.order_total

        for item in g.new_order_csv_item_list:
            if test_timestamp[0] <= item.timestamp <= test_timestamp[1]:  # email item is after test timestamp
                csv_total = csv_total + item.order_total

        for new_order_item in g.new_order_obj_list:
            if test_timestamp[0] <= new_order_item.timestamp <= test_timestamp[1]:
                total = total + float(new_order_item.order_total)

    # Make sure the total received from all 'new_order_items' matches the total received from (emails + csv items)
    assert abs(total - (
        csv_total + email_total)) < 5, "Something was off. The difference between the 'total' and 'email + csv total' "\
                                       "was off my more than 5. Total: {}. Added total: {}".format(
        total, csv_total + email_total)

    print "\n\nTotal since {}: ${}\n\n".format(test_timestamp, total)

    return total


def print_oldest_order_timestamp():
    t = None
    for email_item in email_vars.new_order_email_list:
        if not t:
            t = email_item.timestamp
        elif email_item.timestamp < t:  # if email item has older timestamp than t
            t = email_item.timestamp
    print t


def export_restock_requests(restock_csv_path):
    for email_item in email_vars.restock_email_list:
        write_line_to_csv(email_item.order_info_dict, restock_csv_path)
    print "Finished writing to csv: {}".format(restock_csv_path)


def write_line_to_csv(results_dict, csv_path):
    if not os.path.exists(csv_path):
        # print "*DEBUG* Writing new csv path"
        open_file_as = 'wb'
    else:
        # print "*DEBUG* Appending to csv path"
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


def get_user_date_input(prompt_text):
    x = 5
    valid_input = False
    while not valid_input and x > 0:
        begin_date = raw_input("{}\nUse format 'mm/dd/yy 8:00 pm'\n".format(prompt_text))
        type(begin_date)
        end_date = raw_input("Input ending date here (same format). If using through present time, "
                             "just hit ENTER.\n".format(prompt_text))
        type(end_date)
        try:
            begin_timestamp = convert_timestamp(begin_date)
            valid_input = True
            if end_date != '':
                end_timestamp = convert_timestamp(end_date)
                return [begin_timestamp, end_timestamp]
            return begin_timestamp
        except Exception as e:
            print "Dummy, use the right format please: {}".format(e.message)
            x -= 1


def get_user_digit_input(prompt_text, input_option_list):
    x = 5
    options_text = ""
    for input_option in input_option_list:
        options_text = "{}{} - {}\n".format(options_text, input_option_list.index(input_option) + 1, input_option)

    while x > 0:
        user_input = raw_input(
            "{} Input corresponding digit (or comma separated digits) with option\n{}".format(prompt_text,
                                                                                                options_text))
        type(user_input)

        if user_input == 'all':
            return input_option_list
        elif "," in user_input:
            input_list = []
            user_input = user_input.split(',')
            valid_input = True
            for index_input in user_input:
                if not index_input.strip().isdigit():
                    print "Invalid input, we need a digit, list of digits comma separated, or 'all'"
                    valid_input = False
                    break
                input_list.append(input_option_list[int(index_input.strip()) - 1])
            if valid_input:
                return input_list
        else:
            if not user_input.isdigit():
                print "Invalid input, we need a digit, list of digits comma separated, or 'all'"
            else:
                user_input = int(user_input)
                if (0 <= (user_input - 1) < len(input_option_list)):
                    return input_option_list[user_input - 1]

        x -= 1
    raise AssertionError("We didn't get a valid input within 5 tries")


def get_restock_email_list(restock_item_passed, restock_date, size_restock_input, color_restock_input):
    print "If restock request item ({}) was not in a new order by that person, send the restock notification email".format(
        restock_item_passed)
    send_restock_list = []
    for restock_item in g.restock_obj_list:
        skip_restock = False
        if restock_item.item == restock_item_passed and restock_item.timestamp >= restock_date and restock_item.size in size_restock_input and (
                color_restock_input and (x for x in restock_item.color.lower() if x in color_restock_input.lower()) or not color_restock_input):
            for new_order_item in g.new_order_obj_list:
                # print "Check if new order name '{}' matches restock item name '{}'".format(new_order_item.person_name, restock_item.person_name)
                if new_order_item.person_name == restock_item.person_name and restock_item.item in new_order_item.item_list:
                    print "{}, who requested a restock of {}, also has a new order with items {} that contains the restock item".format(
                        restock_item.person_name, restock_item_passed, new_order_item.item_list)

                    # new order after restock request, but order for a different color = add to list
                    if new_order_item.timestamp > restock_item.timestamp and color_restock_input and not (
                            x for x in restock_item.color.lower() if x in color_restock_input.lower()):
                        print "{} ordered {} on {}, after requesting a restock on {}, but the color requested ({}) was"\
                              " different than the color ordered ({}),"\
                              " so send them a restock notification.".format(new_order_item.person_name,
                                                                             new_order_item.item_list,
                                                                             new_order_item.timestamp,
                                                                             restock_item.timestamp,
                                                                             restock_item.color,
                                                                             new_order_item.order_info_dict)
                        skip_restock = False
                    # else if new order after restock request for same item, don't add to list
                    elif new_order_item.timestamp > restock_item.timestamp:
                        print "{} ordered {} on {}, after requesting a restock on {}, and there was either no color or " \
                              "it was the same. Don't send a restock notification.".format(new_order_item.person_name,
                                                                             new_order_item.item_list,
                                                                             new_order_item.timestamp,
                                                                             restock_item.timestamp,
                                                                             restock_item.color,
                                                                             new_order_item.order_info_dict)
                        skip_restock = True
                    # else (restock request is after the new order, add to list)
                    else:
                        print "{} ordered {} on {} before restock request on {}. Color info: {} Send notification "\
                              "to this person.".format(new_order_item.person_name, new_order_item.item_list,
                                                       new_order_item.timestamp, restock_item.timestamp,
                                                       new_order_item.order_info_dict)
                        skip_restock = False
                        break

            if not skip_restock:
                # print "Add {} to restock list. Name: {}".format(restock_item.order_info_dict["item"],
                                                                # restock_item.person_name)
                send_restock_list.append(restock_item.email)
    print "\n\n\nCurrent restock email list: {}\n\n\n".format(', '.join(send_restock_list))


def is_restock_removal_needed(restock_email, new_order_email):
    assert restock_email.item in new_order_email.item_list, "Unexpected logic"
    skip_restock = False

    if restock_email.timestamp > new_order_email.timestamp:
        print "Restock request by {} was on {} after their new order ({}). Keep them on the list".format(
            restock_email.person_name, restock_email.timestamp, new_order_email.timestamp)
    else:
        if restock_email.order_info_dict["SIZE"] in new_order_email.order_info_dict[restock_email.item]:
            print "Restock request by {} was before their order for {} and they ordered a size that was requested.".format(
                restock_email.person_name, restock_email.item)
        else:
            print "{} ordered a {} after they requested a restock, but the sizes were different. Take them off the list.".format(
                restock_email.person_name, restock_email.item)
            skip_restock = True

    return skip_restock


def get_restock_item_options(item_for_restock, info_category):
    """
    Get restock requests present for a specific size or color
    :param item_for_restock: 
    :param info_category: 
    :return: 
    """
    option_list = []
    for restock_email in email_vars.restock_email_list:
        if restock_email.item == item_for_restock:
            item_options = restock_email.order_info_dict[info_category].split(',')
            for option in item_options:
                if option.strip() == '':
                    continue
                elif option.strip() in option_list:
                    continue
                else:
                    option_list.append(option.strip())
    return option_list


def get_all_restock_item_options():
    option_list = []
    for restock_email in email_vars.restock_email_list:
        if restock_email.item.strip() in option_list:
            continue
        else:
            option_list.append(restock_email.item.strip())
    return option_list


def call_restock_test_functions(passed_restock_item, restock_date_passed):
    color_restock_input = None
    color_list = get_restock_item_options(passed_restock_item, "COLOR")
    if color_list:
        color_restock_input = get_user_digit_input(
            "These color ways have been requested to be restocked. Input which color got restocked or 'all' "
            "for all colors: ",
            color_list)
        if type(color_restock_input) == str:
            color_restock_input = [color_restock_input.lower()]

    size_list = get_restock_item_options(passed_restock_item, "SIZE")
    if size_list:
        size_restock_input = get_user_digit_input(
            "These sizes have been requested to be restocked. Input which size got restocked or 'all' for all sizes: ",
            size_list)
        if type(size_restock_input) == str:
            size_restock_input = [size_restock_input]
    else:
        raise AssertionError("We need a size restock input")

    get_restock_email_list(passed_restock_item, restock_date_passed, size_restock_input, color_restock_input)


new_order_text = "new order has arrived"
restock_text = ["Form Submission - RESTOCK REQUEST", "Form submission error"]
restock_csv_path = os.path.join(get_user_folder_path(), "GGRestockRequests.csv")
pickle_file_path = os.path.join(os.getcwd(), "p.pkl")

debug_mode = False

if debug_mode:
    script_type = "send restock emails"
    test_date_timestamp = convert_timestamp("06/04/18 8:00 pm")
    restock_item = "Laurina Skinny Jeans"
else:
    script_type = get_user_digit_input("Which script do you want to run?", email_vars.script_types)

    #test_date_timestamp = get_user_date_input()

test_param = None
try:
    if os.path.exists(pickle_file_path):
        test_param = pickle.load(open(pickle_file_path, 'rb'))

        if test_param:
            email_vars.restock_email_list = test_param[0]
            email_vars.new_order_email_list = test_param[1]
            g.restock_csv_item_list = test_param[2]
            g.new_order_csv_item_list = test_param[3]
            email_vars.latest_sort = test_param[4]
except EOFError:
    print "EOFError caught. Empty pickle file at: {}".format(pickle_file_path)

# Populate the csv variables if they don't exist
if not g.restock_csv_item_list:
    print "Running script to get restocks from csv"
    GetCSVItemInfo.add_restock_items_from_restocks_csv()     # restock items are in g.restock_obj_list
    # latest restock item date is in g.latest_restock_from_csv
if not g.new_order_csv_item_list:
    print "Running script to get new orders from csv"
    GetCSVItemInfo.add_new_order_items_from_orders_csv()     # new order items are in g.new_order_obj_list
    # latest new order item date is in g.latest_order_from_csv
if not email_vars.latest_sort:
    email_vars.latest_sort = min(g.latest_restock_from_csv, g.latest_order_from_csv)


# Now populate the email variables
assert sort_emails(email_vars.latest_sort), "Unable to sort emails properly"
print "\n\n\t\t\t\t*****\n\n"
email_vars.latest_sort = datetime.datetime.now()


# Dump all variables independently
pObj = (email_vars.restock_email_list, email_vars.new_order_email_list, g.restock_csv_item_list, g.new_order_csv_item_list,
        email_vars.latest_sort)
test_param = pickle.dump(pObj, open(pickle_file_path, 'wb'))


# Combine variables into one iterable variable
g.restock_obj_list = email_vars.restock_email_list + g.restock_csv_item_list
g.new_order_obj_list = email_vars.new_order_email_list + g.new_order_csv_item_list


keep_going = True
while keep_going:

    if script_type == 'export restock file':
        clear_prev_csv_results(restock_csv_path)
        export_restock_requests(restock_csv_path)
    elif script_type == 'order summary':
        input_text = "Run order summary script. Use start date of:"
        timestamp_range = get_user_date_input(input_text)
        # If user wants a range of time, a list is returned
        get_order_summary(timestamp_range)
    elif script_type == 'send restock emails':

        restock_item = get_user_digit_input("Input a single item that got restocked", input_option_list=get_all_restock_item_options())
        assert not type(restock_item) == list, "We are only allowing one restock item per loop"

        restock_date = get_user_date_input(prompt_text="Run restock request script. Use start point:")
        call_restock_test_functions(restock_item, restock_date)

    keep_going = get_user_digit_input("Are you finished running this script?", input_option_list=["Yes", "No"])
    keep_going = keep_going == "No"
