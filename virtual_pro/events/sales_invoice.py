import frappe
from frappe import _


def update_service_request(doc, method):
    sp = frappe.get_doc("Service Request", doc.custom_service_request)
    if doc.docstatus == 1:
        sp.db_set('status', "Completed")
        sp.db_set('sales_invoice', doc.name)
    elif doc.docstatus == 2:
        sp.db_set('status', "To Sales Invoice")
        sp.db_set('sales_invoice', " ")
    sp.save()


def create_tasks(doc, method):
        
        if not doc.custom_enquiry:
            frappe.log_error("No custom_service_request found")
            return
        
        # Fix: Use get_value with proper field name
        step = frappe.db.get_value("Enquiry", doc.custom_enquiry, "services")
        if not step:
            frappe.log_error(f"No services found for Service Request: {doc.custom_enquiry}")
            return
        
        
        try:
            service = frappe.get_doc("Services", step)
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
            
            user_list = []
            for user_doc in users:
                user = user_doc.parent
                if frappe.db.exists("User", user):
                    user_data = frappe.db.get_value("User", user, ["enabled", "user_type"], as_dict=True)
                    if user_data and user_data.enabled == 1 and user_data.user_type == "System User":
                        user_list.append(user)
            
            frappe.log_error(f"Active users for role {role}: {user_list}")
            return user_list

        def get_user_by_email(email):
            """Check if email exists as an active user and return the user"""
            if not email:
                return None
            
            try:
                # Check if user exists with this email
                if frappe.db.exists("User", email):
                    user_data = frappe.db.get_value("User", email, ["enabled", "user_type"], as_dict=True)
                    if user_data and user_data.enabled == 1 and user_data.user_type == "System User":
                        frappe.log_error(f"Found active user for email: {email}")
                        return email
                    else:
                        frappe.log_error(f"User {email} exists but is not active or not system user")
                        return None
                else:
                    frappe.log_error(f"No user found with email: {email}")
                    return None
            except Exception as e:
                frappe.log_error(f"Error checking user for email {email}: {e}")
                return None

        def get_assigned_users(step_row):
            """Get users to assign based on email or role"""
            users = []
            
            # First check if there's an email (CC field) in the step
            if hasattr(step_row, 'cc') and step_row.cc:
                user = get_user_by_email(step_row.cc)
                if user:
                    users.append(user)
                    frappe.log_error(f"Assigned user by email: {user}")
                else:
                    frappe.log_error(f"Email {step_row.cc} not found as user, falling back to role assignment")
            
            # If no user found by email, fall back to role assignment
            if not users and hasattr(step_row, 'assign_by_role') and step_row.assign_by_role:
                users = get_users_by_role(step_row.assign_by_role)
                frappe.log_error(f"Assigned users by role {step_row.assign_by_role}: {users}")
            
            return users

        def create_task_and_todos(parent_task_name=None):
            if hasattr(service, 'parent_steps') and service.parent_steps:
                
                for parent in service.parent_steps:
                    request = frappe.db.get_value("Service Request", {"enquiry": doc.custom_enquiry},"name")
                    
                    parent_users = get_assigned_users(parent)
                    
                    # Create parent task
                    try:
                        parent_task = frappe.get_doc({
                            "doctype": "Task",
                            "subject": parent.step_name,
                            "status": "Open",
                            "project": doc.project if hasattr(doc, 'project') and   doc.project else None,
                            "description": f"Task created from Service {parent.step_name}",
                            "custom_service_request": request,
                            "is_group": 1,
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
            
            elif hasattr(service, 'child_steps') and service.child_steps:
                frappe.log_error(f"Processing {len(service.child_steps)} child steps without parents")
                
                for child in service.child_steps:
                    if not hasattr(child, 'parent_step') or not child.parent_step:
                        create_child_task(child, parent_task_name)
        
        def create_child_task(child, parent_task_name=None):
            users = get_assigned_users(child)
            request = frappe.db.get_value("Service Request", {"enquiry": doc.custom_enquiry},"name")
            
            task_doc = {
                "doctype": "Task",
                "subject": child.step_name,
                "status": "Open",
                "description": f"Task created from Service {child.step_name}",
                "custom_service_request": request,
            }
            
            if hasattr(doc, 'project') and doc.project:
                task_doc["project"] = doc.project
            
            if parent_task_name:
                task_doc["parent_task"] = parent_task_name
            
            task = frappe.get_doc(task_doc)
            task.insert(ignore_permissions=True)
            
            for user in users:
                try:
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
                    frappe.log_error(f"ToDo created for user {user} on task {task.name}")
                except Exception as e:
                    frappe.log_error(f"Error creating ToDo for user {user} on task {task.name}: {e}")
                     
        create_task_and_todos()
        
        frappe.msgprint(_("Tasks and ToDos created and assigned by email/role."))