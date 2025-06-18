import frappe


def update_service_request(doc, method):
    sp = frappe.get_doc("Service Request", doc.custom_service_request)
    if doc.docstatus == 1:
        sp.db_set('status', "Completed")
    elif doc.docstatus == 2:
        sp.db_set('status', "To Sales Invoice")
    sp.save()