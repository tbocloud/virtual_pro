# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document

# class ServiceRequest(Document):
#     pass

# @frappe.whitelist()
# def create_project_from_service_request():
#     try:
#         project = frappe.new_doc("Project")
#         project.project_name = "Test Project"  # Static value
#         project.customer = "viji"     # Static value
        
#         project.insert()
#         frappe.db.commit()
        
#         return project.name
#     except Exception as e:
#         frappe.throw(f"Error creating project: {str(e)}")
import frappe
from frappe.model.document import Document

class ServiceRequest(Document):
    def on_submit(self):
        self.db_set("status", "Open")
        """Automatically mark the linked Enquiry as Converted on submission."""
        if self.enquiry_reference:
            try:
                frappe.db.set_value("Enquiry", self.enquiry_reference, "status", "Converted")
                frappe.msgprint(f"Enquiry {self.enquiry_reference} marked as Converted.")
            except Exception as e:
                frappe.log_error(f"Failed to update Enquiry status: {e}", "ServiceRequest on_submit")


@frappe.whitelist()
def create_project_from_service_request(services, customer_company_name, service_request_name):
    try:
        # Create the project
        project = frappe.new_doc("Project")
        
        # Generate unique project name with SR numbering
        base_name = services or "Default Project Name"
        unique_project_name = generate_project_name_with_sr(base_name)
        
        project.project_name = unique_project_name
        project.customer = customer_company_name or "Default Customer"
        
        project.insert()
        frappe.db.commit()
        
        # DON'T update Service Request here - let client-side handle it
        return project.name
    except Exception as e:
        frappe.throw(f"Error creating project: {str(e)}")

def generate_project_name_with_sr(base_name):
    """Generate project name like 'Service Name - SR1', 'Service Name - SR2', etc."""
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
