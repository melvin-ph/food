# FoodShare — Good Food. Brighter Tomorrows.
### Full-Stack Surplus Food Donation and Redistribution Platform

FoodShare is a full-stack, responsive web application connecting surplus food providers—such as restaurants, hotels, hostels, caterers, and event organizers—with charitable NGOs, community kitchens, and registered individuals who need food.

The platform eliminates avoidable food waste, protects hygiene and dietary requirements, and ensures an auditable redistribution lifecycle with automated quantity reservations, collection confirmations, and sustainability analytics.

---

## 1. Key Features & Role-Based Workflows

### 🍽️ Food Donors (Restaurants, Hotels, Caterers, Hostels)
- **Real-Time Surplus Listings:** Create listings specifying food type, category, remaining quantity, dietary classification (Vegetarian/Non-Vegetarian/Vegan), allergens, storage temperatures, and pickup windows.
- **Atomic Allocation Management:** When requests are approved, available quantity is reserved automatically to prevent over-allocation.
- **Request Oversight:** Accept or decline incoming collection requests with custom notes.
- **Handover Confirmation:** Mark donations as collected and review comprehensive redistribution history.
- **Impact Metrics:** Automated calculation of total food rescued (kg) and greenhouse gas emission offsets.

### 🏢 NGOs & Charitable Organizations
- **Surplus Discovery Feed:** Browse and filter food by distance, category, quantity, dietary classification, and pickup deadlines.
- **One-Click Food Requests:** Request specified quantities for community shelters and distribution programs.
- **Pickup Coordination:** Access donor service entry directions and designated pickup windows.
- **Monthly Impact Dashboard:** Interactive Chart.js analytics tracking meals distributed, beneficiaries fed, and food rescued.

### 🙋 Individual Recipients
- **Mobile-Friendly Access:** Dignified browsing of fresh, wholesome food available locally.
- **Equitable Request Safeguards:** Built-in configurable request limits (max 10 units per request) to prevent hoarding.
- **Private & Secure:** Individual contact information is never publicly displayed.

### 🛡️ Platform Administrators
- **System Oversight:** Real-time metrics calculated directly from database records (users, listings, requests, food quantity redistributed).
- **User Verification:** Review and verify donor facility credentials and NGO registration documents.
- **Safety Incident Center:** Investigate reported food listings and remove non-compliant entries immediately.
- **Audit Logs & Configuration:** Review immutable action logs and adjust global settings and allowed food categories.

---

## 2. Technology Stack

- **Frontend:** HTML5, CSS3 (Custom FoodShare Design System), JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons.
- **Backend:** Python Flask 3.x with modular blueprints.
- **Database:** MongoDB via PyMongo (with transparent, persistent local development fallback for offline evaluation).
- **Authentication:** Flask session-based authentication with Werkzeug PBKDF2:SHA256 password hashing.
- **Forms & Security:** Flask-WTF CSRF protection, input sanitization, and role-based route decorators.
- **Analytics & Data Visualization:** Chart.js 4.x.
- **Configuration:** `python-dotenv`.
- **Assets:** Authentic, documentary culinary photography generated specifically for surplus food recovery.

---

## 3. Brand Identity & Design System

The application implements the specified dark green and warm charcoal design tokens:

| Token | Hex Code | Purpose |
|---|---|---|
| **Main Background** | `#0B0D0B` | Deep contrast background |
| **Secondary Background** | `#111511` | Sidebar and page sections |
| **Card Background** | `#191E1A` | Surface cards and data containers |
| **Elevated Surface** | `#222923` | Inner callouts and table headers |
| **Primary Green** | `#39D353` | Donor highlights and CTA buttons |
| **Warm Orange** | `#FF8A24` | NGO & recipient actions |
| **Borders** | `#303A32` | Subtle structural division |
| **Primary Text** | `#FFFFFF` | Headings and high-contrast labels |
| **Secondary Text** | `#B9C2BB` | Supporting captions and metadata |

---

## 4. Project Directory Structure

```text
foodshare/
├── app.py                     # Flask application factory & routing setup
├── config.py                  # Environment and application configuration
├── requirements.txt           # Project dependencies
├── .env.example               # Template environment variables
├── .env                       # Local environment settings
├── .gitignore                 # Version control exclusions
├── README.md                  # Comprehensive documentation
├── seed_demo.py               # Seed script for demo accounts & sample listings
├── schema_setup.py            # MongoDB collections & index initialization
├── test_app.py                # Automated end-to-end test suite
├── database/
│   ├── __init__.py
│   ├── db.py                  # PyMongo connection manager & persistent fallback
│   └── local_db_dump.json     # Seeded persistent storage dump
├── routes/
│   ├── __init__.py
│   ├── auth.py                # Login, registration, profile routes
│   ├── public.py              # Homepage, how it works, impact, safety, contact
│   ├── donor.py               # Donor dashboard, listings, requests
│   ├── ngo.py                 # NGO dashboard, browse, collection history
│   ├── recipient.py           # Individual recipient dashboard & requests
│   ├── donations.py           # Donation details & report listing
│   ├── notifications.py       # Notification center
│   ├── admin.py               # Administrator controls & audit logs
│   └── reports.py             # JSON API for Chart.js analytics
├── services/
│   ├── auth_service.py        # Password hashing & role-based decorators
│   ├── donation_service.py    # Donation lifecycle & auto-expiry
│   ├── request_service.py     # Request approval & atomic quantity deduction
│   ├── notification_service.py# In-app notifications
│   └── reporting_service.py   # Database query aggregation & chart statistics
├── static/
│   ├── css/
│   │   └── style.css          # Design system stylesheet
│   ├── js/
│   │   └── main.js            # Client-side interactive scripts & badge updater
│   └── images/                # Documentary culinary assets & uploads
└── templates/                 # Modular Jinja2 templates (base, auth, donor, etc.)
```

---

## 5. Prerequisites

- **Python:** 3.10, 3.11, or 3.12 installed.
- **MongoDB:** (Optional) Local MongoDB daemon or MongoDB Atlas URI. If MongoDB is not installed or running, the application automatically uses its built-in PyMongo-compatible persistent store, ensuring zero-configuration execution during academic evaluation!

---

## 6. Installation & Quickstart

### Step 1: Clone or Open the Workspace
```powershell
cd c:\Users\urk24cs9067\Desktop\Projects\Abiya
```

### Step 2: (Optional) Set Up Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Default configuration values:
```env
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=foodshare_db
SECRET_KEY=foodshare-dev-secret-key-replace-in-production
APP_ENV=development
APP_TIMEZONE=Asia/Kolkata
MAX_CONTENT_LENGTH=5242880
```

### Step 5: Seed Demonstration Accounts & Sample Data
Run the idempotent seed script:
```powershell
python seed_demo.py
```
This populates sample accounts, food categories, realistic surplus listings (Veg Dum Biryani, Fried Rice, Fresh Produce, Whole Wheat Rotis), requests, and notifications.

### Step 6: Run the Application
```powershell
python app.py
```
Open your browser and navigate to:
**`http://127.0.0.1:5000/`**

---

## 7. Demonstration Accounts (1-Click Login)

The login screen includes one-click buttons to instantly fill and sign into each role:

| Role | Email | Password | Access Portal |
|---|---|---|---|
| **Donor** | `donor@foodshare.com` | `Donor123!` | `/donor/dashboard` |
| **NGO** | `ngo@foodshare.com` | `Ngo123!` | `/ngo/dashboard` |
| **Recipient** | `user@foodshare.com` | `User123!` | `/recipient/dashboard` |
| **Administrator** | `admin@foodshare.com` | `Admin123!` | `/admin/dashboard` |

> For comprehensive details on role permissions and demo profiles, see [CREDENTIALS.md](CREDENTIALS.md).

---


## 8. Automated End-to-End Testing

To run the automated test suite verifying all routes, password security, role permissions, and the full donation request/approval lifecycle:

```powershell
python test_app.py
```

Expected result:
```text
Ran 4 tests in X.XXs
OK
End-to-end donation and request test PASSED successfully!
```

---

## 9. Food Donation & Redistribution Lifecycle

1. **Listing Publication:** Donor submits surplus food item details. Validation ensures positive quantity, future expiry date, and safety declaration.
2. **Surplus Discovery:** Available food appears immediately on the public landing page, NGO portal, and Recipient portal.
3. **Request Submission:** Recipient or NGO specifies requested quantity and pickup window. System verifies requested quantity does not exceed remaining availability.
4. **Donor Review & Allocation:** Donor accepts the request. The application atomically decrements the listing's remaining quantity and marks the listing as `Partially Reserved` or `Fully Reserved`.
5. **Collection Confirmation:** Recipient arrives at donor premises. Either party clicks "Confirm Collection".
6. **Metrics Updating:** The database increments redistributed food totals, updates user stats, and creates permanent audit logs.

---

## 10. Security & Quality Assurance

- **Password Hashing:** Passwords are never stored in plaintext; all credentials use PBKDF2:SHA256 with cryptographically strong salt.
- **CSRF Protection:** Every state-changing form is secured with Flask-WTF CSRF tokens.
- **Strict Role Authorization:** Routes are protected with server-side `@role_required(...)` decorators. Normal users cannot access admin or other users' private settings.
- **Admin Isolation:** Public registration is restricted to Donors, NGOs, and Individuals. Admin accounts cannot be created from public signup.
- **Atomic Concurrency Protection:** Quantities are checked and reserved atomically to prevent duplicate requests or negative allocations.
- **Image Upload Sanitization:** Permitted extensions (`.jpg`, `.png`, `.jpeg`, `.webp`), 5MB size limits, and `secure_filename` enforcement.
