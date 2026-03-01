# NutriConnect API

A healthcare platform connecting clients with verified nutritionists, dietitians, and physiotherapists. Built with Django REST Framework.

---

## 🚀 Live API

**Base URL:** `https://osozi.pythonanywhere.com/`

---

## 📚 API Endpoints

### Root & Info
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API root with navigation links |
| `/health/` | GET | Health check |

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register/` | POST | Create new account |
| `/login/` | POST | Login and get token |
| `/logout/` | POST | Logout and invalidate token |
| `/profile/` | GET | Get current user profile |

### Specialties
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/specialties/` | GET | List all specialties |

### Practitioners
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/practitioners/` | GET | List verified practitioners |
| `/practitioners/{id}/` | GET | Practitioner details |
| `/practitioners/me/` | GET | My practitioner profile |
| `/practitioners/{id}/verify/` | PATCH | Verify practitioner (admin) |
| `/practitioners/{id}/availability/` | GET | Public availability |
| `/practitioners/{id}/reviews/` | GET | Practitioner reviews |

### Practitioner Applications
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/practitioners/application/create/` | POST | Create application |
| `/practitioners/application/me/` | GET | View my application |
| `/practitioners/application/submit/` | POST | Submit for review |
| `/practitioners/application/status/` | GET | Check status |

### Availability
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/availability/` | GET/POST | List/create availability |
| `/availability/{id}/` | GET/PUT/DELETE | Manage availability slot |

### Consultations
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/consultations/` | GET/POST | List/create consultations |
| `/consultations/{id}/` | GET | Consultation details |
| `/consultations/{id}/status/` | PATCH | Update status |
| `/consultations/my-client/` | GET | Client's consultations |
| `/consultations/my-practitioner/` | GET | Practitioner's consultations |
| `/consultations/completed/no-review/` | GET | Completed w/out review |
| `/consultations/metrics/` | GET | Dashboard metrics |

### Reviews
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reviews/create/` | POST | Write a review |
| `/reviews/my-reviews/` | GET | My reviews |

### Notifications
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/` | GET | List notifications |
| `/notifications/{id}/` | GET | Notification details |
| `/notifications/{id}/read/` | POST | Mark as read |
| `/notifications/mark-all-read/` | POST | Mark all as read |
| `/notifications/unread-count/` | GET | Unread count |

### Admin
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/practitioners/pending/` | GET | Pending verifications |
| `/admin/practitioners/{id}/approve/` | PATCH | Approve practitioner |
| `/admin/practitioners/{id}/reject/` | POST | Reject practitioner |
| `/admin/applications/` | GET | List applications |
| `/admin/applications/{id}/` | GET | Application details |
| `/admin/applications/{id}/action/` | POST | Approve/reject application |

---

## 🔐 Authentication

Include token in Authorization header:
```
Authorization: Token your_token_here
```

---

## 🛠 Tech Stack

- **Backend:** Django, Django REST Framework
- **Database:** SQLite / PostgreSQL
- **Auth:** Token Authentication
- **Hosting:** PythonAnywhere

---

## 💻 Local Setup

```bash
# Clone repo
git clone https://github.com/sozi-source/NutriConnect.git
cd NutriConnect

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Migrate and run
python manage.py migrate
python manage.py runserver
```

---

## 👨‍💻 Author

**Wilfred Osozi**
- GitHub: [@sozi-source](https://github.com/sozi-source)
- Project: [NutriConnect](https://github.com/sozi-source/NutriConnect)

---

**Live API:** [https://osozi.pythonanywhere.com/](https://osozi.pythonanywhere.com/)

---

*Last updated: March 2026*