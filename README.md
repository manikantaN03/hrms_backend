# Levitica HR Management System

A modern, secure HR management platform built with FastAPI and PostgreSQL.

## 🎉 Latest Updates - Onboarding Module Complete (Feb 18, 2026)

### ✅ New: Complete Onboarding Workflow

The frontend onboarding module is now fully functional with:

1. **11-Step Onboarding Sequence** - All pages working with proper navigation
2. **View Form Modal** - Review complete candidate submissions
3. **Form Validation** - Comprehensive validation at each step
4. **Progress Tracking** - Visual progress bars (0% to 100%)
5. **Sequential Navigation** - Back/Continue buttons on all pages

### 🚀 Quick Test - Onboarding Flow

```bash
# Start frontend (in client directory)
cd client
npm start

# Open in browser
http://localhost:3000/newhire
```

Click "Continue" through all 11 steps to test the complete onboarding flow!

### 📋 Onboarding Steps

| Step | URL | Purpose |
|------|-----|---------|
| 0 | `/newhire` | Welcome & Instructions |
| 1 | `/basicdetails` | Basic Details (Name, DOB, Photo) |
| 2 | `/onboardingcontactdetails` | Contact Details (Mobile, Email) |
| 3 | `/onboardingPersonaldetails` | Personal Info (Blood, Passport, DL) |
| 4 | `/onboardingstatutorydetails` | Statutory (Aadhar, PAN, UAN, ESI) |
| 5 | `/familydetails` | Family Details (Parents Info) |
| 6 | `/onboardingpresentaddress` | Present Address |
| 7 | `/permanentaddress` | Permanent Address |
| 8 | `/onboardingbankdetails` | Bank Details |
| 9 | `/uploaddocument` | Upload Documents |
| 10 | `/final` | Review & Submit |

### 📚 Onboarding Documentation

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Fast reference guide
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Complete overview
- **[ONBOARDING_SEQUENCE_FLOW.md](ONBOARDING_SEQUENCE_FLOW.md)** - Detailed steps
- **[ONBOARDING_FLOW_DIAGRAM.md](ONBOARDING_FLOW_DIAGRAM.md)** - Visual diagrams
- **[VIEW_FORM_MODAL_IMPLEMENTATION.md](VIEW_FORM_MODAL_IMPLEMENTATION.md)** - Modal details
- **[FRONTEND_ANALYSIS.md](FRONTEND_ANALYSIS.md)** - Full frontend analysis

---

## Features

- 🔐 **JWT Authentication** - Secure token-based access control
- 📧 **OTP Email Verification** - Email verification with 6-digit codes
- 👥 **Multi-Role Support** - Superadmin, Admin, and User roles
- 🎯 **Unified User Storage** - Single table architecture for all user types
- 📝 **RESTful API** - Clean, well-documented endpoints
- 🚀 **Production Ready** - Connection pooling, error handling, logging

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- SMTP server (Gmail, Mailmug, or custom)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd levitica-hr


# Create virtual environment
conda create -n levitica_hrms python=3.11.9 -y
conda activate levitica_hrms 


# Install dependencies
python -m pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and SMTP credentials
```

### Database Setup


#  use the standard setup:

python scripts/setup.py



**Note:** 
- The setup script now automatically creates the default business, so you won't encounter the "No business found" error anymore.
- Pandas is only needed for CSV data import. If you don't have CSV files to import, the setup will work fine without pandas.

### Run Application

conda activate levitica_hrms & python -m uvicorn app.main:app --reload

or
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Access the API:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- API Root: http://localhost:800 0 

### Frontend URLs

Access the frontend application:
- **Forms Management**: http://localhost:3000/onboarding/forms
- **Start Onboarding**: http://localhost:3000/newhire
- **Dashboard**: http://localhost:3000/dashboard/overviewsx`x`
- **Login**: http://localhost:3000/login 

### Default Credentials                                                                                                                                                     

```
Email: superadmin@levitica.com
Password: Admin@123
```

⚠️ **Change the default password immediately after first login!**

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/refresh` - Refresh token

### Registration (Public)
- `POST /api/v1/register` - Register new user
- `POST /api/v1/verify-otp` - Verify email OTP
- `POST /api/v1/resend-otp` - Resend OTP
- `POST /api/v1/set-password` - Create password

### Superadmin (Requires Superadmin Role)
- `POST /api/v1/superadmin/admins` - Create admin
- `GET /api/v1/superadmin/admins` - List admins
- `PUT /api/v1/superadmin/admins/{id}` - Update admin
- `DELETE /api/v1/superadmin/admins/{id}` - Delete admin
- `PUT /api/v1/superadmin/users/{id}/role` - Change user role
- `GET /api/v1/superadmin/users` - Get all users
- `PATCH /api/v1/superadmin/users/{id}/status` - Update user status

### File Upload
- `POST /api/v1/upload/profile-image` - Upload profile image (max 4MB)

### System
- `GET /health` - Health check
- `GET /` - API information

## Project Structure

```
levitica-hr/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/      # API route handlers
│   │   ├── deps.py         # Dependencies (auth, etc.)
│   │   └── router.py       # Route aggregation
│   ├── core/
│   │   ├── config.py       # Settings
│   │   ├── database.py     # Database connection
│   │   ├── security.py     # Password hashing, JWT
│   │   └── otp.py          # OTP management
│   ├── models/
│   │   ├── base.py         # Base model
│   │   └── user.py         # User model
│   ├── repositories/
│   │   ├── base_repository.py
│   │   └── user_repository.py
│   ├── schemas/
│   │   ├── enums.py        # Enums
│   │   ├── token.py        # Auth schemas
│   │   └── user.py         # User schemas
│   ├── services/
│   │   ├── admin_service.py
│   │   ├── auth_service.py
│   │   ├── email_service.py
│   │   └── registration_service.py
│   ├── templates/emails/   # Email templates
│   └── main.py             # App entry point
├── scripts/
│   ├── setup.py            # Complete setup
│   ├── init_db.py          # Initialize database
│   ├── check_superadmin.py # Verify superadmin
│   ├── test_cors.py        # Test CORS
│   └── test_mailmug.py     # Test SMTP
├── .env.example            # Environment template
├── requirements.txt        # Dependencies
└── README.md
```

## Development

### Useful Scripts

```bash
# Quick setup with automatic dependency installation
python scripts/quick_setup.py

# Validate setup is working correctly
python scripts/validate_setup.py

# Create default business (if missing)
python scripts/create_business.py

# Check superadmin account
python scripts/check_superadmin.py

# Reset superadmin password
python scripts/reset_superadmin_password.py

# Check database tables
python scripts/check_tables.py

# Verify unified storage
python scripts/verify_unified_storage.py

# Test SMTP configuration
python scripts/test_mailmug.py

# Test CORS
python scripts/test_cors.py

# List all routes
python scripts/list_routes.py
```

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Configuration

### SMTP Setup

#### Gmail (Recommended for Development)

1. Enable 2-Factor Authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Update .env:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=False
SMTP_USE_STARTTLS=True
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

#### Mailmug (Budget-Friendly)

```env
SMTP_HOST=smtp.mailmug.net
SMTP_PORT=587
SMTP_USE_TLS=False
SMTP_USE_STARTTLS=True
SMTP_USERNAME=your-mailmug-username
SMTP_PASSWORD=your-mailmug-password
```

### CORS Configuration

For frontend integration, update .env:

```env
# Development
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Production
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Security Best Practices

- Change default credentials immediately
- Use strong SECRET_KEY - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Enable HTTPS in production
- Restrict CORS origins to your actual domains
- Use environment variables for sensitive data
- Enable 2FA for email accounts
- Use PostgreSQL (not SQLite) in production
- Regular backups of database
- Monitor logs for suspicious activity
- Keep dependencies updated

## Deployment

### Docker

```bash
docker-compose up -d
```

### Production Checklist

- [ ] Change SECRET_KEY
- [ ] Change SUPERADMIN_PASSWORD
- [ ] Update CORS origins
- [ ] Enable HTTPS
- [ ] Use PostgreSQL
- [ ] Configure production SMTP
- [ ] Set DEBUG=False
- [ ] Setup database backups
- [ ] Configure logging
- [ ] Setup monitoring

## Architecture

### Unified User Storage

All users (SUPERADMIN, ADMIN, USER) are stored in a single `users` table, differentiated by the `role` column. This design:

- Simplifies data model
- Enables easy role changes
- Reduces code duplication
- Improves query performance

### Registration Flow

1. User submits registration (no password)
2. 6-digit OTP sent to email
3. User verifies OTP
4. Email marked as verified
5. User creates password
6. Account ready for login

## Support

For issues or questions:

- Check documentation: http://localhost:8000/docs
- Review logs in console
- Run diagnostic scripts in `/scripts`

## License

MIT License - See LICENSE file

## Contributors

Built with ❤️ by Levitica Technologies

---

## Requirements

**File: `requirements.txt`**

```txt
# ============================================================================
# Levitica HR Management System - Python Dependencies
# ============================================================================

# Web Framework
fastapi==0.115.4              # Modern, fast web framework
uvicorn[standard]==0.30.0     # ASGI server with auto-reload

# Database
sqlalchemy==2.0.36            # ORM for database operations
psycopg2-binary==2.9.9        # PostgreSQL adapter
alembic==1.13.2               # Database migrations

# Data Validation
pydantic==2.9.2               # Data validation using Python type hints
pydantic-settings==2.5.2      # Settings management

# Security & Authentication
python-jose[cryptography]==3.3.0  # JWT token handling
passlib[bcrypt]==1.7.4            # Password hashing
bcrypt==4.1.2                     # Bcrypt algorithm
cryptography==43.0.1              # Cryptographic recipes

# Email
aiosmtplib==3.0.1             # Async SMTP client
jinja2==3.1.4                 # Email template rendering

# Utilities
python-multipart==0.0.18      # Form data parsing
python-dotenv==1.0.1          # Environment variable loading
email-validator==2.1.1        # Email validation
itsdangerous==2.2.0           # Secure token generation

# ============================================================================
# Development Dependencies (install with: pip install -r requirements-dev.txt)
# ============================================================================
# pytest==7.4.3
# pytest-cov==4.1.0
# pytest-asyncio==0.21.1
# httpx==0.25.2
# black==23.12.0
# flake8==6.1.0
# mypy==1.7.1
# isort==5.13.2
```