# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class Enquiry(Document):
	pass

@frappe.whitelist()
def make_quotation(source_name, target_doc=None):

    def set_missing_values(source, target):
        
        source_data = frappe.get_doc("Services", source.services)

        for item in source_data.service_items:
            target.append("items", {
                'item_code': item.item_name,
                'uom': item.uom,
                'qty': item.qty,
                'price_list_rate': item.default_rate,
                'rate': item.default_rate,
            })

    doc = get_mapped_doc(
        "Enquiry",
        source_name,
        {
            "Enquiry": {
                "doctype": "Quotation",
                "field_map": {
                    "customer_company_name": "party_name",
                   "posting_date":  "transaction_date",
                }
            }
        },
        target_doc,
        set_missing_values
    )
    
   
    doc.insert(ignore_permissions=True)
    return doc