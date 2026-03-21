# Django E-commerce

A Django-based e-commerce application with product browsing, cart management, checkout flow, user accounts, order history, wishlist support, and Razorpay payment integration.

## Features

- Product catalog and product detail pages
- Cart and order summary flow
- Checkout with address handling
- User authentication with `django-allauth`
- Wishlist support
- Order history and order detail views
- Razorpay integration
- Static file hosting with WhiteNoise
- Production-ready environment-based settings

## Tech Stack

- Python
- Django
- SQLite for local development
- PostgreSQL for production
- Gunicorn
- WhiteNoise

## Project Structure

```text
core/                    Main app logic
djecommerce/             Project config and settings
templates/               Django templates
static_in_env/           Source static assets
media_root/              Uploaded media files
requirements.txt         Python dependencies
Procfile                 Gunicorn start command
.env.example             Example production environment variables
```

## Requirements

- Python 3.10+
- `pip`
- PostgreSQL for production deployments

## Local Setup

1. Create a virtual environment.
2. Activate it.
3. Install dependencies.
4. Configure environment variables.
5. Run migrations.
6. Start the development server.

### Windows

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root for local use.

### Minimum local `.env`

```env
SECRET_KEY=change-me
DEBUG=True
RAZORPAY_TEST_KEY_ID=
RAZORPAY_TEST_KEY_SECRET=
GOOGLE_MAPS_API_KEY=
```

### Production example

See [.env.example](.env.example).

## Database

Local development uses SQLite by default.

```bash
python manage.py migrate
```

## Run Locally

```bash
python manage.py runserver
```

Default local settings:

- `DJANGO_SETTINGS_MODULE=djecommerce.settings`
- SQLite database at `db.sqlite3`
- Local development server URL: `http://127.0.0.1:8000/`

Do not use `https://127.0.0.1:8000/` with Django `runserver`. The built-in development server only supports HTTP and will show SSL/bad request errors if you open the HTTPS URL.

## Production Deployment

This project is prepared for hosting on platforms like Render, Railway, or a VPS.

### Production requirements

- Set `DJANGO_SETTINGS_MODULE=djecommerce.settings`
- Set `DEBUG=False`
- Configure `ALLOWED_HOSTS`
- Configure `CSRF_TRUSTED_ORIGINS`
- Use a PostgreSQL `DATABASE_URL`

### Required production env vars

```env
SECRET_KEY=change-me
DEBUG=False
DJANGO_SETTINGS_MODULE=djecommerce.settings
ALLOWED_HOSTS=your-app.onrender.com
CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com
DATABASE_URL=postgresql://user:password@host:5432/dbname
DB_SSL_REQUIRE=True
RAZORPAY_LIVE_KEY_ID=
RAZORPAY_LIVE_KEY_SECRET=
```

### Deploy commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Collect static files:

```bash
python manage.py collectstatic --noinput
```

Start the app:

```bash
gunicorn djecommerce.wsgi:application
```

### Render Example

- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- Start command: `gunicorn djecommerce.wsgi:application`

### PythonAnywhere

This project can also run on PythonAnywhere. The repository does not contain any proof that your PythonAnywhere account is already configured, so from this machine we can only prepare the code and deployment steps.

Recommended `.env` values for PythonAnywhere:

```env
SECRET_KEY=change-me
DEBUG=False
DJANGO_SETTINGS_MODULE=djecommerce.settings
ALLOWED_HOSTS=shreekanthch.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://shreekanthch.pythonanywhere.com
PYTHONANYWHERE_DOMAIN=shreekanthch.pythonanywhere.com
RAZORPAY_LIVE_KEY_ID=
RAZORPAY_LIVE_KEY_SECRET=
```

If you want to stay on SQLite, you can leave `DATABASE_URL` unset. If you use PostgreSQL or MySQL, set `DATABASE_URL` accordingly.

Typical PythonAnywhere setup:

1. Upload the project or clone it into `/home/yourusername/django-ecommerce-master`.
2. Create a virtualenv and install dependencies with `pip install -r requirements.txt`.
3. Add your production values to `/home/yourusername/django-ecommerce-master/.env`.
4. Run `python manage.py migrate`.
5. Run `python manage.py collectstatic --noinput`.
6. In the PythonAnywhere Web tab, point the WSGI file to this project.

Example WSGI file body:

```python
import os
import sys

path = "/home/yourusername/django-ecommerce-master"
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djecommerce.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Static files mapping in PythonAnywhere:

- URL: `/static/` -> Directory: `/home/yourusername/django-ecommerce-master/static_root`
- URL: `/media/` -> Directory: `/home/yourusername/django-ecommerce-master/media_root`

## Payments

### Razorpay

Use test keys in local development:

```env
RAZORPAY_TEST_KEY_ID=
RAZORPAY_TEST_KEY_SECRET=
```

Use live keys in production:

```env
RAZORPAY_LIVE_KEY_ID=
RAZORPAY_LIVE_KEY_SECRET=
```

## Static and Media Files

- Static files are collected into `static_root/`
- Uploaded media files are stored in `media_root/`
- WhiteNoise is used to serve static files in production

For production media hosting, consider using cloud storage instead of the local filesystem.

## Notes

- Do not use `db.sqlite3` in production
- Do not commit real secret keys
- If the included `venv/` is broken on your machine, recreate it locally

## License

This project includes the original `LICENSE` file in the repository.
