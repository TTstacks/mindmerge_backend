# MindMerge Backend

The server-side API for **MindMerge**, built with **Django REST Framework**. Handles authentication, project management, user data, real-time communication via **Pusher**, media storage via **AWS S3**, and database/auth via **Supabase**.

## Tech Stack

- **Framework:** Django 5.1.6 + Django REST Framework 3.15.2
- **Language:** Python 100%
- **Database:** PostgreSQL via `psycopg` + Supabase
- **Auth:** JWT (`djangorestframework_simplejwt`) + Supabase GoTrue
- **Real-time:** Pusher (channels + push notifications)
- **Storage:** AWS S3 via `boto3` + `django-storages`
- **ASGI Server:** Gunicorn
- **CORS:** `django-cors-headers`

## Project Structure

```
mindmerge_backend/
├── backend/                  # Core Django project settings and URLs
├── common/
│   └── agora_utilities/      # Agora RTC/RTM token generation utilities
├── projects/                 # Projects app (models, views, serializers)
├── users/                    # Users app (auth, profiles)
├── manage.py                 # Django management entry point
└── requirements.txt          # Python dependencies
```

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL database (or Supabase project)

### Installation

```bash
git clone https://github.com/TTstacks/mindmerge_backend.git
cd mindmerge_backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the root directory with the following keys:

```env
# Django
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database / Supabase
DATABASE_URL=postgresql://user:password@host:port/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# AWS S3
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_STORAGE_BUCKET_NAME=your_bucket_name

# Pusher
PUSHER_APP_ID=your_pusher_app_id
PUSHER_KEY=your_pusher_key
PUSHER_SECRET=your_pusher_secret
PUSHER_CLUSTER=your_pusher_cluster

# Agora
AGORA_APP_ID=your_agora_app_id
AGORA_APP_CERTIFICATE=your_agora_certificate
```

### Running the Server

```bash
python manage.py migrate
python manage.py runserver
```

The API will be available at `http://localhost:8000/`.

### Running with Gunicorn (Production)

```bash
gunicorn backend.wsgi:application --bind 0.0.0.0:8000
```

## API Overview

| App        | Description                                      |
|------------|--------------------------------------------------|
| `users`    | Registration, login, JWT auth, user profiles     |
| `projects` | Project CRUD, collaboration, membership          |
| `common`   | Agora token generation for real-time audio/video |

## Key Dependencies

| Package                        | Purpose                              |
|-------------------------------|--------------------------------------|
| `djangorestframework`         | REST API                             |
| `djangorestframework_simplejwt` | JWT authentication                 |
| `supabase`                    | Database and auth client             |
| `boto3` / `django-storages`   | AWS S3 file storage                  |
| `pusher`                      | Real-time event broadcasting         |
| `pusher_push_notifications`   | Mobile push notifications            |
| `psycopg`                     | PostgreSQL driver                    |
| `django-cors-headers`         | Cross-origin request handling        |
| `pillow`                      | Image processing                     |
| `python-dotenv`               | Environment variable management      |

## Related Repositories

- **Frontend:** [MindMerge](https://github.com/TTstacks/MindMerge) — Angular + Tailwind web app

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Supabase Documentation](https://supabase.com/docs)
- [Agora Documentation](https://docs.agora.io/)
- [Pusher Documentation](https://pusher.com/docs/)
