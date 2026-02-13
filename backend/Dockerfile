FROM python:3.12-slim

WORKDIR /app

# Install dependencies for xray
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download xray-core
ARG XRAY_VERSION=1.8.24
RUN curl -fsSL "https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-64.zip" -o /tmp/xray.zip \
    && mkdir -p /app/xray \
    && unzip /tmp/xray.zip -d /app/xray \
    && chmod +x /app/xray/xray \
    && rm /tmp/xray.zip

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Data volume
RUN mkdir -p /app/data

ENV VPN_XRAY_PATH=/app/xray/xray
ENV VPN_DATA_DIR=/app/data
ENV VPN_HOST=0.0.0.0
ENV VPN_PORT=8052

EXPOSE 8052

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8052", "--workers", "1"]
