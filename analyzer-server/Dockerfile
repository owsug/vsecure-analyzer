FROM python:3.12-slim

# Metadata
LABEL maintainer="your-email@example.com"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CODEQL_VERSION=2.16.2

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl unzip git build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip

# Install Semgrep
RUN pip install semgrep

# Download and install CodeQL CLI
RUN curl -L https://github.com/github/codeql-cli-binaries/releases/download/v${CODEQL_VERSION}/codeql-linux64.zip -o /tmp/codeql.zip && \
    unzip /tmp/codeql.zip -d /opt && \
    ln -s /opt/codeql/codeql /usr/local/bin/codeql && \
    rm /tmp/codeql.zip

# Copy project files
COPY . /app/

# Install Python dependencies (FastAPI, openai, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# Expose FastAPI port
EXPOSE 8000

# Launch the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
