FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg3/asyncpg and GEOS (needed for shapely/geoalchemy2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
