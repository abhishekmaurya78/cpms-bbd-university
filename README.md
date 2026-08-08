# Campus Placement Management System (CPMS)

A complete, production-ready Campus Placement Management System web application built with **Flask**, **SQLAlchemy**, **PostgreSQL** (with **SQLite fallback**), **Flask-Login**, and **Flask-Mail**.

---

## 🌟 Key Features

1. **Multi-Role System**:
   - **Student Portal**: Register, update academic details (branch, semester, CGPA, skills), browse eligible jobs whose deadlines have not passed, apply with one-click, and track application status (`applied`, `shortlisted`, `rejected`, `selected`).
   - **Employer Portal**: Register, post job openings (with package, requirements, CGPA criteria, deadline), view candidate applications, and evaluate/update candidate statuses.
   - **Placement Cell Admin**: Overview dashboard of all registered students, companies, active jobs, and system-wide application tracking.
   - **Super Admin Panel**: Restricted master control panel accessible strictly by `abhishekmaurya53957@gmail.com`. Includes total platform metrics, admin account management (create & toggle active/inactive status), and shortcuts to all role dashboards.

2. **Automatic Database Connection & Fallback**:
   - Reads `DATABASE_URL` environment variable for PostgreSQL. Handles `postgres://` to `postgresql://` conversion.
   - If PostgreSQL is unavailable or unconfigured, automatically falls back to SQLite (`sqlite:///cpms.db`) without crashing.

3. **Authentication & Password Recovery**:
   - Session management via Flask-Login.
   - Secure password hashing using Werkzeug Security.
   - Password reset via timed URL tokens (`itsdangerous.URLSafeTimedSerializer`) sent through `Flask-Mail`.
   - Security protection blocking Super Admin account from password reset.

4. **Dynamic UI & Error Handling**:
   - Single Jinja2 `base.html` template layout extended by all pages.
   - Dynamic navbar & footer responding to authentication state, role, and email.
   - Custom 404 (Not Found) and 500 (Internal Server Error with automatic database transaction rollback) error pages.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.x, Flask
- **ORM / Database**: Flask-SQLAlchemy (PostgreSQL / SQLite)
- **Auth & Session**: Flask-Login, Werkzeug Security
- **Email & Token**: Flask-Mail, itsdangerous
- **Environment Management**: python-dotenv
- **Frontend**: HTML5, Vanilla JavaScript, CSS3 custom styling

---

## 🚀 Setup & Execution Instructions

1. **Clone / Open Project Directory**:
   ```bash
   cd d:/CPMS
   ```

2. **Create & Activate Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your values if needed:
   ```bash
   cp .env.example .env
   ```

5. **Run Application**:
   ```bash
   python app.py
   ```

---

## 🔑 Default Super Admin Login Credentials

On first run, the system automatically creates the developer Super Admin account:
- **Email**: `abhishekmaurya53957@gmail.com`
- **Password**: `Abhishek@1234`
- **Role**: Super Admin

---

## 💡 SQLite Fallback Note

If PostgreSQL is not running or `DATABASE_URL` is not set, CPMS automatically creates and connects to local SQLite database `cpms.db`. Tables are created automatically on startup inside the application context.
