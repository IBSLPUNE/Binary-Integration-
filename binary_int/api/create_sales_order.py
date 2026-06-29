import frappe
import requests
 
 
ORDER_URL = "https://api-dev.binaryintent.com/api/campaign-manager/order"
 
 
def pulse_login(config=None):
    if not config:
        config = frappe.get_single("Pulse Sales Configuration")
 
    payload = {
        "emailId": config.username,
        "password": config.get_password("password"),
        "lsRememberMe": True
    }
 
    response = requests.post(config.url, json=payload, timeout=30)
    response.raise_for_status()
 
    data = response.json()
 
    token = data.get("idToken")
    if token:
        config.token = token
        config.save(ignore_permissions=True)
        frappe.db.commit()
 
    return token
 
 
def get_token(config):
    if config.token:
        return config.token
 
    return pulse_login(config)
 
 
def build_sales_order_payload(doc):
    frappe.msgprint("Hook Triggered")
 
    sales_order = frappe.get_doc("Sales Order", doc.custom_sales_order_no)
    so_item = frappe.get_doc("Sales Order Item", doc.custom_so_item_row)
 
    product_cat_name = so_item.custom_product_category or so_item.item_group or ""
 
    products_cat_items = []
    if product_cat_name:
        products_cat_items.append({
            "productCatName": product_cat_name
        })
 
    products_items = [{
        "productName": so_item.item_name or "",
        "productStartDate": str(sales_order.transaction_date) if sales_order.transaction_date else "",
        "productEndDate": str(sales_order.delivery_date) if sales_order.delivery_date else "",
        "getProductNameListByCat": [
            so_item.item_code or ""
        ],
        "getProductCatType": "1",
        "billingTypes": "Yes",
        "quantity": int(doc.custom_qty or 0),
        "cpl": str(getattr(doc, "custom_cpl", "") or so_item.rate or ""),
        "totalAmount": int((doc.custom_qty or 0) * (getattr(doc, "custom_cpl", 0) or so_item.rate or 0)),
        "productCatName": "Lead Generation",
        "productCatId": so_item.custom_product_category or ""
    }]
 
    return {
        "userId": "20193",
        "sfdcOrderId": sales_order.name,
        "orderDate": str(sales_order.transaction_date) if sales_order.transaction_date else "",
        "endClientCode": sales_order.customer or "",
        "clientCode": sales_order.customer or "",
        "isDirect": 0,
        "clientStartDate": str(sales_order.transaction_date) if sales_order.transaction_date else "",
        "clientEndDate": str(sales_order.delivery_date) if sales_order.delivery_date else "",
        "specification": "",
        "poNumber": sales_order.po_no or "",
        "deliverySchedule": "",
        "pacing": "",
        "billingType": "monthly",
        "invoiceNumber": "",
        "documents": "",
        "timezone": "",
        "client_cid": sales_order.custom_client_cid or "",
        "client_io": sales_order.custom_client_io_number or "",
        "client_campaign_name": doc.project_name or doc.name,
        "productsCatItems": products_cat_items,
        "productsItems": products_items,
        "paymentTerms": [
            {
                "termName": term.payment_term or "",
                "description": term.description or "",
                "dueDate": str(term.due_date) if term.due_date else "",
                "invoicePortion": str(term.invoice_portion or ""),
                "amount": str(term.payment_amount or "")
            }
            for term in sales_order.payment_schedule
        ],
        "contacts": [
            {
                "contactId": sales_order.contact_person or "",
                "contactPerson": sales_order.contact_display or "",
                "contactTitle": "",
                "phoneNumber": sales_order.contact_mobile or "",
                "emailId": sales_order.contact_email or "",
                "timeZone": "",
                "contactType": ""
            }
        ],
        "allocationQuantity": int(doc.custom_qty or 0),
        "cpl": float(getattr(doc, "custom_cpl", 0) or so_item.rate or 0)
    }
 
 
def post_sales_order(payload, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
 
    return requests.post(
        ORDER_URL,
        json=payload,
        headers=headers,
        timeout=30
    )
 
 
def create_sales_order(doc, method=None):
    frappe.log_error(
        title="PROJECT HOOK SALES ORDER TEST",
        message=f"Triggered for Project {doc.name}"
    )
 
    try:
        frappe.msgprint("Pulse Sales Order sync has been triggered.")
 
        if not doc.custom_sales_order_no or not doc.custom_so_item_row:
            frappe.log_error(
                title="Pulse Sales Order Sync Skipped",
                message=f"Project {doc.name} missing Sales Order or Sales Order Item Row"
            )
            return
 
        config = frappe.get_single("Pulse Sales Configuration")
 
        payload = build_sales_order_payload(doc)
 
        frappe.log_error(
            title="Pulse Sales Order Payload",
            message=frappe.as_json(payload, indent=2)
        )
 
        frappe.log_error(
            title="Pulse Products Items Count",
            message=f"Project {doc.name} productsItems count: {len(payload.get('productsItems', []))}"
        )
 
        token = get_token(config)
 
        response = post_sales_order(payload, token)
 
        if response.status_code == 401:
            frappe.msgprint("Pulse token expired. Generating a new token.")
 
            token = pulse_login(config)
            response = post_sales_order(payload, token)
 
        response.raise_for_status()
 
        frappe.msgprint(
            title="Pulse Response",
            msg=f"<pre>{frappe.as_json(response.json(), indent=2)}</pre>"
        )
 
        frappe.msgprint("Sales Order synced successfully with Pulse.")
 
        frappe.log_error(
            title="Pulse Sales Order Sync Success",
            message=f"Project {doc.name} synced successfully with Pulse.\n\nResponse:\n{response.text}"
        )
 
    except Exception:
        frappe.msgprint("Pulse Sales Order sync failed. Please check Error Log.")
 
        frappe.log_error(
            title="Pulse Sales Order Sync Error",
            message=frappe.get_traceback()
        )