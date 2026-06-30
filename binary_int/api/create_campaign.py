import frappe
import requests
 
 
CAMPAIGN_URL = "https://api-dev.binaryintent.com/api/campaign-manager/campaign"
 
 
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
 
 
def to_list(value):
    if not value:
        return []
 
    if isinstance(value, list):
        return value
 
    return [
        row.strip()
        for row in str(value).replace("\n", ",").split(",")
        if row.strip()
    ]
 
 
def priority_value(priority):
    mapping = {
        "Low": 1,
        "Medium": 2,
        "High": 3
    }
    return mapping.get(priority, 2)
 
 
def build_campaign_payload(doc):
    sales_order = frappe.get_doc("Sales Order", doc.custom_sales_order_no)
    so_item = frappe.get_doc("Sales Order Item", doc.custom_so_item_row)
 
    qty = int(doc.custom_qty or 0)
    cpl = float(getattr(doc, "custom_cpl", 0) or so_item.rate or 0)
    total_amount = qty * cpl
 
    go_live_date = doc.custom_go_live_dateclient_start_date or doc.expected_start_date
    end_date = doc.custom_campaign_end_date or doc.expected_end_date
    client_end_date = doc.custom_client_end_date or sales_order.delivery_date
 
    return {
        "userId": "20193",
        "campaignCode": doc.name,
        "orderId": sales_order.name,
        "campaignMode": 1,
        "campaignType": doc.project_type or "",
        "campaignName": doc.project_name or doc.name,
        "isDirect": 0,
        "deliverySchedule": doc.custom_delivery_schedule or "",
        "pacing": doc.custom_pacing or "",
        "description": doc.notes or "",
        "allocation": doc.custom_qty,
        "billableBonus": 0,
        "nonBillableBonus": 0,
        "goLiveDate": str(go_live_date) if go_live_date else "",
        "endDate": str(end_date) if end_date else "",
        "clientEndDate": str(client_end_date) if client_end_date else "",
        "priority": priority_value(doc.priority),
        "jobTitle": doc.custom_job_title or "",
        "employeeSize": doc.custom_employee_size or "",
        "industry": doc.custom_industry or "",
        "geo": doc.custom_geo or "",
        "revenueRange": doc.custom_revenue_requirement or "",
        "status": doc.status or "",
        "deliveryMode": to_list(doc.custom_delivery_schedule),
        "specs": doc.notes or "",
        "request_id": doc.custom_dba_request_id or "",
        "spoc": {
            "ops": to_list(getattr(doc, "custom_ops", "")),
            "sales": to_list(getattr(doc, "custom_sales", "")),
            "delivery": to_list(getattr(doc, "custom_delivery", "")),
            "qa": to_list(getattr(doc, "custom_qa", "")),
            "salesOps": to_list(getattr(doc, "custom_sales_ops", "")),
            "dba": to_list(getattr(doc, "custom_dba", ""))
        },
        "firstDelivery": {
            "opsDatetime": str(doc.custom_first_delivery_date) if doc.custom_first_delivery_date else "",
            "opsTimezone": doc.custom_new_timezone_2 or "",
            "opsAllocation": int(doc.custom_fd_allocation or 0),
            "clientDatetime": str(doc.custom_first_delivery_date) if doc.custom_first_delivery_date else "",
            "clientTimezone": doc.custom_new_timezone_2 or "",
            "clientAllocation": int(doc.custom_fd_allocation or 0)
        },
        "deliveryDays": {
            "opsDays": to_list(doc.custom_delivery_days),
            "opsTime": str(doc.custom_delivery_time) if doc.custom_delivery_time else "",
            "opsTimezone": doc.custom_timezone or "",
            "clientDays": to_list(doc.custom_delivery_days),
            "clientTime": str(doc.custom_delivery_time) if doc.custom_delivery_time else "",
            "clientTimezone": doc.custom_new_timezone or doc.custom_new_timezone or "",
            "opsDeliveryDays": [],
            "clientDeliveryDays": []
        },
        "products": [
            {
                "startDate": str(sales_order.transaction_date) if sales_order.transaction_date else "",
                "endDate": str(sales_order.delivery_date) if sales_order.delivery_date else "",
                "type": so_item.item_group or "",
                "numberOfLeads": qty
            }
        ],
        "items": [
            {
                "itemName": [so_item.item_name or ""],
                "itemCode": [so_item.item_code or ""],
                "quantity": [str(qty)],
                "cpl": [str(cpl)],
                "totalAmount": [str(total_amount)]
            }
        ],
        "emailSubject": doc.subject or ""
    }
 
 
def post_campaign(payload, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
 
    return requests.post(
        CAMPAIGN_URL,
        json=payload,
        headers=headers,
        timeout=30
    )
 
 
def create_campaign(doc, method=None):
    frappe.log_error(
        title="PROJECT CAMPAIGN HOOK TEST",
        message=f"Triggered for Project {doc.name}"
    )
 
    try:
        frappe.msgprint("Pulse Campaign sync has been triggered.")
 
        if not doc.custom_sales_order_no or not doc.custom_so_item_row:
            frappe.log_error(
                title="Pulse Campaign Sync Skipped",
                message=f"Project {doc.name} missing Sales Order or Sales Order Item Row"
            )
            return
 
        config = frappe.get_single("Pulse Sales Configuration")
 
        payload = build_campaign_payload(doc)
 
        frappe.log_error(
            title="Pulse Campaign Payload",
            message=frappe.as_json(payload, indent=2)
        )
 
        token = get_token(config)
 
        response = post_campaign(payload, token)
 
        if response.status_code == 401:
            frappe.msgprint("Pulse token expired. Generating a new token.")
 
            token = pulse_login(config)
            response = post_campaign(payload, token)
 
        response.raise_for_status()
 
        frappe.msgprint(
            title="Pulse Campaign Response",
            msg=f"<pre>{frappe.as_json(response.json(), indent=2)}</pre>"
        )
 
        frappe.msgprint("Campaign synced successfully with Pulse.")
 
        frappe.log_error(
            title="Pulse Campaign Sync Success",
            message=f"Project {doc.name} synced successfully with Pulse.\n\nResponse:\n{response.text}"
        )
 
    except Exception:
        frappe.msgprint("Pulse Campaign sync failed. Please check Error Log.")
 
        frappe.log_error(
            title="Pulse Campaign Sync Error",
            message=frappe.get_traceback()
        )