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

# # Copy application files
# COPY app.py /app/
# COPY run_information.json /app/

# # Copy project modules
# COPY experiments/data_clean_utils.py /app/experiments/data_clean_utils.py

# # Copy model/preprocessor
# COPY models /app/models/

# # Copy frontend files
# COPY static /app/static/
# COPY templates /app/templates/

# # Expose port
# EXPOSE 8000

# # Start FastAPI
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]


# ================================================

# Use slim-buster for better compatibility than alpine
FROM python:3.11-slim-buster

# Set working directory
WORKDIR /app

# Install system dependencies (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (for better caching)
COPY requirements_docker.txt /app/requirements.txt

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py /app/
COPY run_information.json /app/

# Create experiments directory and copy module
RUN mkdir -p /app/experiments
COPY experiments/data_clean_utils.py /app/experiments/data_clean_utils.py

# Copy models directory
COPY models /app/models/

# Copy frontend files
COPY static /app/static/
COPY templates /app/templates/


# Expose port
EXPOSE 8000

# Start FastAPI with optimized settings
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]