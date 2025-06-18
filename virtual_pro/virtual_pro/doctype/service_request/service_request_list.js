frappe.listview_settings['Service Request'] = {
    add_fields: ["status"],
    get_indicator: function(doc) {
        // Use status field value or default to "Open" for drafts
        const status = doc.status || "Open";
        
        switch(status) {
            case "Open":
                return ["Open", "blue", "status,=,Open"];
            
            case "Completed":
                return ["Completed", "darkgreen", "status,=,Completed"];
            default:
                return [status, "gray", "status,=," + status];
        }
    }
};