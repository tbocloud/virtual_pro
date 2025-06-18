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