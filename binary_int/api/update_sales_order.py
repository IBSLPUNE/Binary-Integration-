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

    return {

        "userId": "20192",

        "sfdcOrderId": "SAL-ORD-2026-00056",

        "orderDate": "2026-06-29",

        "endClientCode": "6613444416306675721",

        "clientCode": "6613444416302481412",

        "isDirect": 0,

        "clientStartDate": "2026-06-29",

        "clientEndDate": "2026-08-29",

        "specification": "<p>Postman ERP XYZ</p>\n",

        "poNumber": "PUR-ALX-0021",

        "deliverySchedule": "0",

        "pacing": "0",

        "billingType": "monthly",

        "invoiceNumber": "",

        "documents": "",

        "timezone": "",

        "client_cid": "CID-0021",

        "client_io": "IO-0021",

        "client_campaign_name": "Camp-Test-019",

        "productItems": [

            {

                "orderProductId": "8434",

                "productName": "CS",

                "pricingType": "USD",

                "quantityType": "No of Leads",

                "productCatName": "Lead Generation",

                "productType": "1",

                "productStartDate": "2026-06-29",

                "productEndDate": "2026-08-29",

                "bilableType": "Yes",

                "quantity": 1010,

                "pricing": 10,

                "totalAmount": 10100,

                "productId": "7343890304509935616",

                "productCatId": "7343889870839873536",

                "isDelete": False

            }

        ],

        "paymentTerms": [

            {

                "paymentTermsId": "",

                "termName": "2",

                "description": "",

                "dueDate": "2026-06-29T18:30:00.000Z",

                "invoicePortion": "100",

                "amount": "10000.00"

            }

        ],

        "contacts": [

            {

                "contactId": "7209921928574795776",

                "contactPerson": "test",

                "contactTitle": "t",

                "phoneNumber": "9080984544",

                "emailId": "t@gmail.com",

                "timeZone": "Pacific/Pago_Pago",

                "contactType": 1

            }

        ],

        "isUpdate": {

            "orderDetails": True,

            "productItems": True,

            "items": True,

            "paymentTerms": True

        },

        "allocation": 1000

    }
 
 
def post_sales_order(payload, token, pulse_so_id):

    headers = {

        "Authorization": f"Bearer {token}",

        "Content-Type": "application/json"

    }
 
    url = f"{ORDER_URL}/order_v2/{pulse_so_id}"
 
    frappe.log_error(

        title="PULSE UPDATE URL",

        message=url

    )
 
    return requests.post(

        url,

        json=payload,

        headers=headers,

        timeout=30

    )
 
 
def update_sales_order(doc, method=None):

    frappe.log_error(

        title="SALES ORDER UPDATE HOOK STARTED",

        message=f"Hook triggered for Sales Order: {doc.name}"

    )
 
    try:

        frappe.msgprint("Sales Order Update Hook Triggered")
 
        pulse_so_id = doc.get("custom_pulse_so_id") or ""
 
        frappe.log_error(

            title="PULSE SO ID CHECK",

            message=f"Sales Order: {doc.name}\ncustom_pulse_so_id: {pulse_so_id}"

        )
 
        if not pulse_so_id:

            frappe.log_error(

                title="PULSE UPDATE ERROR",

                message=f"Sales Order {doc.name} me custom_pulse_so_id empty hai."

            )

            frappe.msgprint("custom_pulse_so_id empty hai.")

            return
 
        config = frappe.get_single("Pulse Sales Configuration")
 
        payload = build_sales_order_payload(doc)
 
        frappe.log_error(

            title="PULSE UPDATE PAYLOAD",

            message=frappe.as_json(payload, indent=2)

        )
 
        token = get_token(config)
 
        response = post_sales_order(payload, token, pulse_so_id)
 
        frappe.log_error(

            title="PULSE UPDATE RAW RESPONSE",

            message=f"""

Status Code: {response.status_code}
 
Response:

{response.text}

"""

        )
 
        if response.status_code == 401:

            frappe.log_error(

                title="PULSE TOKEN EXPIRED",

                message="Token expired. New token generate ho raha hai."

            )
 
            token = pulse_login(config)

            response = post_sales_order(payload, token, pulse_so_id)
 
            frappe.log_error(

                title="PULSE UPDATE RAW RESPONSE AFTER TOKEN REFRESH",

                message=f"""

Status Code: {response.status_code}
 
Response:

{response.text}

"""

            )
 
        response.raise_for_status()
 
        response_data = response.json()
 
        frappe.log_error(

            title="PULSE SALES ORDER UPDATE SUCCESS",

            message=f"""

Sales Order updated successfully.
 
Sales Order: {doc.name}

Pulse SO ID: {pulse_so_id}
 
Response:

{frappe.as_json(response_data, indent=2)}

"""

        )
 
        frappe.msgprint("Sales Order updated successfully with Pulse.")
 
    except Exception:

        frappe.log_error(

            title="PULSE SALES ORDER UPDATE ERROR",

            message=frappe.get_traceback()

        )
 
        frappe.msgprint("Pulse Sales Order update failed. Check Error Log.")
 