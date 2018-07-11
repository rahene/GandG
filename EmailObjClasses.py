import email_vars
import re
from collections import OrderedDict

class OrderInfo:
    def __init__(self, name, email, item, size, color, date):
        self.name = name
        self.email = email
        self.item = item
        self.size = size
        self.color = color
        self.date = date

class EmailObj:
    def __init__(self, subject, sender, body, timestamp, subject_type, person_name):
        self.subject = subject
        self.sender = sender
        self.body = body
        self.timestamp = timestamp
        self.subject_type = subject_type
        self.person_name = person_name

class RestockEmailObj(EmailObj):
    def __init__(self, subject, sender, body, timestamp):
        person_name = self.get_person_name(body)
        EmailObj.__init__(self, subject, sender, body, timestamp, email_vars.restock_order_type, person_name)
        buffer_item = self.get_order_info_item()
        self.order_info_dict = buffer_item[0]
        # self.order_info_item = buffer_item[1]
        self.item = self.order_info_dict["ITEM"]
        self.size = self.order_info_dict["SIZE"]
        self.color = self.order_info_dict["COLOR"].split(',')
        self.email = self.order_info_dict["EMAIL"]


    def get_order_info_item(self):
        results_dict = OrderedDict()
        column_names = ["NAME", "EMAIL", "ITEM", "SIZE", "COLOR"]
        email_body_list = self.body.replace('\n', '').split('\r')
        for line in email_body_list:
            for cname in column_names:
                if cname in line and ":" in line:
                    if line.split(":")[1].replace('*', '').strip() == '':
                        results_dict[cname] = email_body_list[email_body_list.index(line) + 1].strip().lower()
                    else:
                        results_dict[cname] = line.split(":")[1].replace('*', '').strip().lower()
                    break
        if not results_dict.has_key("COLOR"):
            results_dict["COLOR"] = ''

        results_dict["DATE"] = self.timestamp

        if not results_dict.has_key("NAME") or not results_dict.has_key("EMAIL") \
                or not results_dict.has_key("ITEM") or not results_dict.has_key("DATE"):
            raise AssertionError(
                "Failure in finding result item. Person name: {}. Timestamp: {}. Subject: {}".format(self.person_name,
                                                                                                     self.timestamp,
                                                                                                     self.subject))

        if not results_dict.has_key("COLOR"):
            results_dict["COLOR"] = None
        if not results_dict.has_key("SIZE"):
            results_dict["SIZE"] = None
        order_info_item = OrderInfo(results_dict["NAME"], results_dict["EMAIL"], results_dict["ITEM"],
                                    results_dict["SIZE"], results_dict["COLOR"], results_dict["DATE"])
        return results_dict, order_info_item

    @staticmethod
    def get_person_name(email_body):
        person_name = None
        email_body_list = email_body.replace('\n', '').split('\r')
        for line in email_body_list:
            if "NAME:" in line:
                if line.split(":")[1].strip() == '':
                    person_name = email_body_list[email_body_list.index(line) + 1].strip().lower()
                else:
                    person_name = line.split(":")[1].strip().lower()
                break
        assert person_name, "No person name found for restock email object"
        return person_name


class NewOrderEmailObj(EmailObj):
    def __init__(self, subject, sender, body, timestamp):
        person_name = self.get_person_name(body)
        EmailObj.__init__(self, subject, sender, body, timestamp, email_vars.new_order_type, person_name)
        self.order_info_dict = self.get_order_info(body)    # keys = item, values = string containing color/size
        self.item_list = self.get_order_item_list()
        self.order_total = self.get_order_total()
        self.order_id = self.get_order_id()

        if "hudson" in person_name:
            print "break next"

        print "Creating new order email obj. Subject: {}. Name: {}. Total: {}".format(subject, person_name, self.order_total)

    def get_order_id(self):
        return int(re.search(r'\((.*?)\)', self.subject).group(1))


    def get_order_total(self):
        prev_line = ""
        for line in self.body.split('\n'):
            if line.strip() == '':
                continue
            if "Discounts" in line and "$" in prev_line:
                return float(prev_line.strip().split('$')[1])
            if "blog" in line and "$" in prev_line:
                return float(prev_line.strip().split('$')[1])

            prev_line = line

    @staticmethod
    def get_order_info(email_body):
        item_dict = {}
        email_body_list = email_body.replace('\n', '').split('\r')
        for index, line in enumerate(email_body_list):
            if "SQ" in email_body_list[index] and line.split('SQ')[1].isdigit():
                item_dict[email_body_list[index - 1].strip()] = email_body_list[index + 1].strip().lower()
                continue

        return item_dict

    def get_person_name(self, email_body):
        billed_name = None
        shipped_name = None
        email_body_list = email_body.replace('\n', '').split('\r')
        for index, line in enumerate(email_body_list):
            if "BILLED TO" in line and "SHIPPING TO" in email_body_list[index + 1]:
                billed_name = email_body_list[index + 2].strip()
                if self.is_phone_number(email_body_list[index + 9].strip()):
                    shipped_name = email_body_list[index + 10].strip()
                elif self.is_phone_number(email_body_list[index + 8].strip()):
                    shipped_name = email_body_list[index + 9].strip()
                elif "@" in email_body_list[index + 8].strip():
                    shipped_name = email_body_list[index + 9].strip()
                else:
                    shipped_name = email_body_list[index + 8].strip()
            elif "BILLED TO" in line and "SHIPPING TO" not in email_body_list[index + 1]:
                billed_name = email_body_list[index + 1].strip()

        if billed_name and shipped_name and (billed_name == shipped_name):
            person_name = billed_name
        elif shipped_name:
            person_name = shipped_name
        else:
            person_name = billed_name

        assert person_name, "No person name found for new order email object"
        return person_name.lower()

    @staticmethod
    def is_phone_number(str_input):
        if str_input.isdigit() and len(str_input) == 10:
            return True
        elif (sum(c.isdigit() for c in str_input)) == 10:
            return True
        elif (str_input[0] == '+' or str_input[0] == '1') and (sum(c.isdigit() for c in str_input)) == 11:
            return True
        else:
            return False

    def get_order_item_list(self):
        return self.order_info_dict.keys()