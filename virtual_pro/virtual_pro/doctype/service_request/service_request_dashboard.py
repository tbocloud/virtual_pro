from frappe import _

def get_data():
	return {
		"fieldname": "service_request",		
		"non_standard_fieldnames": {
			"Task": "custom_service_request"
			
        },
		"internal_links": {
			"Sales Invoice": "sales_invoice",
			
        },
		
		"transactions": [
			{"label": _("Reference"), "items": ["Sales Invoice", "Task"]},
						
		]
    }