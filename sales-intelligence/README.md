# Sales Intelligence — Setup Guide

A college project web application that helps small retailers analyze their
sales data using machine learning, and delivers insights via WhatsApp.

---

## Project Structure

```
sales-intelligence/
├── backend/
│   ├── app.py                ← Flask main entry point
│   ├── auth_routes.py        ← /register, /login, /profile, /logout
│   ├── upload_routes.py      ← /upload, /upload-history
│   ├── ml_module.py          ← ML prediction engine (from notebook)
│   ├── nlp_module.py         ← English + Tamil insight generator
│   ├── whatsapp_service.py   ← WhatsApp Cloud API integration
│   ├── requirements.txt
│   └── uploads/              ← Uploaded Excel files stored here
│
└── frontend/
    ├── index.html            ← Landing page
    ├── login.html            ← Login page
    ├── register.html         ← Create account page
    ├── upload.html           ← Upload files + view results
    ├── profile.html          ← User profile page
    ├── history.html          ← Upload history page
    ├── css/style.css
    └── js/
        ├── auth.js           ← Login, register, session management
        ├── upload.js         ← File upload and results rendering
        └── validation.js     ← Phone, email, form validation
```

---

## Step 1 — Backend Setup

### Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Configure WhatsApp API

Open `whatsapp_service.py` and fill in your credentials:

```python
ACCESS_TOKEN    = "your_whatsapp_access_token"
PHONE_NUMBER_ID = "your_phone_number_id"
```

Or set them as environment variables:

```bash
export WHATSAPP_ACCESS_TOKEN="your_token"
export WHATSAPP_PHONE_NUMBER_ID="your_id"
```

Get these from: https://developers.facebook.com/apps/

### Run the backend

```bash
cd backend
python app.py
```

Backend will start at: http://127.0.0.1:5000

---

## Step 2 — Frontend Setup

Open `frontend/index.html` in a browser.

**Recommended:** Use VS Code Live Server extension to open the frontend,
because `fetch()` with credentials requires a proper origin (not `file://`).

1. Install VS Code extension: **Live Server**
2. Right-click `index.html` → **Open with Live Server**
3. It will open at `http://127.0.0.1:5500`

---

## Step 3 — Excel File Format

### sales.xlsx

| date       | product_name | quantity_sold | unit_price |
|------------|-------------|---------------|------------|
| 2026-03-10 | Rice        | 10            | 60         |

### stock.xlsx

| date       | product_name | stock_loaded |
|------------|-------------|--------------|
| 2026-03-10 | Rice        | 100          |

### product.xlsx

| product_id | product_name | costprice |
|------------|-------------|-----------|
| P101       | Rice        | 45        |

---

## Step 4 — How to Use

1. Open the frontend in browser
2. Click **Create Account** — fill in name, phone (+91...), email, shop name, location
3. Login with your phone number and password
4. Go to **Upload** page
5. Select all three Excel files
6. Click **Analyze & Send Insights**
7. View ML results and insights on screen
8. WhatsApp messages sent automatically to your login phone number

---

## API Endpoints

| Method | Endpoint         | Description              |
|--------|-----------------|--------------------------|
| POST   | /register        | Create new user account  |
| POST   | /login           | Login and start session  |
| POST   | /logout          | End session              |
| GET    | /profile         | Get logged-in user info  |
| POST   | /upload          | Upload files + run ML    |
| GET    | /upload-history  | List past uploads        |

---

## Phone Number Format

All phone numbers must follow Indian format:

```
+91XXXXXXXXXX
```

- Must start with `+91`
- Next digit must be 6, 7, 8, or 9
- Exactly 10 digits after `+91`
- Example: `+919876543210`

---

## Notes

- User data is stored in `backend/users.json` (simple file-based storage for college project)
- Upload records stored in `backend/upload_history.json`
- Uploaded Excel files stored in `backend/uploads/<phone>/`
- WhatsApp will only send if you configure valid API credentials
- ML model uses RandomForest + GradientBoosting from scikit-learn
