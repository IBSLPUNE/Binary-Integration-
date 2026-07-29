app_name = "binary_int"
app_title = "Binary API Integration"
app_publisher = "IBSL"
app_description = "Binary(Pulse) Integration"
app_email = "design@indibasolutions.com"
app_license = "mit"
 
# Apps
# ------------------
 
# required_apps = []
 
# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "binary_int",
# 		"logo": "/assets/binary_int/logo.png",
# 		"title": "Binary API Integration",
# 		"route": "/binary_int",
# 		"has_permission": "binary_int.api.permission.has_app_permission"
# 	}
# ]
 
# Includes in <head>
# ------------------
 
# include js, css files in header of desk.html
# app_include_css = "/assets/binary_int/css/binary_int.css"
# app_include_js = "/assets/binary_int/js/binary_int.js"
 
# include js, css files in header of web template
# web_include_css = "/assets/binary_int/css/binary_int.css"
# web_include_js = "/assets/binary_int/js/binary_int.js"
 
# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "binary_int/public/scss/website"
 
# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}
 
# include js in page
# page_js = {"page" : "public/js/file.js"}
 
# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
    "Customer": "public/js/customer.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}
 
# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "binary_int/public/icons.svg"
 
# Home Pages
# ----------
 
# application home page (will override Website Settings)
# home_page = "login"
 
# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }
 
# Generators
# ----------
 
# automatically create page for each record of this doctype
# website_generators = ["Web Page"]
 
# Jinja
# ----------
 
# add methods and filters to jinja environment
# jinja = {
# 	"methods": "binary_int.utils.jinja_methods",
# 	"filters": "binary_int.utils.jinja_filters"
# }
 
# Installation
# ------------
 
# before_install = "binary_int.install.before_install"
# after_install = "binary_int.install.after_install"
 
# Uninstallation
# ------------
 
# before_uninstall = "binary_int.uninstall.before_uninstall"
# after_uninstall = "binary_int.uninstall.after_uninstall"
 
# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument
 
# before_app_install = "binary_int.utils.before_app_install"
# after_app_install = "binary_int.utils.after_app_install"
 
# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument
 
# before_app_uninstall = "binary_int.utils.before_app_uninstall"
# after_app_uninstall = "binary_int.utils.after_app_uninstall"
 
# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config
 
# notification_config = "binary_int.notifications.get_notification_config"
 
# Permissions
# -----------
# Permissions evaluated in scripted ways
 
# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }
 
# DocType Class
# ---------------
# Override standard doctype classes
 
override_doctype_class = {
	"Project": "binary_int.overrides.project.CustomProject",
	"Sales Invoice": "binary_int.overrides.sales_invoice.CustomSalesInvoice"
}
 
# Document Events
# ---------------
# Hook on document methods and events
 
doc_events = {
	
	"Project":{
		"after_insert": [
			"binary_int.api.create_sales_order.create_sales_order",
			"binary_int.api.create_campaign.create_campaign"
		],
		"on_update":[
			"binary_int.api.create_campaign.update_campaign"
		]
		# "after_save":"binary_int.api.update_campaign.update_campaign"
	 },
	"Sales Order":{
		"on_update": "binary_int.api.update_sales_order.update_sales_order"
	}

}

# doc_events = {
#     "Project": {
#         "after_insert": [
#             "binary_int.api.create_sales_order.create_sales_order",
#             "binary_int.api.create_campaign.sync_campaign"
#         ],
#         "on_update": [
#             "binary_int.api.create_campaign.sync_campaign"
#         ]
#     }
# }
 
# Scheduled Tasks
# ---------------
 
# scheduler_events = {
# 	"all": [
# 		"binary_int.tasks.all"
# 	],
# 	"daily": [
# 		"binary_int.tasks.daily"
# 	],
# 	"hourly": [
# 		"binary_int.tasks.hourly"
# 	],
# 	"weekly": [
# 		"binary_int.tasks.weekly"
# 	],
# 	"monthly": [
# 		"binary_int.tasks.monthly"
# 	],
# }
 
# Testing
# -------
 
# before_tests = "binary_int.install.before_tests"
 
# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "binary_int.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "binary_int.task.get_dashboard_data"
# }
 
# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]
 
# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------
 
# ignore_links_on_delete = ["Communication", "ToDo"]
 
# Request Events
# ----------------
# before_request = ["binary_int.utils.before_request"]
# after_request = ["binary_int.utils.after_request"]
 
# Job Events
# ----------
# before_job = ["binary_int.utils.before_job"]
# after_job = ["binary_int.utils.after_job"]
 
# User Data Protection
# --------------------
 
# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]
 
# Authentication and authorization
# --------------------------------
 
# auth_hooks = [
# 	"binary_int.auth.validate"
# ]
 
# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True
 
# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
 
# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []