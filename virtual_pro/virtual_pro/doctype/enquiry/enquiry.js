frappe.ui.form.on('Enquiry', {
    refresh: function(frm) {
        frm.clear_custom_buttons();

        if (frm.doc.docstatus === 1) {
            frm.add_custom_button('Change Status', () => {
                show_status_dialog(frm);
            });
            if (!frm.doc.quotation) {
                frm.add_custom_button("Create Quotation", function() {
                    frappe.model.open_mapped_doc({
                        method: "virtual_pro.virtual_pro.doctype.enquiry.enquiry.make_quotation",
                        frm: frm
                    });
                }, __('Create'));
            }
        }
        cur_frm.page.set_inner_btn_group_as_primary(__("Create"));
    },
    services: function(frm) {
        if (frm.doc.services) {
            frappe.db.get_doc('Services', frm.doc.services)
                .then(service_doc => {
                    const has_item_name = service_doc.service_items?.some(row => row.item_name && row.item_name.trim() !== "");
                    if (!has_item_name) {
                        frappe.msgprint({
                            title: __('Missing Service Items'),
                            message: __('The selected Service has no items. Please add at least one Item.'),
                            indicator: 'red'
                        });
                    }
                });
        }
    }
});

function show_status_dialog(frm) {
    const status_options = ['Open', 'Replied', 'Lost Enquiry', 'Interested', 'Do Not Contact', 'Converted', 'Completed'];

    const d = new frappe.ui.Dialog({
        title: 'Change Status',
        fields: [
            {
                label: 'New Status',
                fieldname: 'new_status',
                fieldtype: 'Select',
                reqd: 1,
                options: status_options.join('\n'),
                default: frm.doc.status
            }
        ],
        primary_action_label: 'Save',
        primary_action(values) {
            if (values.new_status === 'Lost Enquiry') {
                d.hide();
                show_lost_enquiry_reason_dialog(frm, values.new_status);
            } else if (values.new_status === 'Converted') {
                d.hide();
                update_status(frm, values.new_status, true); // Create Service Request when status is Converted
            } else {
                update_status(frm, values.new_status);
                d.hide();
            }
        }
    });

    d.show();
}

function show_lost_enquiry_reason_dialog(frm, new_status) {
    const reason_dialog = new frappe.ui.Dialog({
        title: 'Lost Enquiry - Reason',
        fields: [
            {
                label: 'Reason for Lost Enquiry',
                fieldname: 'lost_reason',
                fieldtype: 'Small Text',
                reqd: 1
            }
        ],
        primary_action_label: 'Save',
        primary_action(values) {
            update_status_with_reason(frm, new_status, values.lost_reason);
            reason_dialog.hide();
        },
        secondary_action_label: 'Cancel',
        secondary_action() {
            reason_dialog.hide();
        }
    });

    reason_dialog.show();
}

function update_status(frm, new_status, create_service_request = false) {
    frappe.call({
        method: "frappe.client.set_value",
        args: {
            doctype: frm.doc.doctype,
            name: frm.doc.name,
            fieldname: "status",
            value: new_status
        },
        callback: function() {
            frappe.show_alert(`✅ Status changed to: ${new_status}`);
            if (create_service_request) {
                auto_create_service_request(frm);
            } else {
                frm.reload_doc();
            }
        }
    });
}

function update_status_with_reason(frm, new_status, reason) {
    frappe.call({
        method: "frappe.client.set_value",
        args: {
            doctype: frm.doc.doctype,
            name: frm.doc.name,
            fieldname: {
                "status": new_status,
                "lost_reason": reason
            }
        },
        callback: function() {
            frappe.show_alert(`✅ Status changed to: ${new_status}`);
            frappe.show_alert(`📝 Reason saved: ${reason}`);
            frm.reload_doc();
        }
    });
}

function auto_create_service_request(frm) {
    // Check if Service Request already exists for this Enquiry
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Service Request",
            filters: {
                enquiry: frm.doc.name
            },
            fields: ["name"],
            limit: 1
        },
        callback: function(res) {
            if (res.message && res.message.length > 0) {
                frappe.show_alert(`Service Request already exists: ${res.message[0].name}`);
                frm.reload_doc();
            } else {
                frappe.call({
                    method: "frappe.client.insert",
                    args: {
                        doc: {
                            doctype: "Service Request",
                            enquiry: frm.doc.name,
                            customer_company_name: frm.doc.customer_company_name,
                            services: frm.doc.services,
                            quotation: frm.doc.quotation,

                        }
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert(`✅ Service Request ${r.message.name} created successfully`);
                            frm.reload_doc();
                        } else {
                            frappe.msgprint("❌ Could not create Service Request.");
                        }
                    }
                });
            }
        }
    });
}