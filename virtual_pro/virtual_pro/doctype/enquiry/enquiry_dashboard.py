from frappe import _

def get_data():
	return {
		"fieldname": "enquiry",		
		"non_standard_fieldnames": {
			"Service Request": "enquiry"
			
        },
		"transactions": [
			{"label": _("Reference"), "items": ["Service Request"]},
						
		]
    }