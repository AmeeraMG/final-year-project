"""
upload_routes.py
────────────────
Flask routes for file upload, ML processing, NLP generation,
and WhatsApp message sending.
"""

from flask import Blueprint, request, jsonify, session
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

from ml_module import RetailMLSystem
from nlp_module import generate_insights
from whatsapp_service import send_insights

upload_bp = Blueprint("upload", __name__)

UPLOAD_FOLDER  = os.path.join(os.path.dirname(__file__), "uploads")
HISTORY_FILE   = os.path.join(os.path.dirname(__file__), "upload_history.json")
ALLOWED_EXT    = {"xlsx"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _allowed_file(filename: str) -> bool:
    """Check that the file has .xlsx extension"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def _load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def _save_history(records):
    with open(HISTORY_FILE, "w") as f:
        json.dump(records, f, indent=2)


# ── POST /upload ──────────────────────────────────────────────────────────────

@upload_bp.route("/upload", methods=["POST"])
def upload_files():
    # Get phone from FormData (sent by frontend) or session fallback
    phone_number = request.form.get("phone", "").strip() or session.get("phone", "")
    if not phone_number:
        return jsonify({"success": False, "message": "Please login first."}), 401

    # Store in session for this request
    session["logged_in"] = True
    session["phone"] = phone_number

    # Check all three files are present in the request
    required_files = ["sales", "stock", "product"]
    for fname in required_files:
        if fname not in request.files:
            return jsonify({
                "success": False,
                "message": f"All three files are required: sales.xlsx, stock.xlsx, product.xlsx"
            }), 400

    sales_file   = request.files["sales"]
    stock_file   = request.files["stock"]
    product_file = request.files["product"]

    # Validate all files have .xlsx extension
    for f in [sales_file, stock_file, product_file]:
        if f.filename == "":
            return jsonify({"success": False, "message": "All three files are required."}), 400
        if not _allowed_file(f.filename):
            return jsonify({
                "success": False,
                "message": "Please upload Excel files (.xlsx) only"
            }), 400

    # Save files to upload folder with timestamp prefix
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    phone      = session.get("phone", "unknown").replace("+", "")
    user_dir   = os.path.join(UPLOAD_FOLDER, phone)
    os.makedirs(user_dir, exist_ok=True)

    sales_path   = os.path.join(user_dir, f"{timestamp}_sales.xlsx")
    stock_path   = os.path.join(user_dir, f"{timestamp}_stock.xlsx")
    product_path = os.path.join(user_dir, f"{timestamp}_product.xlsx")

    sales_file.save(sales_path)
    stock_file.save(stock_path)
    product_file.save(product_path)

    # Run ML prediction module
    try:
        ml_system  = RetailMLSystem()
        ml_results = ml_system.run(
            sales_path   = sales_path,
            stock_path   = stock_path,
            product_path = product_path,
        )
    except ValueError as e:
        # Validation error from ML module (missing columns etc.)
        return jsonify({"success": False, "message": str(e)}), 422
    except Exception as e:
        return jsonify({"success": False, "message": f"ML processing error: {str(e)}"}), 500

    # Convert ML results to natural language insights (English + Tamil)
    try:
        nlp_output = generate_insights(ml_results)
    except Exception as e:
        return jsonify({"success": False, "message": f"NLP generation error: {str(e)}"}), 500

    # Send WhatsApp messages — phone_number already set at top of function
    print(f"[WhatsApp] Sending to: {phone_number}")
    whatsapp_result = {"overall_success": False, "note": "WhatsApp not configured"}

    try:
        whatsapp_result = send_insights(
            phone_number = phone_number,
            english_msg  = nlp_output["english"],
            tamil_msg    = nlp_output["tamil"],
        )
    except Exception as e:
        # WhatsApp failure should not block the response
        whatsapp_result = {"overall_success": False, "error": str(e)}

    # Save upload record to history
    history = _load_history()
    history.append({
        "phone"      : phone_number,
        "upload_date": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "files"      : {
            "sales"  : sales_file.filename,
            "stock"  : stock_file.filename,
            "product": product_file.filename,
        },
        "whatsapp_sent": whatsapp_result.get("overall_success", False),
    })
    _save_history(history)

    return jsonify({
        "success"        : True,
        "message"        : "Files processed successfully!",
        "ml_results"     : ml_results,
        "insights"       : nlp_output,
        "whatsapp"       : whatsapp_result,
    }), 200


# ── GET /upload-history ───────────────────────────────────────────────────────

@upload_bp.route("/upload-history", methods=["GET"])
def upload_history():
    if not session.get("logged_in"):
        return jsonify({"success": False, "message": "Please login first."}), 401

    phone   = session.get("phone")
    history = _load_history()

    # Filter records for the current user only
    user_history = [h for h in history if h.get("phone") == phone]
    # Return most recent first
    user_history.reverse()

    return jsonify({"success": True, "history": user_history}), 200