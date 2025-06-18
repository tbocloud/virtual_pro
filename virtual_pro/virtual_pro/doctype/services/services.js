// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Services", {
	refresh(frm) {

	},
});
frappe.ui.form.on('Parent Steps', {
    step_name: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];


        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Phases',
                name: row.step_name
            },
            callback: function(r) {
                if (!r.message || !r.message.child_step) {
                    frappe.msgprint(__('No child steps found in the selected Phase.'));
                    return;
                }

                const phase_children = r.message.child_step;

                phase_children.forEach(step => {
                    let child = frm.add_child('child_steps');
                    if (child) {
                        child.step_name = step.step_name;
                        child.assign_by_role = step.assign_by_role;
                        child.cc = step.cc;
                        child.parent_step = step.parent;
                    }
                });

                frm.refresh_field('child_steps');
            }
        });
    }
});
