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
        row.strip().lower()
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


def get_campaign_id_from_response(data):
    if not data:
        return None

    return (
        data.get("campaignId")
        or data.get("id")
        or data.get("campaign_id")
        or data.get("data", {}).get("campaignId")
        or data.get("data", {}).get("id")
        or data.get("data", {}).get("campaign_id")
    )


def get_safe_time(value):
    if value:
        return str(value).split(".")[0]

    return "15:00:00"


def build_campaign_payload(doc):
    sales_order = frappe.get_doc("Sales Order", doc.custom_sales_order_no)
    so_item = frappe.get_doc("Sales Order Item", doc.custom_so_item_row)

    pulse_order_id = getattr(sales_order, "custom_pulse_so_id", None)

    if not pulse_order_id:
        frappe.throw(f"Pulse Sales Order ID missing in Sales Order {sales_order.name}")

    qty = int(doc.custom_qty or 0)
    cpl = float(getattr(doc, "custom_cpl", 0) or so_item.rate or 0)
    total_amount = qty * cpl

    go_live_date = (
        getattr(doc, "custom_go_live_dateclient_start_date", None)
        or getattr(doc, "expected_start_date", None)
        or sales_order.transaction_date
    )

    end_date = (
        getattr(doc, "custom_campaign_end_date", None)
        or getattr(doc, "expected_end_date", None)
        or sales_order.delivery_date
    )

    client_end_date = (
        getattr(doc, "custom_client_end_date", None)
        or sales_order.delivery_date
    )

    first_delivery_date = (
        getattr(doc, "custom_first_delivery_date", None)
        or go_live_date
        or sales_order.transaction_date
    )

    delivery_time = get_safe_time(getattr(doc, "custom_delivery_time", None))
    delivery_days = to_list(getattr(doc, "custom_delivery_days", None)) or ["monday"]
    first_delivery_datetime = f"{first_delivery_date} 15:00"

    return {
        "userId": "20386",
        "campaignCode": doc.name,
        "orderId": str(pulse_order_id),
        "campaignMode": 1,
        "campaignType": doc.project_type or "CS",
        "campaignName": doc.project_name or doc.name,
        "isDirect": 0,
        "deliverySchedule": doc.custom_delivery_schedule or "",
        "pacing": doc.custom_pacing or "",
        "description": doc.notes or "<p>test</p>",
        "allocation": qty,
        "billableBonus": 0,
        "nonBillableBonus": 0,
        "goLiveDate": str(go_live_date) if go_live_date else "",
        "endDate": str(end_date) if end_date else "",
        "clientEndDate": str(client_end_date) if client_end_date else "",
        "priority": priority_value(doc.priority),
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
            "opsDatetime": first_delivery_datetime,
            "opsTimezone": doc.custom_new_timezone_2 or "2",
            "opsAllocation": int(doc.custom_fd_allocation or qty or 1),
            "clientDatetime": first_delivery_datetime,
            "clientTimezone": doc.custom_new_timezone_2 or "2",
            "clientAllocation": int(doc.custom_fd_allocation or qty or 1)
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
            "deliveryDate": str(doc.custom_first_delivery_date) if doc.custom_first_delivery_date else str(go_live_date),
            "deliverytime": "15:07:00",
            "timeZone": doc.custom_new_timezone or "2",
            "allocation": int(doc.custom_fd_allocation or qty or 1)
        }
    ],
    "clientDeliveryDays": [
        {
            "deliveryDate": str(doc.custom_first_delivery_date) if doc.custom_first_delivery_date else str(go_live_date),
            "deliverytime": "15:08:00",
            "timeZone": doc.custom_new_timezone or "2",
            "allocation": int(doc.custom_fd_allocation or qty or 1)
        }
    ]
},
        "products": [
            {
                "startDate": format_campaign_date(go_live_date),
                "endDate": format_campaign_date(client_end_date),
                "type": "Base",
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
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "PostmanRuntime/7.37.3"
    }

    return requests.post(
        CAMPAIGN_URL,
        json=payload,
        headers=headers,
        timeout=30
    )


def put_campaign(campaign_id, payload, token):
    url = f"{CAMPAIGN_URL}/{campaign_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "PostmanRuntime/7.37.3"
    }

    return requests.put(
        url,
        json=payload,
        headers=headers,
        timeout=30
    )


def create_campaign(doc, method=None):
    try:
        if not doc.custom_sales_order_no or not doc.custom_so_item_row:
            frappe.log_error(
                title="Pulse Campaign Create Skipped",
                message=f"Project {doc.name} missing Sales Order or Sales Order Item Row"
            )
            return

        config = frappe.get_single("Pulse Sales Configuration")
        payload = build_campaign_payload(doc)
        token = get_token(config)

        response = post_campaign(payload, token)

        if response.status_code == 401:
            token = pulse_login(config)
            response = post_campaign(payload, token)

        if not response.ok:
            frappe.log_error(
                title="Pulse Campaign Create Failed",
                message=f"Status: {response.status_code}\nResponse: {response.text}\nPayload:\n{frappe.as_json(payload, indent=2)}"
            )
            return

        data = response.json()
        campaign_id = get_campaign_id_from_response(data)

        if campaign_id:
            doc.db_set(
                "custom_pulse_so_id",
                str(campaign_id),
                update_modified=False
            )

        frappe.log_error(
            title="Pulse Campaign Create Success",
            message=f"Project {doc.name} created in Pulse.\nResponse:\n{response.text}"
        )

    except Exception:
        frappe.log_error(
            title="Pulse Campaign Create Error",
            message=frappe.get_traceback()
        )


def update_campaign(doc, method=None):
    if getattr(doc.flags, "in_insert", False):
        return

    if not doc.custom_sales_order_no or not doc.custom_so_item_row:
        return

    campaign_id = getattr(doc, "custom_pulse_so_id", None)

    if not campaign_id:
        frappe.log_error(
            title="Pulse Campaign Update Skipped",
            message=f"Project {doc.name} has no custom_pulse_so_id"
        )
        return

    try:
        config = frappe.get_single("Pulse Sales Configuration")
        payload = build_campaign_payload(doc)
        token = get_token(config)

        response = put_campaign(campaign_id, payload, token)

        if response.status_code == 401:
            token = pulse_login(config)
            response = put_campaign(campaign_id, payload, token)

        if not response.ok:
            frappe.log_error(
                title="Pulse Campaign Update Failed",
                message=f"Campaign ID: {campaign_id}\nStatus: {response.status_code}\nResponse: {response.text}\nPayload:\n{frappe.as_json(payload, indent=2)}"
            )
            return

        frappe.log_error(
            title="Pulse Campaign Update Success",
            message=f"Project {doc.name} updated in Pulse.\nResponse:\n{response.text}"
        )

    except Exception:
        frappe.log_error(
            title="Pulse Campaign Update Error",
            message=frappe.get_traceback()
        )