import email_vars
import csv
from collections import OrderedDict

class OrderInfo:
    def __init__(self, name, email, item, size, color, date):
        self.name = name
        self.email = email
        self.item = item
        self.size = size
        self.color = color
        self.date = date

class CSVObj:
    def __init__(self, timestamp, person_name, order_info_dict):
        self.timestamp = timestamp
        self.person_name = person_name
        self.order_info_dict = order_info_dict


class RestockCSVObj(CSVObj):
    def __init__(self, timestamp, person_name, order_info_dict, item):
        CSVObj.__init__(self, timestamp, person_name, order_info_dict)
        self.item = item


class NewOrderCSVObj(CSVObj):
    def __init__(self, timestamp, person_name, order_info_dict, item_list, subtotal, taxes, shipping, refund, order_total):
        CSVObj.__init__(self, timestamp, person_name, order_info_dict)
        self.item_list = item_list
        self.subtotal = subtotal
        self.taxes = taxes
        self.shipping = shipping
        self.refund = refund
        self.order_total = order_total
