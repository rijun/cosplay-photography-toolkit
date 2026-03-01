# Cosplay Photography Toolkit

A self-hosted photo gallery and proofing tool for photographers. Clients receive a secret URL to view their gallery, select favorites, and leave comments. The photographer manages everything via CLI.

## Features

- **CLI-driven workflow** — Create galleries, upload photos, export selections
- **Client proofing** — Secret URL access, no login required
- **Photo selection** — Clients mark favorites with a single click
- **Comments** — Clients leave feedback on individual photos
- **S3-compatible storage** — Works with Cloudflare R2, AWS S3, MinIO, etc.
- **Django Admin** — Web-based management interface

## Stack

| Component | Technology                                 |
|-----------|--------------------------------------------|
| Web       | Django 6, Django REST Framework, Alpine.js |
| CLI       | Click, httpx, boto3                        |
| Database  | PostgreSQL                                 |
| Storage   | S3-compatible                              |

## Installation

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/rijun/cosplay-photography-toolkit.git
cd cosplay-photography-toolkit

# Install CLI (photographer's machine)
uv sync --group cli

# Install web app (server)
uv sync --group web
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Database
DB_NAME=gallerydb
DB_USER=gallery
DB_PASSWORD=secret
DB_HOST=localhost
DB_PORT=5432

# Object Storage (S3-compatible)
OBJECT_STORAGE_ENDPOINT_URL=https://your-object-storage-provider
OBJECT_STORAGE_ACCESS_KEY_ID=your-access-key
OBJECT_STORAGE_SECRET_ACCESS_KEY=your-secret-key
OBJECT_STORAGE_BUCKET_NAME=photos

# API
API_KEY=your-api-key
```

## Usage

### CLI Commands

```bash
# Create a gallery
photo gallery create "Client Name 2024"

# Upload photos (strips metadata, uploads to S3, registers with server)
photo upload ./photos --gallery client-name-2024

# List galleries
photo gallery list

# Export client selections (for Lightroom filtering)
photo export client-name-2024

# Archive a gallery
photo gallery archive client-name-2024
```

### Client Access

Clients receive a secret URL:
```
https://yourdomain.com/g/{token}
```

No login required — the token provides access.

## Development

```bash
# Run migrations
cd web && python manage.py migrate

# Start dev server
python manage.py runserver

# Create admin user
python manage.py createsuperuser
```

## Deployment

The web app runs behind a reverse proxy with gunicorn:

```bash
# Install dependencies
uv sync --group web

# Run migrations and collect static files
python manage.py migrate
python manage.py collectstatic

# Start with gunicorn
gunicorn --bind 0.0.0.0:8000 config.wsgi:application
```

## License

See [LICENSE.md](LICENSE.md)
