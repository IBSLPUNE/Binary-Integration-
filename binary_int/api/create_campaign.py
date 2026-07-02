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
 
 
def format_campaign_date(value):
    return f"{value}T00:00:00.000Z" if value else ""
 
 
def build_campaign_payload(doc):
    sales_order = frappe.get_doc("Sales Order", doc.custom_sales_order_no)
    so_item = frappe.get_doc("Sales Order Item", doc.custom_so_item_row)
 
    qty = int(doc.custom_qty or 0)
    cpl = float(getattr(doc, "custom_cpl", 0) or so_item.rate or 0)
    total_amount = qty * cpl
 
    go_live_date = (
        doc.custom_go_live_dateclient_start_date
        or doc.expected_start_date
        or sales_order.transaction_date
    )
    end_date = (
        doc.custom_campaign_end_date
        or doc.expected_end_date
        or sales_order.delivery_date
    )
    client_end_date = doc.custom_client_end_date or sales_order.delivery_date
 
    pulse_order_id = (
        getattr(sales_order, "custom_pulse_order_id", None)
        or "7467494085952012288"
    )
 
    return {
        "userId": "20386",
        "campaignCode": doc.name,
        "orderId": str(pulse_order_id),
        "campaignMode": 1,
        "campaignType": doc.project_type or "CS",
        "campaignName": doc.project_name or doc.name,
        "isDirect": 0,
        "deliverySchedule": doc.custom_delivery_schedule or "6607904512776601600",
        "pacing": doc.custom_pacing or "6607904114242224128",
        "description": doc.notes or "<p>test</p>",
        "allocation": qty or 100,
        "billableBonus": 0,
        "nonBillableBonus": 0,
        "goLiveDate": str(go_live_date) if go_live_date else "",
        "endDate": str(end_date) if end_date else "",
        "clientEndDate": str(client_end_date) if client_end_date else "",
        "priority": priority_value(doc.priority) or 1,
        "jobTitle": doc.custom_job_title or "All",
        "employeeSize": doc.custom_employee_size or "All",
        "industry": doc.custom_industry or "All",
        "geo": doc.custom_geo or "All",
        "revenueRange": doc.custom_revenue_requirement or "All",
        "status": "live",
        "deliveryMode": ["excel-delivery", "csv-upload"],
        "specs": doc.notes or "test",
        "request_id": doc.custom_dba_request_id or "test",
        "spoc": {
            "ops": ["516"],
            "sales": ["20415"],
            "delivery": ["20415"],
            "qa": ["515"],
            "salesOps": ["20415"],
            "dba": ["515"]
        },
        "firstDelivery": {
            "opsDatetime": str(doc.custom_first_delivery_date) if doc.custom_first_delivery_date else "2026-06-02 08:37",
            "opsTimezone": doc.custom_new_timezone_2 or "2",
            "opsAllocation": int(doc.custom_fd_allocation or 5),
            "clientDatetime": str(doc.custom_first_delivery_date) if doc.custom_first_delivery_date else "2026-06-02 08:37",
            "clientTimezone": doc.custom_new_timezone_2 or "2",
            "clientAllocation": int(doc.custom_fd_allocation or 2)
        },
        "deliveryDays": {
            "opsDays": to_list(doc.custom_delivery_days) or ["monday"],
            "opsTime": str(doc.custom_delivery_time) if doc.custom_delivery_time else "2026-06-05T17:07:13.761Z",
            "opsTimezone": doc.custom_new_timezone or "2",
            "clientDays": to_list(doc.custom_delivery_days) or ["tuesday"],
            "clientTime": str(doc.custom_delivery_time) if doc.custom_delivery_time else "2026-06-05T17:08:13.761Z",
            "clientTimezone": doc.custom_new_timezone or "2",
            "opsDeliveryDays": [
                {
                    "deliveryDate": "2026-06-08",
                    "deliverytime": "15:07:00",
                    "timeZone": "2",
                    "allocation": 23
                }
            ],
            "clientDeliveryDays": [
                {
                    "deliveryDate": "2026-06-09",
                    "deliverytime": "15:08:00",
                    "timeZone": "2",
                    "allocation": 24
                }
            ]
        },
        "products": [
            {
                "startDate": format_campaign_date(go_live_date),
                "endDate": format_campaign_date(client_end_date),
                "type": "Base",
                "numberOfLeads": qty or 100
            }
        ],
        "items": [
            {
                "itemName": [so_item.item_name or ""],
                "itemCode": [so_item.item_code or ""],
                "quantity": [str(qty or "")],
                "cpl": [str(cpl or "")],
                "totalAmount": [str(total_amount or "")]
            }
        ],
        "emailSubject": doc.subject or ""
    }
 
 
 
def post_campaign(payload, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "PostmanRuntime/7.37.3"
    }
 
    frappe.log_error(
        title="Pulse Campaign Request Debug",
        message=frappe.as_json({
            "url": CAMPAIGN_URL,
            "headers": {
                "Authorization": f"Bearer {token[:20]}...",
                "Content-Type": headers.get("Content-Type"),
                "Accept": headers.get("Accept"),
                "User-Agent": headers.get("User-Agent")
            },
            "payload": payload
        }, indent=2)
    )
 
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

        