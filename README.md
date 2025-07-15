# Dietly Backend

### 1. Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)
- PostgreSQL instance

### 2. Environment Variables

Create a `.env` file in the project root. Example:

```
# Database
DATABASE_URL=postgresql+psycopg2://<username>:<password>@<host>:5432/<dbname>

# Security
SECRET_KEY=your_secret_key

# Frontend
FRONTEND_URL=http://localhost:3000

# Email (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_email_password
FROM_EMAIL=your_email@gmail.com

# AWS S3
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=ap-south-1
AWS_S3_BUCKET_NAME=your-s3-bucket-name
DEFAULT_AVATAR_URL=https://your-bucket.s3.amazonaws.com/default-avatar.png

# File Upload
UPLOAD_DIR=uploads

# Rate Limiting (optional)
PASSWORD_RESET_RATE_LIMIT=3
LOGIN_RATE_LIMIT=5

# Google OAuth2
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# OpenAI / Gemini
GEMINI_API_KEY=your_gemini_api_key

# Environment
ENVIRONMENT=development
```

- Adjust values as needed for your deployment.
- All variables above are referenced in the codebase (see `app/core/config.py`).

### 2a. Alembic Migrations and `migrations/env.py`

The file `migrations/env.py` is the main configuration script for Alembic database migrations. It:

- Loads your app's SQLAlchemy models and metadata for schema generation.
- Reads the database connection URL from your environment (typically from the `DATABASE_URL` variable in your `.env` file).
- Controls how migrations are run, both in offline and online mode.

**How it works:**

- When you run `alembic upgrade head` (see below), Alembic uses `migrations/env.py` to connect to your database and apply migrations.
- Make sure your `.env` file is set up and the `DATABASE_URL` is correct before running migrations.

**Important: Registering Models for Autogeneration**

To ensure Alembic is aware of all your models for schema autogeneration, make sure you have the following lines in your `migrations/env.py`:

```python
from app.core.database import Base
from app.models import user, image, password_reset, email_verfication, pending_registration, user_calories

target_metadata = Base.metadata
```

- This imports your SQLAlchemy `Base` and all model modules, so Alembic can detect all tables and relationships.
- Setting `target_metadata = Base.metadata` tells Alembic which metadata to use for autogenerating migration scripts.
- Without these imports, Alembic may not detect changes to your models, and `alembic revision --autogenerate -m "..."` may miss tables or columns.

For more details, see the comments in `migrations/env.py`.

### 3. Build and Run the App

```
docker-compose up --build
```

- The API will be available at: [http://localhost:8000](http://localhost:8000)

### 4. Check the App in Your Browser

- Root endpoint: [http://localhost:8000](http://localhost:8000)
- Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Run Database Migrations

To apply Alembic migrations to your database:

```
docker-compose exec app alembic upgrade head
```

### 6. Stopping the App

```
docker-compose down
```

---
