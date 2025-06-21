frappe.listview_settings["Task"] = {
	add_fields: [
		"project",
		"status",
		"priority",
		"exp_start_date",
		"exp_end_date",
		"subject",
		"progress",
		"depends_on_tasks",
	],
	filters: [["status", "=", "Open"]],
	
	onload: function (listview) {
		var method = "erpnext.projects.doctype.task.task.set_multiple_status";

		listview.page.add_menu_item(__("Set as Open"), function () {
			listview.call_for_selected_items(method, { status: "Open" });
		});

		listview.page.add_menu_item(__("Set as Completed"), function () {
			listview.call_for_selected_items(method, { status: "Completed" });
		});
	},
	
	get_indicator: function (doc) {
		var colors = {
			Open: "orange",
			Overdue: "red",
			"Pending Review": "orange",
			Working: "orange",
			Completed: "green",
			Cancelled: "dark grey",
			Template: "blue",
		};
		return [__(doc.status), colors[doc.status], "status,=," + doc.status];
	},
	
	gantt_custom_popup_html: function (ganttobj, task) {
		let html = `
			<a class="text-white mb-2 inline-block cursor-pointer"
				href="/app/task/${ganttobj.id}"">
				${ganttobj.name}
			</a>
		`;

		if (task.project) {
			html += `<p class="mb-1">${__("Project")}:
				<a class="text-white inline-block"
					href="/app/project/${task.project}"">
					${task.project}
				</a>
			</p>`;
		}
		html += `<p class="mb-1">
			${__("Progress")}:
			<span class="text-white">${ganttobj.progress}%</span>
		</p>`;

		if (task._assign) {
			const assign_list = JSON.parse(task._assign);
			const assignment_wrapper = `
				<span>Assigned to:</span>
				<span class="text-white">
					${assign_list.map((user) => frappe.user_info(user).fullname).join(", ")}
				</span>
			`;
			html += assignment_wrapper;
		}

		return `<div class="p-3" style="min-width: 220px">${html}</div>`;
	},

	// Add Status update button
	button: {
		show: function (doc) {
			return true; // Always show the button
		},
		get_label: function () {
			return __('<i class="fa fa-edit"></i> Status');
		},
		get_description: function (doc) {
			return __("Update Status of Task: " + doc.name);
		},
		action: function (doc) {
			console.log("Update Status Clicked for Task:", doc.name);

			// Simple dialog with just status and comment
			let d = new frappe.ui.Dialog({
				title: __('Update Task Status: {0}', [doc.name]),
				fields: [
					{
						label: 'New Status',
						fieldname: 'new_status',
						fieldtype: 'Select',
						options: [
							"Open",
							"Working",
							"Pending Review",
							"Overdue", 
							"Completed",
							"Cancelled"
						],
						reqd: 1,
						default: get_suggested_next_status(doc.status)
					},
					{
						label: 'Comments',
						fieldname: 'comments',
						fieldtype: 'Small Text',
						description: 'Add comments about the status change'
					}
				],
				size: 'small',
				primary_action_label: __('Update'),
				primary_action: function() {
					var data = d.get_values();
					
					if (data.new_status === doc.status) {
						frappe.msgprint(__("Please select a different status"));
						return;
					}
					
					// Update task status
					frappe.call({
						method: "erpnext.projects.doctype.task.task.set_multiple_status",
						args: {
							names: [doc.name],
							status: data.new_status
						},
						freeze: true,
						freeze_message: __("Updating..."),
						callback: function(r) {
							if (!r.exc) {
								// Add comment if provided
								if (data.comments) {
									frappe.call({
										method: "frappe.desk.form.utils.add_comment",
										args: {
											reference_doctype: "Task",
											reference_name: doc.name,
											content: data.comments,
											comment_email: frappe.session.user,
											comment_by: frappe.session.user_fullname
										}
									});
								}
								
								frappe.show_alert({
									message: __("Status updated to {0}", [data.new_status]),
									indicator: 'green'
								});
								
								// Refresh the list
								cur_list.refresh();
								d.hide();
							}
						}
					});
				}
			});

			d.show();
		},
	},
};

// Helper function to suggest next logical status
function get_suggested_next_status(current_status) {
	const status_flow = {
		"Open": "Working",
		"Working": "Pending Review",
		"Pending Review": "Completed",
		"Overdue": "Working",
		"Completed": "Open", 
		"Cancelled": "Open"
	};
	return status_flow[current_status] || "Working";
}