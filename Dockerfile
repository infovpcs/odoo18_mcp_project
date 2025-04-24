FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY setup.py pyproject.toml ./
COPY README.md ./
COPY src ./src

# Install dependencies
RUN pip install --no-cache-dir .

# Copy the rest of the application
COPY main.py ./
COPY .env.example ./.env.example

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py"]