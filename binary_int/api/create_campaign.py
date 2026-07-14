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

    response = requests.post(
        config.url,
        json=payload,
        timeout=30
    )
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


def priority_value(priority):
    mapping = {
        "Low": 1,
        "Medium": 2,
        "High": 3
    }
    return mapping.get(priority, 2)


def format_campaign_date(value):
    if not value:
        return ""

    return f"{value}T00:00:00.000Z"


def format_time(value):
    if not value:
        return ""

    return str(value).split(".")[0]


def format_datetime(date_value, time_value=None):
    if not date_value:
        return ""

    formatted_time = format_time(time_value) or "15:00:00"
    return f"{date_value} {formatted_time[:5]}"


def format_iso_datetime(date_value, time_value=None):
    if not date_value:
        return ""

    formatted_time = format_time(time_value) or "15:00:00"
    return f"{date_value}T{formatted_time}.000Z"


def get_campaign_id_from_response(data):
    if not data:
        return None

    response_data = data.get("data") or {}

    return (
        data.get("campaignId")
        or data.get("id")
        or data.get("campaign_id")
        or response_data.get("campaignId")
        or response_data.get("id")
        or response_data.get("campaign_id")
    )


def build_delivery_scheduler_rows(doc):
    rows = []

    for row in doc.get("custom_delivery_scheduler") or []:
        delivery_date = row.get("delivery_date")

        if not delivery_date:
            continue

        rows.append({
            "deliveryDate": str(delivery_date),
            "deliverytime": format_time(
                row.get("delivery_time")
            ) or "15:00:00",
            "timeZone": str(
                row.get("timezone")
                or doc.get("custom_new_timezone")
                or "2"
            ),
            "allocation": int(
                row.get("allocation")
                or 0
            )
        })

    return rows


def build_delivery_days_payload(doc, go_live_date):
    delivery_days = [
        str(row.get("day")).strip().lower()
        for row in doc.get("custom_delivery_days") or []
        if row.get("day")
    ]

    scheduler_rows = build_delivery_scheduler_rows(doc)

    delivery_time = doc.get("custom_delivery_time")
    client_time = doc.get("custom_time") or delivery_time
    timezone = doc.get("custom_new_timezone") or "2"

    return {
        "opsDays": delivery_days,
        "opsTime": format_iso_datetime(
            go_live_date,
            delivery_time
        ),
        "opsTimezone": str(timezone),
        "clientDays": delivery_days,
        "clientTime": format_iso_datetime(
            go_live_date,
            client_time
        ),
        "clientTimezone": str(timezone),
        "opsDeliveryDays": scheduler_rows,
        "clientDeliveryDays": [
            dict(row)
            for row in scheduler_rows
        ]
    }


def build_campaign_payload(doc, is_update=False):
    sales_order = frappe.get_doc(
        "Sales Order",
        doc.custom_sales_order_no
    )

    so_item = frappe.get_doc(
        "Sales Order Item",
        doc.custom_so_item_row
    )

    pulse_order_id = sales_order.get("custom_pulse_so_id")

    if not pulse_order_id:
        frappe.throw(
            f"Pulse Sales Order ID missing in Sales Order "
            f"{sales_order.name}"
        )

    qty = int(doc.get("custom_qty") or 0)
    cpl = float(
        doc.get("custom_cpl")
        or so_item.rate
        or 0
    )
    total_amount = qty * cpl

    go_live_date = (
        doc.get("custom_go_live_dateclient_start_date")
        or doc.get("expected_start_date")
        or sales_order.transaction_date
    )

    client_end_date = (
        doc.get("custom_client_end_date")
        or sales_order.delivery_date
    )

    first_delivery_date = (
        doc.get("custom_first_delivery_date")
        or go_live_date
    )

    ops_delivery_time = (
        doc.get("custom_delivery_time")
        or "15:00:00"
    )

    client_delivery_time = (
        doc.get("custom_time")
        or ops_delivery_time
    )

    payload = {
        "userId": "20386",
        "campaignCode": doc.name,
        "orderId": str(pulse_order_id),
        "campaignMode": 1,
        "campaignType": doc.get("project_type") or "CS",
        "campaignName": doc.get("project_name") or doc.name,
        "isDirect": 0,
        "deliverySchedule": (
            doc.get("custom_delivery_schedule")
            or ""
        ),
        "pacing": doc.get("custom_pacing") or "",
        "description": doc.get("notes") or "",
        "allocation": qty,
        "billableBonus": 0,
        "nonBillableBonus": 0,
        "goLiveDate": (
            str(go_live_date)
            if go_live_date
            else ""
        ),
        "endDate": (
            str(client_end_date)
            if client_end_date
            else ""
        ),
        "clientEndDate": (
            str(client_end_date)
            if client_end_date
            else ""
        ),
        "priority": priority_value(
            doc.get("priority")
        ),
        "jobTitle": (
            doc.get("custom_job_title")
            or "All"
        ),
        "employeeSize": (
            doc.get("custom_employee_size")
            or "All"
        ),
        "industry": (
            doc.get("custom_industry")
            or "All"
        ),
        "geo": (
            doc.get("custom_geo")
            or "All"
        ),
        "revenueRange": (
            doc.get("custom_revenue_requirement")
            or "All"
        ),
        "status": "live",
        "deliveryMode": [],
        "specs": doc.get("notes") or "",
        "request_id": (
            doc.get("custom_dba_request_id")
            or None
        ),
        "spoc": {
            "ops": [],
            "sales": [],
            "delivery": [],
            "qa": [],
            "salesOps": [],
            "dba": []
        },
        "products": [
            {
                "startDate": format_campaign_date(
                    go_live_date
                ),
                "endDate": format_campaign_date(
                    client_end_date
                ),
                "type": "Base",
                "numberOfLeads": qty
            }
        ],
        "items": [
            {
                "itemName": [
                    so_item.item_name or ""
                ],
                "itemCode": [
                    so_item.item_code or ""
                ],
                "quantity": [
                    str(qty)
                ],
                "cpl": [
                    str(cpl)
                ],
                "totalAmount": [
                    str(total_amount)
                ]
            }
        ],
        "emailSubject": doc.get("subject") or ""
    }

    if is_update:
        payload["firstDelivery"] = {
            "opsDatetime": format_datetime(
                first_delivery_date,
                ops_delivery_time
            ),
            "opsTimezone": str(
                doc.get("custom_new_timezone_2")
                or "2"
            ),
            "opsAllocation": int(
                doc.get("custom_fd_allocation")
                or 0
            ),
            "clientDatetime": format_datetime(
                first_delivery_date,
                client_delivery_time
            ),
            "clientTimezone": str(
                doc.get("custom_new_timezone_2")
                or "2"
            ),
            "clientAllocation": int(
                doc.get("custom_fd_allocation")
                or 0
            )
        }

        payload["deliveryDays"] = build_delivery_days_payload(
            doc,
            go_live_date
        )

    return payload


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
        if (
            not doc.get("custom_sales_order_no")
            or not doc.get("custom_so_item_row")
        ):
            frappe.log_error(
                title="Pulse Campaign Create Skipped",
                message=(
                    f"Project {doc.name} missing Sales Order "
                    f"or Sales Order Item Row"
                )
            )
            return

        config = frappe.get_single(
            "Pulse Sales Configuration"
        )

        payload = build_campaign_payload(
            doc,
            is_update=False
        )

        token = get_token(config)
        response = post_campaign(payload, token)

        if response.status_code == 401:
            token = pulse_login(config)
            response = post_campaign(payload, token)

        if not response.ok:
            frappe.log_error(
                title="Pulse Campaign Create Failed",
                message=(
                    f"Status: {response.status_code}\n"
                    f"Response: {response.text}\n"
                    f"Payload:\n"
                    f"{frappe.as_json(payload, indent=2)}"
                )
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
            message=(
                f"Project {doc.name} created in Pulse.\n"
                f"Response:\n{response.text}"
            )
        )

    except Exception:
        frappe.log_error(
            title="Pulse Campaign Create Error",
            message=frappe.get_traceback()
        )


def update_campaign(doc, method=None):
    if getattr(doc.flags, "in_insert", False):
        return

    if (
        not doc.get("custom_sales_order_no")
        or not doc.get("custom_so_item_row")
    ):
        return

    campaign_id = doc.get("custom_pulse_so_id")

    if not campaign_id:
        frappe.log_error(
            title="Pulse Campaign Update Skipped",
            message=(
                f"Project {doc.name} has no "
                f"custom_pulse_so_id"
            )
        )
        return

    try:
        config = frappe.get_single(
            "Pulse Sales Configuration"
        )

        payload = build_campaign_payload(
            doc,
            is_update=True
        )

        token = get_token(config)
        response = put_campaign(
            campaign_id,
            payload,
            token
        )

        if response.status_code == 401:
            token = pulse_login(config)
            response = put_campaign(
                campaign_id,
                payload,
                token
            )

        if not response.ok:
            frappe.log_error(
                title="Pulse Campaign Update Failed",
                message=(
                    f"Campaign ID: {campaign_id}\n"
                    f"Status: {response.status_code}\n"
                    f"Response: {response.text}\n"
                    f"Payload:\n"
                    f"{frappe.as_json(payload, indent=2)}"
                )
            )
            return

        frappe.log_error(
            title="Pulse Campaign Update Success",
            message=(
                f"Project {doc.name} updated in Pulse.\n"
                f"Response:\n{response.text}"
            )
        )

    except Exception:
        frappe.log_error(
            title="Pulse Campaign Update Error",
            message=frappe.get_traceback()
        )
