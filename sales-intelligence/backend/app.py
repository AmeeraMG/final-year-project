"""
app.py
──────
Main Flask application entry point for Sales Intelligence system.
"""

from flask import Flask
from flask_cors import CORS
import os

from auth_routes import auth_bp
from upload_routes import upload_bp

app = Flask(__name__)

# Secret key for session management — change this in production
app.secret_key = os.getenv("SECRET_KEY", "sales_intelligence_secret_2024")

# Allow cross-origin requests from the frontend
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5500",
                                               "http://localhost:5500",
                                               "http://localhost:3000",
                                               "null"])

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(upload_bp)


@app.route("/", methods=["GET"])
def health_check():
    return {"status": "Sales Intelligence Backend is running", "version": "1.0"}, 200


if __name__ == "__main__":
    print("Starting Sales Intelligence Backend...")
    print("API running at: http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
