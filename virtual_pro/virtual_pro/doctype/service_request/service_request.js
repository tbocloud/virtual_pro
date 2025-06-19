// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt


frappe.ui.form.on("Service Request", {
    refresh: function(frm) {
        frm.toggle_display("create_project", !frm.doc.project_id);

        if (frm.doc.docstatus === 1 && frm.doc.status === "To Quotation") { 
            frm.add_custom_button("Create Quotation", function() {
                create_quotation_from_service_request(frm);
            });
        }
    },

    create_project: function(frm) {
        if (frm.doc.project_id) {
            frappe.msgprint(`Project already created: ${frm.doc.project_id}`);
            return;
        }

        if (frm.doc.services) {
            create_project_call(frm);
        } else {
            frappe.msgprint("Please select services before creating a project.");
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
                frm.set_value('project_id', r.message);
                frm.save();
                frappe.show_alert(`Project ${r.message} created`);
            } else {
                frappe.msgprint("Could not create project.");
            }
        }
    });
}

function create_quotation_from_service_request(frm) {
    frappe.model.open_mapped_doc({
        method: "virtual_pro.virtual_pro.doctype.service_request.service_request.mak_quotation",
        args: {
            source_name: frm.doc.name
        },
        frm: frm
    });
}
