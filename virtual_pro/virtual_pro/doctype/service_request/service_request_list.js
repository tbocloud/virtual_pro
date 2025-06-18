frappe.listview_settings["Service Request"] = {
  add_fields: ["status"],
  get_indicator: function (doc) {
    const status = doc.status || "Open";

    switch (status) {
      case "To Quotation":
        return ["To Quotation", "blue", "status,=,To Quotation"];
      case "To Sales Order":
        return ["To Sales Order", "blue", "status,=,To Sales Order"];
      case "To Sales Invoice":
        return ["To Sales Invoice", "blue", "status,=,To Sales Invoice"];
      case "Completed":
        return ["Completed", "darkgreen", "status,=,Completed"];
      default:
        return [status, "gray", "status,=," + status];
    }
  },
};
