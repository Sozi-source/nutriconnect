# NutriConnect API

A comprehensive healthcare platform connecting clients with verified health professionals. Built with Django REST Framework.

---

## 🚀 Live API

**Base URL:** `https://osozi.pythonanywhere.com/`

---

## ✨ Features

### For Clients
- User registration & authentication
- Search practitioners by specialty, location, rate
- View practitioner profiles and ratings
- Book consultations (clinic, home visit, telehealth)
- Leave reviews after consultations
- Appointment history and management

### For Practitioners
- Professional profile creation
- License verification system
- Set availability schedules
- Manage appointments
- Track earnings
- Respond to reviews

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Django, Django REST Framework |
| Database | SQLite / PostgreSQL |
| Authentication | Token Authentication |
| API Documentation | Swagger UI, ReDoc |
| Deployment | PythonAnywhere |

---

## 📚 API Documentation

Interactive documentation available at:
- **Swagger UI:** `https://osozi.pythonanywhere.com/swagger/`
- **ReDoc:** `https://osozi.pythonanywhere.com/redoc/`

### Authentication
All authenticated endpoints require a token in the Authorization header:
```
Authorization: Token your_token_here
```

### Core Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/register/` | POST | Register new user | No |
| `/login/` | POST | Login and get token | No |
| `/profile/` | GET | Get my profile | Yes |
| `/practitioners/` | GET | List practitioners | No |
| `/practitioners/{id}/` | GET | Practitioner details | No |
| `/specialties/` | GET | List specialties | No |
| `/consultations/` | GET | My consultations | Yes |
| `/consultations/create/` | POST | Book consultation | Yes |
| `/reviews/` | GET | List reviews | No |
| `/reviews/create/` | POST | Create review | Yes |
| `/availability/` | GET | Check availability | No |
| `/metrics/` | GET | Dashboard metrics | Yes |

---

## 💻 Local Installation

### Prerequisites
- Python 3.9+
- pip
- virtualenv (recommended)

### Setup Steps

```bash
# Clone repository
git clone https://github.com/yourusername/NutriConnect.git
cd NutriConnect

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

---

## 🔐 Environment Variables

Create a `.env` file with:
- `SECRET_KEY`
- `DEBUG`
- `DATABASE_URL`
- `ALLOWED_HOSTS`

---

## 📁 Project Structure

```
NutriConnect/
├── manage.py
├── requirements.txt
├── README.md
├── NutriConnect/          # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── NutriApp/              # Main application
    ├── models.py
    ├── views.py
    ├── serializers.py
    ├── urls.py
    ├── admin.py
    └── migrations/
```

---

## 📊 Database Models

- **User** - email, first_name, last_name
- **UserProfile** - user, role, phone
- **Practitioner** - user, currency, hourly_rate, bio, city, experience_level, is_verified
- **Specialty** - name, description
- **Availability** - practitioner, day_of_week, start_time, end_time
- **Consultation** - client, practitioner, date, time, status
- **Review** - consultation, reviewer, rating, comment

---

## 🚢 Deployment

This API is deployed on PythonAnywhere:
1. Push code to GitHub
2. Set up PythonAnywhere web app
3. Configure virtual environment
4. Set environment variables
5. Run migrations
6. Configure static files

---

## 📧 Contact

**Wilfred Osozi**  
- GitHub: [@yourusername](https://github.com/sozi-source)
- Email: your.email@example.com
- Project Link: [https://github.com/yourusername/NutriConnect](https://github.com/sozi-source/NutriConnect)

---

**Live API:** [https://osozi.pythonanywhere.com/](https://osozi.pythonanywhere.com/)  
**Documentation:** [https://osozi.pythonanywhere.com/swagger/](https://osozi.pythonanywhere.com/swagger/)

---

*Last updated: February 17, 2026*