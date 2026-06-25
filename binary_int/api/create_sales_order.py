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
    products_cat_items = []
    products_items = []
 
    for item in doc.get("items"):
        product_cat_name = item.custom_product_category or item.item_group or ""
 
        if product_cat_name and not any(
            row.get("productCatName") == product_cat_name
            for row in products_cat_items
        ):
            products_cat_items.append({
                "productCatName": product_cat_name
            })
 
        products_items.append({
            "productName": item.item_name or "",
            "productStartDate": str(doc.transaction_date) if doc.transaction_date else "",
            "productEndDate": str(doc.delivery_date) if doc.delivery_date else "",
            "getProductNameListByCat": [
                item.item_code or ""
            ],
            "getProductCatType": "1",
            "billingTypes": "Yes",
            "quantity": int(item.qty or 0),
            "cpl": str(item.rate or ""),
            "totalAmount": int(item.amount or 0),
            "productCatName": product_cat_name,
            "productCatId": item.item_group or ""
        })
 
    return {
        "userId": "20193",
        "sfdcOrderId": doc.name,
        "orderDate": str(doc.transaction_date) if doc.transaction_date else "",
        "endClientCode": doc.customer or "",
        "clientCode": doc.customer or "",
        "isDirect": 0,
        "clientStartDate": str(doc.transaction_date) if doc.transaction_date else "",
        "clientEndDate": str(doc.delivery_date) if doc.delivery_date else "",
        "specification": "",
        "poNumber": doc.po_no or "",
        "deliverySchedule": "",
        "pacing": "",
        "billingType": "monthly",
        "invoiceNumber": "",
        "documents": "",
        "timezone": "",
        "client_cid": doc.custom_client_cid or "",
        "client_io": doc.custom_client_io_number or "",
        "client_campaign_name": doc.name,
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
            for term in doc.payment_schedule
        ],
        "contacts": [
            {
                "contactId": doc.contact_person or "",
                "contactPerson": doc.contact_display or "",
                "contactTitle": "",
                "phoneNumber": doc.contact_mobile or "",
                "emailId": doc.contact_email or "",
                "timeZone": "",
                "contactType": ""
            }
        ],
        "allocationQuantity": int(sum(
            float(item.qty or 0)
            for item in doc.get("items")
        )),
        "cpl": float(doc.items[0].rate or 0) if doc.items else 0
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
        title="SALES ORDER HOOK TEST",
        message=f"Triggered for {doc.name}"
    )

    try:
        frappe.msgprint("Pulse Sales Order sync has been triggered.")

        frappe.log_error(
            title="Pulse Sales Order Hook Triggered",
            message=f"Sales Order submit hook triggered for {doc.name}"
        )

        config = frappe.get_single("Pulse Sales Configuration")

        payload = build_sales_order_payload(doc)

        frappe.log_error(
            title="Pulse Sales Order Payload",
            message=frappe.as_json(payload, indent=2)
        )

        frappe.log_error(
            title="Pulse Product Items Count",
            message=f"Sales Order {doc.name} productItems count: {len(payload.get('productItems', []))}"
        )

        token = get_token(config)

        response = post_sales_order(payload, token)

        if response.status_code == 401:
            frappe.msgprint("Pulse token expired. Generating a new token.")

            frappe.log_error(
                title="Pulse Token Expired",
                message=f"Token expired for Sales Order {doc.name}. Generating new token."
            )

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
            message=f"Sales Order {doc.name} synced successfully with Pulse.\n\nResponse:\n{response.text}"
        )

    except Exception:
        frappe.msgprint("Pulse Sales Order sync failed. Please check Error Log.")

        frappe.log_error(
            title="Pulse Sales Order Sync Error",
            message=frappe.get_traceback()
        )



