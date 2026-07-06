# Product Customization System — Setup Guide

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16 (or use SQLite for dev)
- Redis 7 (optional for dev, required for Celery)

## Quick Start (Development)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed sample data
python manage.py seed_data

# Start development server
python manage.py runserver
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Django Admin**: http://localhost:8000/admin/
- **API Docs (Swagger)**: http://localhost:8000/api/docs/
- **API Docs (ReDoc)**: http://localhost:8000/api/redoc/

### 4. Optional: Start Celery Worker

```bash
cd backend
celery -A config worker -l info
```

### 5. Optional: Start Celery Beat

```bash
cd backend
celery -A config beat -l info
```

## Docker Deployment

```bash
# From project root
docker-compose up --build

# Access at http://localhost
```

## Environment Variables

See `backend/config/.env.example` for all backend variables.
See `frontend/.env.local` for frontend variables.

## Running Tests

```bash
# Backend
cd backend
python manage.py test

# Frontend
cd frontend
npm test
```
