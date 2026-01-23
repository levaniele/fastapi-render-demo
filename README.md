# Badminton360 API

Official API for the Badminton360 registry and management platform. Built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

## 🚀 Features
- **FastAPI**: High performance, easy to learn, fast to code, ready for production.
- **SQLAlchemy ORM**: Full ORM support for all database interactions.
- **Alembic Migrations**: robust database schema version control.
- **Pytest**: Automated testing setup.
- **Modular Structure**: Clean separation of concerns (Routes, Services, Models, Schemas).

## 🛠️ Local Setup

### 1. Prerequisites
- Python 3.10+
- PostgreSQL installed and running
- [Optional] `uv` or `poetry` for dependency management (using standard `pip` below)

### 2. Installation
Clone the repository and install dependencies:

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# (Ensure alembic, psycopg2-binary, etc. are installed)
```

### 3. Environment Configuration
Copy the example environment file:
```powershell
Copy-Item .env.example .env
```

Edit `.env` with your local database credentials:
```ini
APP_ENV=local
DATABASE_URL=postgresql://user:password@localhost:5432/badminton
LOG_LEVEL=INFO
```

### 4. Database Setup
The project uses **Alembic** for migrations.

**Initialize Database:**
```powershell
# Apply all migrations to bring DB to latest state
alembic upgrade head
```

**Creating New Migrations:**
If you modify `app/models/`, generate a new migration:
```powershell
alembic revision --autogenerate -m "Add new feature"
```

### 5. Running the App
Start the development server with live reload:
```powershell
uvicorn app.main:app --reload
# OR via the entry script
python main.py
```
API Documentation will be available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## ✅ Testing
Run the automated test suite using `pytest`:

```powershell
# Run all tests
pytest

# Run with verbose output
# Run with verbose output
pytest -v

# Generate HTML Test Report
pytest --html=test_report.html --self-contained-html
```

## 📂 Project Structure
```
.
├── app/
│   ├── core/           # Config and security
│   ├── models/         # SQLAlchemy ORM models
│   ├── routes/         # API endpoints (Controllers)
│   ├── schemas/        # Pydantic models (Validation)
│   ├── services/       # Business logic
│   ├── database.py     # DB Session management
│   └── main.py         # App factory
├── alembic/            # Migration scripts
├── tests/              # Pytest suite
├── main.py             # Entry point script
└── alembic.ini         # Alembic config
```

## 🔧 Production (Render)
Set these environment variables in your Render dashboard:
- `APP_ENV=production`
- `DATABASE_URL=...` (Use Render's internal connection string)
- `ALLOWED_ORIGINS=https://your-frontend-domain.com`
- `LOG_LEVEL=INFO`
- `DOCS_ENABLED=false`
