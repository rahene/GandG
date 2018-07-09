class RestockRequestObj():
    def __init__(self, timestamp, person_name, item, size, color, email):
        self.timestamp = timestamp
        self.person_name = person_name
        self.item = item
        self.size = size
        self.color = color
        self.email = email


class NewOrderObj():
    def __init__(self, order_id, timestamp, person_name, order_info_dict, item_list, subtotal, taxes, shipping, refund, order_total):
        self.order_id = order_id
        self.timestamp = timestamp
        self.person_name = person_name
        self.order_info_dict = order_info_dict
        self.item_list = item_list
        self.subtotal = float(subtotal)
        self.taxes = float(taxes)
        self.shipping = float(shipping)
        self.refund = float(refund)
        self.order_total = float(order_total)
