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
    product_items = []

    for item in doc.get("items", []):
        product_items.append({
            "orderProductId": "",
            "productName": item.item_name or "",
            "pricingType": doc.currency or "",
            "quantityType": item.uom or "",
            "productCatName": item.custom_product_category or "",
            "productType": "1",
            "productStartDate": str(doc.custom_client_start_date) if doc.custom_client_start_date else "",
            "productEndDate": str(doc.delivery_date) if doc.delivery_date else "",
            "bilableType": "Yes",
            "quantity": float(item.qty or 0),
            "pricing": float(item.rate or 0),
            "totalAmount": float(item.amount or 0),
            "productId": item.item_code or "",
            "productCatId": item.custom_product_category or "",
            "isDelete": False
        })

    return {
        "userId": doc.owner,
        "sfdcOrderId": "",
        "orderDate": str(doc.transaction_date) if doc.transaction_date else "",
        "endClientCode": doc.custom_end_client_sponsor or "",
        "clientCode": doc.customer or "",
        "isDirect": 0,
        "clientStartDate": str(doc.custom_client_start_date) if doc.custom_client_start_date else "",
        "clientEndDate": str(doc.delivery_date) if doc.delivery_date else "",
        "specification": "",
        "poNumber": doc.po_no or "",
        "deliverySchedule": doc.custom_delivery_schedule or "",
        "pacing": doc.custom_pacing or "",
        "billingType": "",
        "invoiceNumber": "",
        "documents": "",
        "timezone": doc.custom_time_zone or "",
        "client_cid": doc.custom_client_cid or "",
        "client_io": doc.custom_client_io_number or "",
        "client_campaign_name": doc.name,

        "productItems": product_items,

        "paymentTerms": [
            {
                "paymentTermsId": "",
                "termName": term.payment_term or "",
                "description": term.description or "",
                "dueDate": str(term.due_date) if term.due_date else "",
                "invoicePortion": term.invoice_portion or 0,
                "amount": term.payment_amount or 0
            }
            for term in doc.get("payment_schedule", [])
        ],

        "contacts": [
            {
                "contactId": doc.contact_person or "",
                "contactPerson": doc.contact_display or "",
                "contactTitle": "",
                "phoneNumber": doc.contact_mobile or "",
                "emailId": doc.contact_email or "",
                "timeZone": "",
                "contactType": 3
            }
        ],

        "isUpdate": {
            "orderDetails": True,
            "productItems": False,
            "items": False,
            "paymentTerms": False
        },

        "allocation": 100
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