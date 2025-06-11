// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt


frappe.ui.form.on("Service Request", {
    create_project: function(frm) {
        // Check if the document is saved
        if (frm.is_new()) {
            frm.save().then(() => {
                create_project_call(frm);
            });
        } else {
            create_project_call(frm);
        }
    }
});

function create_project_call(frm) {
    frappe.call({
        method: "virtual_pro.virtual_pro.doctype.service_request.service_request.create_project_from_service_request",
        args: {
            services: frm.doc.services,
            customer_company_name: frm.doc.customer_company_name,
            service_request_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                // Just update the form field and refresh - no alert
                frm.set_value('project_name', r.message);
                frm.save();
                frm.refresh();
            }
        }
    });
}
// List view settings for Service request 
frappe.listview_settings['Service Request'] = {
    add_fields: ["status"],
    get_indicator: function(doc) {
        // Use status field value or default to "Open" for drafts
        const status = doc.status || "Open";
        
        switch(status) {
            case "Open":
                return ["Open", "blue", "status,=,Open"];
            
            case "Completed":
                return ["Completed", "darkgreen", "status,=,Completed"];
            default:
                return [status, "gray", "status,=," + status];
        }
    }
};