from frappe import _


def get_quotation_dashboard(data):
	return {
		"fieldname": "prevdoc_docname",
		"non_standard_fieldnames": {
			"Auto Repeat": "reference_document",
			"Sales Invoice": "custom_quotation",
		},
		"transactions": [
			{"label": _("Sales Order"), "items": ["Sales Order", "Sales Invoice"]},
			{"label": _("Subscription"), "items": ["Auto Repeat"]},
		],
	}
