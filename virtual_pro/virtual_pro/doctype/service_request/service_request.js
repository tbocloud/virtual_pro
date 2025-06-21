// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt


frappe.ui.form.on("Service Request", {
    refresh: function(frm) {
        frm.toggle_display("create_project", !frm.doc.project_id);

        if (frm.doc.docstatus === 1 && frm.doc.status === "To Sales Invoice") { 
            frm.add_custom_button("Sales Invoice", function() {
                if (frm.doc.quotation) {
                    create_sales_invoice_from_quotation(frm);
                }else {
                create_quotation_from_service_request(frm);
                }
            },__('Create'));
        }
        cur_frm.page.set_inner_btn_group_as_primary(__("Create"));
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
        method: "virtual_pro.virtual_pro.doctype.service_request.service_request.mak_sales_invoice",
        args: {
            source_name: frm.doc.name
        },
        frm: frm
    });
}

function create_sales_invoice_from_quotation(frm) {
    // Check if quotation exists
    if (!frm.doc.quotation) {
        frappe.msgprint({
            title: __('Missing Quotation'),
            message: __('No quotation linked to this Service Request'),
            indicator: 'red'
        });
        return;
    }

    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Quotation",
            name: frm.doc.quotation
        },
        callback: function(r) {
            if (r.message) {
                let quotation = r.message;
                
                // Check if quotation is submitted
                if (quotation.docstatus !== 1) {
                    frappe.msgprint({
                        title: __('Invalid Quotation'),
                        message: __('Quotation {0} is not submitted', [frm.doc.quotation]),
                        indicator: 'orange'
                    });
                    return;
                }

                // Check quotation status
                if (quotation.status === 'Ordered' || quotation.status === 'Closed' || quotation.status === 'Lost') {
                    frappe.msgprint({
                        title: __('Quotation Status'),
                        message: __('Quotation {0} status is {1}. Cannot create Sales Invoice', [frm.doc.quotation, quotation.status]),
                        indicator: 'orange'
                    });
                    return;
                }

                // Create Sales Invoice from Quotation
                frappe.model.open_mapped_doc({
                    method: "virtual_pro.events.quotation.make_sales_invoice", 
                    source_name: frm.doc.quotation,
                    get_query_filters: {
                        company: frm.doc.company || frappe.defaults.get_default("Company")
                    }
                });

            } else {
                frappe.msgprint({
                    title: __('Quotation Not Found'),
                    message: __('Quotation {0} does not exist', [frm.doc.quotation]),
                    indicator: 'red'
                });
            }
        }
    });
}
