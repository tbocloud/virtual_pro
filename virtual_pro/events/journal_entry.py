import frappe

@frappe.whitelist()
def unlink_invoice_on_journal_cancel(doc, method):
    if doc.doctype != "Journal Entry":
        return

    linked_invoices = frappe.get_all(
        "Sales Invoice",
        filters={"custom_ref_journal_entry": doc.name},
        fields=["name"]
    )

    for inv in linked_invoices:
        frappe.db.set_value("Sales Invoice", inv.name, "custom_ref_journal_entry", None)
        frappe.msgprint(f"Removed Journal Entry reference from Sales Invoice <b>{inv.name}</b>.")
