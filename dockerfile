FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy pyproject.toml first (poetry.lock is optional)
COPY pyproject.toml ./
# Check if poetry.lock exists and copy it if it does
COPY poetry.lock* ./

# Install dependencies without installing the root project
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

# Copy the application code
COPY . .

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
