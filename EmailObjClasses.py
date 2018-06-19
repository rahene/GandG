import email_vars
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
        self.item = self.get_restock_item()


    def get_restock_item(self):
        return self.order_info_dict["ITEM"]

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

    @staticmethod
    def get_order_info(email_body):
        item_dict = {}
        email_body_list = email_body.replace('\n', '').split('\r')
        for index, line in enumerate(email_body_list):
            if "SQ" in email_body_list[index] and line.split('SQ')[1].isdigit():
                item_dict[email_body_list[index - 1].strip()] = email_body_list[index + 1].strip().lower()
                continue

        return item_dict

    @staticmethod
    def get_person_name(email_body):
        billed_name = None
        shipped_name = None
        email_body_list = email_body.replace('\n', '').split('\r')
        for index, line in enumerate(email_body_list):
            if "BILLED TO" in line and "SHIPPING TO" in email_body_list[index + 1]:
                billed_name = email_body_list[index + 2].strip()
                if email_body_list[index + 9].strip().isdigit():
                    shipped_name = email_body_list[index + 10].strip()
                elif email_body_list[index + 8].strip().isdigit():
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

    def get_order_item_list(self):
        return self.order_info_dict.keys()