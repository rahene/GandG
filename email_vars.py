from collections import OrderedDict

inbox_folder = "inbox"
new_order_folder = "New Orders"
trash_folder = "[Gmail]/Trash"
email_folder_list = [inbox_folder, new_order_folder, trash_folder]

new_order_text = "new order has arrived"
restock_text_list = ["Form Submission - RESTOCK REQUEST", "Form submission error"]
valid_subject_list = ["Form Submission - RESTOCK REQUEST", "Form submission error", "new order has arrived"]

restock_order_type = "restock"
new_order_type = "new order"

script_types = ['export restock file', 'order summary', 'send restock emails']

restock_email_list = []
new_order_email_list = []
latest_sort = None
