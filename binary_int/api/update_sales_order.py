import frappe
import requests


ORDER_URL = "https://api-dev.binaryintent.com/api/campaign-manager/order"


@frappe.whitelist()
def update_sales_order_from_js(sales_order):
    doc = frappe.get_doc("Sales Order", sales_order)

    if doc.docstatus != 1:
        frappe.throw("Sales Order must be submitted.")

    update_sales_order(doc, method="manual_button")


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

    for item in doc.items:
        item_doc = frappe.get_doc("Item", item.item_code)

        product_cat_name = item_doc.item_group or ""
        product_cat_id = ""

        if product_cat_name:
            product_cat_id = frappe.db.get_value(
                "Item Group",
                product_cat_name,
                "custom_pulse_product_category_id"
            ) or ""

        product_items.append({
            "orderProductId": item.get("custom_pulse_order_product_id") or "",
            "productName": item.item_name or item.item_code or "",
            "pricingType": doc.currency or "",
            "quantityType": item.uom or "",
            "productCatName": product_cat_name,
            "productType": "1",
            "productStartDate": str(doc.transaction_date) if doc.transaction_date else "",
            "productEndDate": str(item.delivery_date or doc.delivery_date) if (item.delivery_date or doc.delivery_date) else "",
            "bilableType": "Yes",
            "quantity": int(item.qty or 0),
            "pricing": float(item.rate or 0),
            "totalAmount": float(item.amount or 0),
            "productId": item_doc.get("custom_pulse_product_id") or "",
            "productCatId": product_cat_id,
            "isDelete": False
        })

    end_client_code = ""
    if doc.get("custom_end_client_sponsor"):
        end_client_code = frappe.db.get_value(
            "End Client Sponsor",
            doc.custom_end_client_sponsor,
            "pulse_end_client_id"
        ) or ""

    client_code = ""
    if doc.customer:
        client_code = frappe.db.get_value(
            "Customer",
            doc.customer,
            "custom_pulse_client_id"
        ) or ""

    return {
        "userId": "20192",
        "sfdcOrderId": doc.name,
        "orderDate": str(doc.transaction_date) if doc.transaction_date else "",
        "endClientCode": end_client_code,
        "clientCode": client_code,
        "isDirect": 0,
        "clientStartDate": str(doc.transaction_date) if doc.transaction_date else "",
        "clientEndDate": str(doc.delivery_date) if doc.delivery_date else "",
        "specification": doc.get("terms") or "",
        "poNumber": doc.po_no or "",
        "deliverySchedule": doc.get("custom_delivery_schedule") or "0",
        "pacing": doc.get("custom_pacing") or "0",
        "billingType": doc.get("custom_billing_type") or "monthly",
        "invoiceNumber": doc.get("custom_invoice_number") or "",
        "documents": "",
        "timezone": doc.get("custom_timezone") or "",
        "client_cid": doc.custom_client_cid or "",
        "client_io": doc.custom_client_io_number or "",
        "client_campaign_name": doc.get("custom_client_campaign_name") or doc.name,
        "productItems": product_items,
        "paymentTerms": [
            {
                "paymentTermsId": term.get("custom_pulse_payment_term_id") or "",
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
                "timeZone": doc.get("custom_contact_timezone") or "",
                "contactType": 1
            }
        ],
        "isUpdate": {
            "orderDetails": True,
            "productItems": False,
            "items": False,
            "paymentTerms": True
        },
        "allocation": int(doc.get("custom_allocation") or 1000)
    }


def post_sales_order(payload, token, pulse_so_id):
    url = f"{ORDER_URL}/order_v2/{pulse_so_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    frappe.log_error(title="PULSE UPDATE URL", message=url)

    return requests.put(url, json=payload, headers=headers, timeout=30)


def update_sales_order(doc, method=None):
    if doc.docstatus != 1:
        return

    if method != "manual_button" and not doc.get("amended_from"):
        return

    frappe.msgprint("Sales Order Update test")

    frappe.log_error(
        title="SALES ORDER UPDATE TRIGGERED",
        message=f"Sales Order: {doc.name}, Method: {method}, Amended From: {doc.get('amended_from')}"
    )

    try:
        pulse_so_id = doc.get("custom_pulse_so_id") or ""

        frappe.log_error(
            title="PULSE SO ID",
            message=pulse_so_id
        )

        if not pulse_so_id:
            frappe.log_error(
                title="PULSE UPDATE STOPPED",
                message=f"custom_pulse_so_id is empty for Sales Order: {doc.name}"
            )
            return

        config = frappe.get_single("Pulse Sales Configuration")
        payload = build_sales_order_payload(doc)

        frappe.log_error(
            title="PULSE UPDATE PAYLOAD",
            message=frappe.as_json(payload, indent=2)
        )

        token = get_token(config)
        response = post_sales_order(payload, token, pulse_so_id)

        if response.status_code == 401:
            token = pulse_login(config)
            response = post_sales_order(payload, token, pulse_so_id)

        frappe.log_error(
            title="PULSE UPDATE RESPONSE",
            message=f"""
Status Code: {response.status_code}

Response:
{response.text}
"""
        )

        response.raise_for_status()

        frappe.msgprint("Pulse Sales Order update API hit successfully.")

    except Exception:
        frappe.log_error(
            title="PULSE SALES ORDER UPDATE ERROR",
            message=frappe.get_traceback()
        )

        frappe.msgprint("Pulse Sales Order update failed. Check Error Log.")