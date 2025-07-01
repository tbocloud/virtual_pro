frappe.ui.form.on('Sales Invoice Item', {
    amount: function (frm, cdt, cdn) {
        calculate_cost_difference(frm, cdt, cdn);
    },
    custom_cost: function (frm, cdt, cdn) {
        calculate_cost_difference(frm, cdt, cdn);
    }
});

function calculate_cost_difference(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let amount = flt(row.amount);
    let cost = flt(row.custom_cost);

    row.custom_cost_difference = amount - cost;
    frm.refresh_field("items");
}
