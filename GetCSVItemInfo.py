import ConfigParser
import smtplib
import datetime, time
import imaplib
import itertools
import csv
import os, sys
import g
import CustomerObjClasses
import traceback
import cPickle as pickle



def convert_new_order_timestamp(timestamp_str):
    # print "current str: {}".format(timestamp_str)
    k = timestamp_str.index(" ", timestamp_str.index(" ") + 1)
    timestamp_str = timestamp_str[0:k].replace('-', '/')

    timestamp = datetime.datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S")
    # print "Using timestamp: {}".format(timestamp)
    return timestamp


def convert_restock_timestamp(timestamp_str):
    assert len(timestamp_str) > 4, "Something wrong with the timestamp str: {}".format(timestamp_str)
    # print "Convert string timestamp: {}".format(timestamp_str)
    if len(timestamp_str) < 10:
        timestamp = datetime.datetime.strptime(timestamp_str, "%m/%d/%y")
    elif len(timestamp_str) > 10:
        timestamp = datetime.datetime.strptime(timestamp_str, "%m/%d/%Y %H:%M:%S")
    else:
        timestamp = datetime.datetime.strptime(timestamp_str, "%m/%d/%Y")
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
        latest_restock_date = None
        for row in csvreader:
            if len(row["Submitted On"]) > 0:
                timestamp = convert_restock_timestamp(row["Submitted On"])
            else:
                print "\n*Empty timestamp cell for '{}' ordering '{}', just use the previous timestamp NBD*\n".format(
                    row["NAME"], row["ITEM"])
            csv_obj = CustomerObjClasses.RestockRequestObj(timestamp=timestamp, person_name=row["NAME"],
                                                           item=row["ITEM"], size=row["SIZE"], color=row["COLOR(S)"],
                                                           email=row["EMAIL"])
            g.restock_csv_item_list.append(csv_obj)

            if not latest_restock_date:
                print "No current latest new order date, set timestamp to '{}'".format(timestamp)
                latest_restock_date = timestamp
            elif timestamp > latest_restock_date:
                print "Current timestamp '{}' is greater than compared value '{}'. Update latest.".format(
                    latest_restock_date, timestamp)
                latest_restock_date = timestamp

        g.latest_restock_from_csv = latest_restock_date


def add_new_order_items_from_orders_csv():
    latest_new_order_date = None

    print "Get new order items"
    new_order_csv_path = os.path.join(os.getcwd(), "orders.csv")

    with open(new_order_csv_path, 'rb') as csvfile:
        all_lines = csvfile.readlines()

    with open(new_order_csv_path, 'rb') as csvfile:
        csvreader = csv.DictReader(csvfile)

        item_list = []
        order_info_dict = {}
        timestamp = None
        person_name = None
        subtotal = None
        taxes = None
        shipping = None
        refund = None
        total = None

        for i, row in enumerate(csvreader):

            order_id = row["Order ID"]

            if row["Paid at"] != '':
                timestamp = convert_new_order_timestamp(row["Paid at"])
            if row["Shipping Name"] != '':
                person_name = row["Shipping Name"]
            if row["Subtotal"] != '':
                subtotal = row["Subtotal"]
            if row["Taxes"] != '':
                taxes = row["Taxes"]
            if row["Shipping"] != '':
                shipping = row["Shipping"]
            if row["Amount Refunded"] != '':
                refund = row["Amount Refunded"]
            if row["Total"] != '':
                total = row["Total"]

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
                csv_obj = CustomerObjClasses.NewOrderObj(order_id=order_id, timestamp=timestamp, person_name=person_name,
                                                         order_info_dict=order_info_dict, item_list=item_list,
                                                         subtotal=subtotal, taxes=taxes, shipping=shipping,
                                                         refund=refund, order_total=total)
                g.new_order_csv_item_list.append(csv_obj)
                item_list = []
                order_info_dict = {}

            if not latest_new_order_date:
                print "No current latest new order date, set timestamp to '{}'".format(timestamp)
                latest_new_order_date = timestamp
            elif timestamp > latest_new_order_date:
                print "Current timestamp '{}' is greater than compared value '{}'. Update latest.".format(latest_new_order_date, timestamp)
                latest_new_order_date = timestamp

        g.latest_order_from_csv = latest_new_order_date



#add_new_order_items_from_orders_csv()
#add_restock_items_from_restocks_csv()