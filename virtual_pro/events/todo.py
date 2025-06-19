import frappe
from frappe.utils import today

def before_save(doc, method=None):
    if not doc.assined_date: 
        doc.assined_date = today()
