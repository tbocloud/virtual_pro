frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.status !== "Closed" && frm.doc.status !== "Lost" && frm.doc.status !== "Ordered") {
            frm.add_custom_button("Sales Invoice", function() {
                frappe.model.open_mapped_doc({
                    method: "virtual_pro.events.quotation.make_sales_invoice",
                    frm: frm
                });
            }, __('Create'));
        }
        setTimeout(() => {
            frm.remove_custom_button('Sales Order', 'Create');
        }, 500);
    }
});