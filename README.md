# SAITM Placement Portal — Backend

Django 6 + Django REST Framework, connected to Supabase (PostgreSQL).

## Setup

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Open .env and paste your real Supabase DATABASE_URL (from Supabase → Connect → Direct connection → URI)
# Replace [YOUR-PASSWORD] with your actual database password, keep ?sslmode=require at the end.

python manage.py migrate
python manage.py createsuperuser   # creates your first Admin / Django Admin login
python manage.py runserver
```

Server runs at `http://127.0.0.1:8000`. Admin panel at `http://127.0.0.1:8000/admin`.

## Creating a Placement Manager account

There's no PM self-registration (matches the frontend — PM accounts are admin-created only).
Easiest way for now, from the Django shell:

```bash
python manage.py shell
```
```python
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_user(
    username="placementmanager@saitm.ac.in",
    email="placementmanager@saitm.ac.in",
    password="choose-a-real-password",
    role="placement_manager",
    is_active=True,
)
```

## API Reference

| Method | Endpoint | Who | Purpose |
|---|---|---|---|
| POST | `/api/auth/register/` | Public | Student signup (creates inactive user + OTP) |
| POST | `/api/auth/verify-otp/` | Public | Verify OTP, activates account, returns JWT |
| POST | `/api/auth/login/` | Public | Login (student or PM) — returns role + JWT |
| GET | `/api/auth/me/` | Authenticated | Current user info |
| GET/PATCH | `/api/students/me/` | Student | Own profile |
| PATCH | `/api/students/me/mandatory/` | Student | Registration step 1 (required) |
| PATCH | `/api/students/me/optional/` | Student | Registration step 2 (skippable) |
| GET | `/api/students/?course=&batch=` | PM | Student Database, filterable |
| GET | `/api/drives/` | Authenticated | All open drives (student Notifications page) |
| POST | `/api/drives/` | PM | Create a drive (Drive Creation page) |
| GET | `/api/drives/mine/` | PM | Drives Floated — own drives only |
| POST | `/api/drives/<id>/apply/` | Student | Apply — server re-checks eligibility + deadline |
| GET | `/api/applications/?course=&batch=&company=` | PM | Students Applied, filterable |
| GET | `/api/applications/mine/` | Student | Own applications |

All authenticated endpoints expect `Authorization: Bearer <access_token>`.

## Notes

- **OTP is printed to the console** right now (`[DEV ONLY] OTP for ...`), not emailed. Wiring real email (SMTP / SES / Resend / Postmark) is the next step before this goes live.
- **WhatsApp notifications** aren't wired yet — needs a provider (Gupshup/Interakt recommended for India) plugged into the drive-publish flow, triggered alongside the email.
- Eligibility (`course` + `batch` match) and deadline are **re-checked server-side** on every Apply — this is deliberate, matching the security discussion earlier: the frontend's disabled button is UX only, this is the real gate.
