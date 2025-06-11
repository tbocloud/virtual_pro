frappe.ui.form.on('Enquiry', {
    refresh: function(frm) {
        frm.clear_custom_buttons();

        // Show Change Status button ONLY when document is submitted (docstatus = 1)
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button('Change Status', () => {
                show_status_dialog(frm);
            });
        }

        if (frm.doc.status === 'Interested') {
            frm.add_custom_button('Create Service Request', () => {
                // Auto-fill Service Request with only specific Enquiry data
                frappe.new_doc('Service Request', {
                    // Basic reference
                    enquiry_reference: frm.doc.name,
                    
                    // Customer details
                   customer_company_name: frm.doc.customer_company_name,
                    services: frm.doc.services
                });
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
            // Check if the new status is "Lost Enquiry"
            if (values.new_status === 'Lost Enquiry') {
                d.hide(); // Hide the current dialog
                show_lost_enquiry_reason_dialog(frm, values.new_status);
            } else {
                // For other statuses, proceed normally
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
                reqd: 1,
                description: 'Please provide the reason why this enquiry was lost'
            }
        ],
        primary_action_label: 'Save',
        primary_action(values) {
            // Update the status and save the reason
            update_status_with_reason(frm, new_status, values.lost_reason);
            reason_dialog.hide();
        },
        secondary_action_label: 'Cancel',
        secondary_action() {
            reason_dialog.hide();
            // Optionally, you can reshow the status dialog here
            // show_status_dialog(frm);
        }
    });

    reason_dialog.show();
}

function update_status(frm, new_status) {
    // For submitted documents, use server call to update
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
            // Reload doc to refresh buttons
            frm.reload_doc();
        }
    });
}

function update_status_with_reason(frm, new_status, reason) {
    // Update both status and reason in the lost_reason field
    frappe.call({
        method: "frappe.client.set_value",
        args: {
            doctype: frm.doc.doctype,
            name: frm.doc.name,
            fieldname: {
                "status": new_status,
                "lost_reason": reason  // Saves to the lost_reason field in Enquiry doctype
            }
        },
        callback: function() {
            frappe.show_alert(`✅ Status changed to: ${new_status}`);
            frappe.show_alert(`📝 Reason saved: ${reason}`);
            // Reload doc to refresh buttons
            frm.reload_doc();
        }
    });
}

// List view settings for Enquiry 
frappe.listview_settings['Enquiry'] = {
    add_fields: ["status"],
    get_indicator: function(doc) {
        // Use status field value or default to "Open" for drafts
        const status = doc.status || "Open";
        
        switch(status) {
            case "Open":
                return ["Open", "blue", "status,=,Open"];
            case "Replied":
                return ["Replied", "orange", "status,=,Replied"];
            case "Lost Enquiry":
                return ["Lost Enquiry", "red", "status,=,Lost Enquiry"];
            case "Interested":
                return ["Interested", "green", "status,=,Interested"];
            case "Do Not Contact":
                return ["Do Not Contact", "red", "status,=,Do Not Contact"];
            case "Converted":
                return ["Converted", "green", "status,=,Converted"];
            case "Completed":
                return ["Completed", "darkgreen", "status,=,Completed"];
            default:
                return [status, "gray", "status,=," + status];
        }
    }
};