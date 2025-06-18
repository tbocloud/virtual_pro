import frappe
from frappe import _

def update_service_request(doc, method):
    sp = frappe.get_doc("Service Request", doc.custom_service_request)
    if doc.docstatus == 1:
        sp.db_set('status', "To Sales Invoice")
    elif doc.docstatus == 2:
        sp.db_set('status', "To Sales Order")
    sp.save()


def create_tasks(doc, method):
        frappe.log_error(f"create_tasks called for doc: {doc.name}")
        
        if not doc.custom_service_request:
            frappe.log_error("No custom_service_request found")
            return
        
        # Fix: Use get_value with proper field name
        step = frappe.db.get_value("Service Request", doc.custom_service_request, "services")
        if not step:
            frappe.log_error(f"No services found for Service Request: {doc.custom_service_request}")
            return
        
        frappe.log_error(f"Found service: {step}")
        
        try:
            service = frappe.get_doc("Services", step)
            frappe.log_error(f"Service doc loaded: {service.name}")
        except Exception as e:
            frappe.log_error(f"Error loading service doc: {e}")
            return

        def get_users_by_role(role):
            if not role:
                return []
            
            # Get only actual users, not reports or other doctypes
            users = frappe.get_all("Has Role", 
                filters={
                    "role": role,
                    "parenttype": "User"  # This ensures we only get User records
                }, 
                fields=["parent"]
            )
            
            # Filter out system users and get only active users
            user_list = []
            for user_doc in users:
                user = user_doc.parent
                if frappe.db.exists("User", user):
                    user_data = frappe.db.get_value("User", user, ["enabled", "user_type"], as_dict=True)
                    if user_data and user_data.enabled == 1 and user_data.user_type == "System User":
                        user_list.append(user)
            
            frappe.log_error(f"Active users for role {role}: {user_list}")
            return user_list

        def create_task_and_todos(parent_task_name=None):
            if hasattr(service, 'parent_steps') and service.parent_steps:
                frappe.log_error(f"Processing {len(service.parent_steps)} parent steps")
                
                for parent in service.parent_steps:
                    frappe.log_error(f"Processing parent step: {parent.step_name}")
                    
                    parent_users = get_users_by_role(parent.assign_by_role) if hasattr(parent, 'assign_by_role') and parent.assign_by_role else []
                    
                    # Create parent task
                    try:
                        parent_task = frappe.get_doc({
                            "doctype": "Task",
                            "subject": parent.step_name,
                            "status": "Open",
                            "project": doc.project if hasattr(doc, 'project') and doc.project else None,
                            "description": f"Task created from Service {parent.step_name}",
                            "custom_service_request": doc.custom_service_request,
                        })
                        parent_task.insert(ignore_permissions=True)
                        frappe.log_error(f"Parent task created: {parent_task.name}")
                        
                        # Create ToDos for parent task
                        for user in parent_users:
                            try:
                                todo = frappe.get_doc({
                                    "doctype": "ToDo",
                                    "description": parent_task.subject,
                                    "reference_type": "Task",
                                    "reference_name": parent_task.name,
                                    "status": "Open",
                                    "assigned_by": frappe.session.user,
                                    "allocated_to": user
                                })
                                todo.insert(ignore_permissions=True)
                                frappe.log_error(f"ToDo created for user {user}")
                            except Exception as e:
                                frappe.log_error(f"Error creating ToDo for user {user}: {e}")
                        
                        # Process child steps for this parent
                        if hasattr(service, 'child_steps') and service.child_steps:
                            for child in service.child_steps:
                                if hasattr(child, 'parent_step') and child.parent_step == parent.step_name:
                                    create_child_task(child, parent_task.name)
                                    
                    except Exception as e:
                        frappe.log_error(f"Error creating parent task {parent.step_name}: {e}")
            
            # Handle child steps without parents
            elif hasattr(service, 'child_steps') and service.child_steps:
                frappe.log_error(f"Processing {len(service.child_steps)} child steps without parents")
                
                for child in service.child_steps:
                    if not hasattr(child, 'parent_step') or not child.parent_step:
                        create_child_task(child, parent_task_name)
        
        def create_child_task(child, parent_task_name=None):
            frappe.log_error(f"Creating child task: {child.step_name}")
            
            users = get_users_by_role(child.assign_by_role) if hasattr(child, 'assign_by_role') and child.assign_by_role else []
            
            task_doc = {
                "doctype": "Task",
                "subject": child.step_name,
                "status": "Open",
                "description": f"Task created from Service {child.step_name}",
                "custom_service_request": doc.custom_service_request,
            }
            
            if hasattr(doc, 'project') and doc.project:
                task_doc["project"] = doc.project
            
            if parent_task_name:
                task_doc["parent_task"] = parent_task_name
            
            task = frappe.get_doc(task_doc)
            task.insert(ignore_permissions=True)
            for user in users:
                    todo = frappe.get_doc({
                        "doctype": "ToDo",
                        "description": task.subject,
                        "reference_type": "Task",
                        "reference_name": task.name,
                        "status": "Open",
                        "assigned_by": frappe.session.user,
                        "allocated_to": user
                    })
                    todo.insert(ignore_permissions=True)
                     
        create_task_and_todos()
        
        frappe.msgprint(_("Tasks and ToDos created and assigned by role."))
       