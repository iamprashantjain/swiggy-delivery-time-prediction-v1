# FROM python:3.11-slim

# # Set working directory
# WORKDIR /app

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*

# # Copy requirements
# COPY requirements_docker.txt /app/requirements.txt

# # Install Python dependencies
# RUN pip install --no-cache-dir --upgrade pip && \
#     pip install --no-cache-dir -r requirements.txt

# # Copy application
# COPY . /app/

# # Create necessary directories
# RUN mkdir -p /app/artifacts /app/models /app/static /app/templates

# # Expose port
# EXPOSE 8000

# # Start FastAPI
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]


# ===============


FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements_docker.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py /app/
COPY run_information.json /app/

# Copy project modules
COPY experiments /app/experiments/

# Copy model/preprocessor
COPY models /app/models/

# Copy frontend files
COPY static /app/static/
COPY templates /app/templates/

# Expose port
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]