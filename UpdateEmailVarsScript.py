import ConfigParser
import smtplib
import datetime, time
import imaplib
import itertools
import csv
import os, sys
import email_vars
import CSVObjClasses
import traceback
import cPickle as pickle



def convert_timestamp(timestamp_str):
    # print "current str: {}".format(timestamp_str)
    k = timestamp_str.index(" ", timestamp_str.index(" ") + 1)
    timestamp_str = timestamp_str[0:k].replace('-', '/')

    timestamp = datetime.datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S")
    print "Using timestamp: {}".format(timestamp)
    return timestamp


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


def add_restock_items_from_restocks_csv():
    print "Get restock items"
    restock_csv_path = os.path.join(os.getcwd(), "G+G Restocks.csv")

    with open(restock_csv_path, 'rb') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            order_info_dict = {"SIZE": row["SIZE"], "COLOR": row["COLOR(S)"]}
            csv_obj = CSVObjClasses.RestockCSVObj(timestamp=row["Submitted on"], person_name=row["NAME"],
                                                  order_info_dict=order_info_dict, item=row["ITEM"])
            email_vars.restock_email_list.append(csv_obj)


def add_new_order_items_from_orders_csv():
    print "Get restock items"
    new_order_csv_path = os.path.join(os.getcwd(), "orders.csv")

    with open(new_order_csv_path, 'rb') as csvfile:
        all_lines = csvfile.readlines()

    with open(new_order_csv_path, 'rb') as csvfile:
        csvreader = csv.DictReader(csvfile)

        item_list = []
        order_info_dict = {}
        timestamp = None
        person_name = None

        for i, row in enumerate(csvreader):

            order_id = row["Order ID"]
            subtotal = row["Subtotal"]

            if row["Paid at"] != '':
                timestamp = convert_timestamp(row["Paid at"])
            if row["Shipping Name"] != '':
                person_name = row["Shipping Name"]

            item_list.append(row["Lineitem name"])
            size_and_color = row["Lineitem variant"]
            order_info_dict[row["Lineitem name"]] = size_and_color

            try:
                next_order_id = all_lines[i + 2].split(',')[0].replace('"', '')
                if order_id in next_order_id:
                    same_order = True
                else:
                    same_order = False
            except IndexError:
                print "Catching index error"
                same_order = False

            if same_order:  # if we are looking at the same order, continue on
                continue
            else:
                assert timestamp, "No timestamp found"
                assert person_name, "No name found"
                csv_obj = CSVObjClasses.RestockCSVObj(timestamp=timestamp, person_name=person_name,
                                                      order_info_dict=order_info_dict, item=item_list)
                email_vars.restock_email_list.append(csv_obj)
                item_list = []
                order_info_dict = {}



add_new_order_items_from_orders_csv()
add_restock_items_from_restocks_csv()