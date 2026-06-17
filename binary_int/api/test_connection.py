import frappe
import requests
 
 
@frappe.whitelist()
def pulse_login():
    try:
        config = frappe.get_single("Pulse Sales Configuration")
 
        url = config.url
        username = config.username
        password = config.get_password("password")
 
        payload = {
            "emailId": username,
            "password": password,
            "lsRememberMe": True
        }
 
        response = requests.post(url, json=payload, timeout=30)
 
        response.raise_for_status()
 
        return response.json()
 
    except requests.exceptions.RequestException as e:
        frappe.log_error(
            title="Pulse Login API Error",
            message=frappe.get_traceback()
        )
        return {
            "status": "error",
            "message": str(e)
        }
 
    except Exception as e:
        frappe.log_error(
            title="Pulse Login Error",
            message=frappe.get_traceback()
        )
        return {
            "status": "error",
            "message": str(e)
        }