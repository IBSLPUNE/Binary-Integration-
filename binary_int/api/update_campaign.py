import frappe


@frappe.whitelist()
def update_campaign(doc, method):
    frappe.throw("Campaign Update hook triggered")