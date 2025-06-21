from frappe import _

def get_data():
	return {
		"fieldname": "service_request",		
		"non_standard_fieldnames": {
			"Sales Invoice": "custom_enquiry",
			"Task": "custom_service_request"
			
        },
		"transactions": [
			{"label": _("Reference"), "items": ["Quotation", "Task"]},
						
		]
    }