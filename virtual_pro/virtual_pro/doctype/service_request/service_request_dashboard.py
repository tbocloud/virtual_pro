from frappe import _

def get_data():
	return {
		"fieldname": "service_request",		
		"non_standard_fieldnames": {
			"Quotation": "custom_service_request"
			
        },
		"transactions": [
			{"label": _("Reference"), "items": ["Quotation"]},
						
		]
    }