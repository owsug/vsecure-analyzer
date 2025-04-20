FROM python:3.12-slim

WORKDIR /app

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    && apt-get clean

# Python 패키지 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Semgrep 설치
RUN pip install --no-cache-dir semgrep

# CodeQL CLI 설치
RUN curl -L -o codeql.zip https://github.com/github/codeql-cli-binaries/releases/download/v2.16.3/codeql-linux64.zip \
    && unzip codeql.zip -d /opt \
    && mv /opt/codeql /opt/codeql-cli \
    && rm codeql.zip

ENV PATH="/opt/codeql-cli:$PATH"

RUN mkdir -p /opt/codeql-workspace && \
    cd /opt/codeql-workspace && \
    echo -e "dependencies:\n  codeql/javascript-queries: \"*\"" > codeql-pack.yml && \
    codeql pack install


ENV CODEQL_WORKSPACE="/opt/codeql-workspace"

# 앱 복사
COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
