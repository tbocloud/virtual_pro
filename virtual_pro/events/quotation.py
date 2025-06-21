import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, getdate, nowdate


def update_service_request(doc, method):
    sp = frappe.get_doc("Enquiry", doc.custom_enquiry)
    if doc.docstatus == 1:
        sp.db_set('quotation', doc.name)
    elif doc.docstatus == 2:
        sp.db_set('quotation', "")
    sp.save()


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
	return _make_sales_invoice(source_name, target_doc)


def _make_sales_invoice(source_name, target_doc=None, ignore_permissions=False):
	customer = _make_customer(source_name, ignore_permissions)

	def set_missing_values(source, target):
		if customer:
			target.customer = customer.name
			target.customer_name = customer.customer_name

		target.flags.ignore_permissions = ignore_permissions
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	def update_item(obj, target, source_parent):
		target.cost_center = None
		target.stock_qty = flt(obj.qty) * flt(obj.conversion_factor)
		
		balance_qty = get_quotation_item_balance_qty(obj.name)
		if balance_qty <= 0:
			return None
		target.qty = min(obj.qty, balance_qty)  # Use balance or original qty, whichever is smaller

	def condition_check(row):
		# Only include items that have balance quantity and are not alternative
		if row.is_alternative:
			return False
		balance_qty = get_quotation_item_balance_qty(row.name)
		return balance_qty > 0

	doclist = get_mapped_doc(
		"Quotation",
		source_name,
		{
			"Quotation": {"doctype": "Sales Invoice", "validation": {"docstatus": ["=", 1]}},
			"Quotation Item": {
				"doctype": "Sales Invoice Item",
				"field_map": {"parent": "custom_quotation", "name": "custom_quotation_item"},  # Fixed typo
				"postprocess": update_item,
				"condition": condition_check,
			},
			"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "reset_value": True},
			"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
		},
		target_doc,
		set_missing_values,
		ignore_permissions=ignore_permissions,
	)

	return doclist


def get_quotation_item_balance_qty(quotation_item_id):
	quotation_item = frappe.get_doc("Quotation Item", quotation_item_id)
	
	invoiced_qty = frappe.db.sql("""
		SELECT SUM(qty) as total_qty
		FROM `tabSales Invoice Item` 
		WHERE custom_quotation_item = %s
		AND docstatus = 1
	""", (quotation_item_id,), as_dict=True)
	
	total_invoiced = invoiced_qty[0].total_qty or 0
	balance_qty = quotation_item.qty - total_invoiced
	
	return max(0, balance_qty)  


def _make_customer(source_name, ignore_permissions=False):
	quotation = frappe.db.get_value(
		"Quotation",
		source_name,
		["order_type", "quotation_to", "party_name", "customer_name"],
		as_dict=1,
	)

	if quotation.quotation_to == "Customer":
		return frappe.get_doc("Customer", quotation.party_name)

	existing_customer = None
	if quotation.quotation_to == "Lead":
		existing_customer = frappe.db.get_value("Customer", {"lead_name": quotation.party_name})
	elif quotation.quotation_to == "Prospect":
		existing_customer = frappe.db.get_value("Customer", {"prospect_name": quotation.party_name})

	if existing_customer:
		return frappe.get_doc("Customer", existing_customer)

	if quotation.quotation_to == "Lead":
		return create_customer_from_lead(quotation.party_name, ignore_permissions=ignore_permissions)
	elif quotation.quotation_to == "Prospect":
		return create_customer_from_prospect(quotation.party_name, ignore_permissions=ignore_permissions)

	return None


def create_customer_from_lead(lead_name, ignore_permissions=False):
	from erpnext.crm.doctype.lead.lead import _make_customer

	customer = _make_customer(lead_name, ignore_permissions=ignore_permissions)
	customer.flags.ignore_permissions = ignore_permissions

	try:
		customer.insert()
		return customer
	except frappe.MandatoryError as e:
		handle_mandatory_error(e, customer, lead_name)


def create_customer_from_prospect(prospect_name, ignore_permissions=False):
	from erpnext.crm.doctype.prospect.prospect import make_customer as make_customer_from_prospect

	customer = make_customer_from_prospect(prospect_name)
	customer.flags.ignore_permissions = ignore_permissions

	try:
		customer.insert()
		return customer
	except frappe.MandatoryError as e:
		handle_mandatory_error(e, customer, prospect_name)


def handle_mandatory_error(e, customer, lead_name):
	from frappe.utils import get_link_to_form

	mandatory_fields = e.args[0].split(":")[1].split(",")
	mandatory_fields = [_(customer.meta.get_label(field.strip())) for field in mandatory_fields]

	frappe.local.message_log = []
	message = _("Could not auto create Customer due to the following missing mandatory field(s):") + "<br>"
	message += "<br><ul><li>" + "</li><li>".join(mandatory_fields) + "</li></ul>"
	message += _("Please create Customer from Lead {0}.").format(get_link_to_form("Lead", lead_name))

	frappe.throw(message, title=_("Mandatory Missing"))


def validate_quotation_balance_qty(doc, method):
	"""Validate that sales invoice items don't exceed quotation balance"""
	for item in doc.items:
		if item.custom_quotation and item.custom_quotation_item:
			quotation_item = frappe.get_doc("Quotation Item", item.custom_quotation_item)
			
			invoiced_qty = frappe.db.sql("""
				SELECT SUM(qty) as total_qty
				FROM `tabSales Invoice Item` 
				WHERE custom_quotation_item = %s
				AND docstatus = 1
				AND name != %s
			""", (item.custom_quotation_item, item.name), as_dict=True)
			
			total_invoiced = invoiced_qty[0].total_qty or 0
			balance_qty = quotation_item.qty - total_invoiced
			
			if item.qty > balance_qty:
				frappe.throw(f"Row {item.idx}: Item {item.item_code} - Cannot invoice {item.qty} qty. Balance quantity available: {balance_qty}")


def update_quotation_status(doc, method):
	processed_quotations = set()  
	
	for item in doc.items:
		if item.custom_quotation and item.custom_quotation not in processed_quotations:
			quotation = frappe.get_doc("Quotation", item.custom_quotation)
			processed_quotations.add(item.custom_quotation)
			
			if doc.docstatus == 1:  
				fully_converted_items = 0
				
				for quotation_item in quotation.items:
					converted_qty = frappe.db.sql("""
						SELECT SUM(qty) as total_qty
						FROM `tabSales Invoice Item` 
						WHERE custom_quotation_item = %s
						AND docstatus = 1
					""", (quotation_item.name,), as_dict=True)
					
					total_converted = converted_qty[0].total_qty or 0
					
					if total_converted >= quotation_item.qty:
						fully_converted_items += 1
				
				total_quotation_items = len(quotation.items)
				if fully_converted_items >= total_quotation_items:
					quotation.db_set('status', "Ordered")
				elif fully_converted_items > 0:
					quotation.db_set('status', "Partially Ordered")
					
			elif doc.docstatus == 2:  
				fully_converted_items = 0
				
				for quotation_item in quotation.items:
					converted_qty = frappe.db.sql("""
						SELECT SUM(qty) as total_qty
						FROM `tabSales Invoice Item` 
						WHERE custom_quotation_item = %s
						AND docstatus = 1
					""", (quotation_item.name,), as_dict=True)
					
					total_converted = converted_qty[0].total_qty or 0
					
					if total_converted >= quotation_item.qty:
						fully_converted_items += 1
				
				total_quotation_items = len(quotation.items)
				if fully_converted_items >= total_quotation_items:
					quotation.db_set('status', "Ordered")
				elif fully_converted_items > 0:
					quotation.db_set('status', "Partially Ordered")
				else:
					quotation.db_set('status', "Open")
			
			quotation.save()