frappe.listview_settings["Service Request"] = {
  add_fields: ["status"],
  get_indicator: function (doc) {
    const status = doc.status || "To Sales Invoice";

    switch (status) {
      case "To Sales Invoice":
        return ["To Sales Invoice", "blue", "status,=,To Sales Invoice"];
      case "Completed":
        return ["Completed", "darkgreen", "status,=,Completed"];
      default:
        return [status, "gray", "status,=," + status];
    }
  },
};
