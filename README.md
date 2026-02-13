# VPN Monitor

Система мониторинга VPN-профилей для России. Автоматически проверяет доступность VPN-конфигураций из публичных репозиториев, измеряет латентность, определяет геолокацию и категоризирует профили.

## Архитектура

```
vpn-monitor/
├── backend/           # FastAPI (Python 3.12)
│   ├── app/
│   │   ├── routers/   # API endpoints
│   │   ├── services/  # Бизнес-логика (parser, xray, geo, checker, storage)
│   │   ├── config.py  # Конфигурация через env
│   │   ├── models.py  # Pydantic модели
│   │   ├── sources.py # Источники подписок
│   │   └── main.py    # Entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/          # Next.js 14 + Tailwind CSS
│   ├── src/
│   │   ├── app/       # Pages
│   │   ├── components/# UI компоненты
│   │   └── lib/       # API client, утилиты
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Порты

| Сервис | Порт |
|--------|------|
| Backend (FastAPI) | `127.0.0.1:8052` |
| Frontend (Next.js) | `127.0.0.1:3052` |

## Запуск (Docker)

```bash
docker compose up -d --build
```

## Запуск (Dev)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8052 --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Деплой

Целевой URL: `https://lmtools.ru/vpn-monitor`

```bash
# На сервере
cd /root/docker-apps/vpn-monitor
git fetch --prune origin
git reset --hard origin/main
docker compose up -d --build
```

## Nginx (lmtools.ru)

```nginx
location /vpn-monitor/ {
    proxy_pass http://127.0.0.1:3052;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /vpn-monitor/api/ {
    proxy_pass http://127.0.0.1:8052;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /vpn-monitor/_next/static/ {
    proxy_pass http://127.0.0.1:3052;
    proxy_cache_valid 200 30d;
    add_header Cache-Control "public, immutable, max-age=2592000";
}
```
