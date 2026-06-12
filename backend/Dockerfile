FROM python:3.12-slim

WORKDIR /app

# Install dependencies for xray
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl unzip ca-certificates gosu \
    && rm -rf /var/lib/apt/lists/*

# Download xray-core (pinned version) — engine for vless/vmess/ss/trojan
ARG XRAY_VERSION=1.8.24
RUN curl -fsSL "https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-64.zip" -o /tmp/xray.zip \
    && mkdir -p /app/xray \
    && unzip -t /tmp/xray.zip \
    && unzip /tmp/xray.zip -d /app/xray \
    && chmod +x /app/xray/xray \
    && rm /tmp/xray.zip

# Download sing-box (pinned version) — engine for hysteria2/tuic (QUIC), which
# xray-core 1.8.24 does not support. glibc build for the debian-slim base.
ARG SINGBOX_VERSION=1.13.13
RUN curl -fsSL "https://github.com/SagerNet/sing-box/releases/download/v${SINGBOX_VERSION}/sing-box-${SINGBOX_VERSION}-linux-amd64.tar.gz" -o /tmp/singbox.tar.gz \
    && mkdir -p /app/singbox \
    && tar -xzf /tmp/singbox.tar.gz -C /app/singbox --strip-components=1 \
    && chmod +x /app/singbox/sing-box \
    && /app/singbox/sing-box version \
    && rm /tmp/singbox.tar.gz

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Non-root user
RUN groupadd --system appgroup && useradd --system --gid appgroup appuser \
    && mkdir -p /app/data && chown -R appuser:appgroup /app/data

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV VPN_XRAY_PATH=/app/xray/xray
ENV VPN_SINGBOX_PATH=/app/singbox/sing-box
ENV VPN_DATA_DIR=/app/data
ENV VPN_HOST=127.0.0.1
ENV VPN_PORT=8052

EXPOSE 8052

ENTRYPOINT ["/app/entrypoint.sh"]
