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
    },
    before_parent_steps_remove: function (frm, cdt, cdn) {
        let row = locals[cdt] && locals[cdt][cdn] ? locals[cdt][cdn] : null;
        
        if (!row || !row.step_name) {
            console.error("Step row not found or step_name is missing before removal.");
            return;
        }
        
        let template_to_remove = row.step_name;
        frm.doc.child_steps = frm.doc.child_steps.filter(item => item.parent_step !== template_to_remove);
        
        frm.refresh_field("child_steps");
        
        frm.dirty();
    }
});
