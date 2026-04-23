"""
whatsapp_service.py
───────────────────
Handles sending messages via WhatsApp Cloud API.
Phone number comes from the logged-in user session — never hardcoded.
"""

import requests
import os


# Fill in your WhatsApp Cloud API credentials in .env or config
WHATSAPP_API_URL = "https://graph.facebook.com/v19.0/{phone_number_id}/messages"
ACCESS_TOKEN     = os.getenv("WHATSAPP_ACCESS_TOKEN", "EAARa3LXZCDtEBQyGIc9XBWZAeHRO9hHfp1kwdbVhY9dD1kNie7Sapf4aGGd9ZBt10ZCpbACBVzYfV50iHh28ZCDjPXMFPaUPZCz22aP1yZCDoRkM2ukyHCTZBGJhLqrAqly5azEAy8ILQwfSDctEWVXV2BqZBdsAVhZB5TxBBzMM6ZCyy4xglRpiYWZAen5g9PXgFzZCf2135wM4PjLt3iAZCAXAA30iwcKz5GUEwkGX4r47Nsg6Tmn0OHAmZCXTuC5F3la4SCa5vwbiAsZCDw28jeeCLV2q")
PHONE_NUMBER_ID  = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "1013099101888600")


def send_whatsapp_message(to_phone: str, message: str) -> dict:
    """
    Sends a WhatsApp text message to the given phone number.

    Parameters
    ----------
    to_phone : str  — recipient number in international format, e.g. '+919876543210'
    message  : str  — message body text

    Returns
    -------
    dict with 'success' bool and 'response' or 'error' key
    """
    # Clean the phone number — remove '+' for WhatsApp API
    clean_number = to_phone.replace("+", "").replace(" ", "").replace("-", "")

    url = WHATSAPP_API_URL.format(phone_number_id=PHONE_NUMBER_ID)

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": clean_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            return {"success": True, "response": response.json()}
        else:
            return {
                "success": False,
                "error": f"API returned {response.status_code}: {response.text}"
            }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "WhatsApp API request timed out."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Could not connect to WhatsApp API."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_insights(phone_number: str, english_msg: str, tamil_msg: str) -> dict:
    """
    Sends both English and Tamil insight messages to the user's WhatsApp.
    The phone number must come from the logged-in user session.

    Returns combined result dict.
    """
    results = {}

    # Send English message first
    eng_result = send_whatsapp_message(phone_number, english_msg)
    results["english"] = eng_result

    # Send Tamil message second
    ta_result = send_whatsapp_message(phone_number, tamil_msg)
    results["tamil"] = ta_result

    overall_success = eng_result.get("success", False) or ta_result.get("success", False)
    results["overall_success"] = overall_success

    return results
