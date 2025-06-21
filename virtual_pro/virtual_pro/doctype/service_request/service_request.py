# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class ServiceRequest(Document):
    def on_submit(self):
        if not self.project_id:
            frappe.throw(_("Project is not set. Please create a project first."))
    
            

@frappe.whitelist()
def create_project_from_service_request(services, customer_company_name, service_request_name):
   
    project = frappe.new_doc("Project")
    
    base_name = services or "Default Project Name"
    unique_project_name = generate_project_name_with_sr(base_name)
    
    project.project_name = unique_project_name
    project.customer = customer_company_name or "Default Customer"
    
    project.insert()
    frappe.db.commit()
    
    return project.name
  

def generate_project_name_with_sr(base_name):
    counter = 1
    
    while True:
        project_name = f"{base_name} - SR{counter}"
        
        if not frappe.db.exists("Project", {"project_name": project_name}):
            return project_name
        
        counter += 1
        
        if counter > 999:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"{base_name} - SR{timestamp}"


@frappe.whitelist()
def mak_sales_invoice(source_name, target_doc=None):

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
        "Service Request",
        source_name,
        {
            "Service Request": {
                "doctype": "Sales Invoice",
                "field_map": {
                    "customer_company_name": "customer",
                    "project_id": "project",
                    "posting_date": "due_date",
                    "enquiry": "custom_enquiry",
                }
            }
        },
        target_doc,
        set_missing_values
    )
    
   
    doc.insert(ignore_permissions=True)
    return doc