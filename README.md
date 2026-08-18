# VPN Monitor

> **Прод:** https://lmtools.ru/vpn-monitor
> **Репо:** github.com/axor91/vpn-monitor

Система мониторинга VPN-профилей для России. Автоматически проверяет доступность VPN-конфигураций из публичных подписок, измеряет латентность, определяет геолокацию и категоризирует профили по типу обхода блокировок.

---

## Что делает

- **Скачивает** 8 подписок из [igareck/vpn-configs-for-russia](https://github.com/igareck/vpn-configs-for-russia) (белые + чёрные списки)
- **Парсит** ссылки VLESS, VMess, Shadowsocks, Trojan (Reality, gRPC, WS, xHTTP, splitHTTP) + Hysteria2, TUIC
- **Тестирует** каждый конфиг через два движка — Xray-core (vless/vmess/ss/trojan) и sing-box (hysteria2/tuic, QUIC): поднимает SOCKS-прокси, проверяет connectivity через Google/Cloudflare
- **Измеряет** латентность (мс), определяет геолокацию (страна, ISP, IP) через ipwho.is с кэшированием
- **Категоризирует**: белые (CIDR/SNI для отключений мобильного) и чёрные (обычный VPN для YouTube/Discord/WhatsApp)
- **Фоновый планировщик** — автоматическая проверка каждые 6 часов (`VPN_CHECK_INTERVAL`)
- **Ручная проверка** — вставь любую vless/vmess/ss/trojan/hysteria2/tuic ссылку и проверь

> **Движки.** Парсер помечает каждый конфиг движком (`_engine`): `xray` или
> `singbox`. Xray-core 1.8.24 не поддерживает QUIC-протоколы hysteria2/tuic,
> поэтому для них в образе лежит второй бинарник — sing-box. Резолв адреса и
> пиннинг global-IP (anti-SSRF/DNS-rebinding) общий для обоих движков.

---

## Архитектура

```
vpn-monitor/
├── backend/                    # FastAPI (Python 3.12)
│   ├── app/
│   │   ├── main.py             # Entry point, lifespan, scheduler
│   │   ├── config.py           # Pydantic Settings (env-конфигурация)
│   │   ├── models.py           # Pydantic модели запросов/ответов
│   │   ├── sources.py          # 8 подписок (URL, категория, описание)
│   │   ├── routers/
│   │   │   └── monitor.py      # API endpoints (7 эндпоинтов)
│   │   └── services/
│   │       ├── parser.py       # Парсинг VLESS/VMess/SS/Trojan/Hysteria2/TUIC → outbound + движок
│   │       ├── xray.py         # Движки xray-core + sing-box, порт-менеджер
│   │       ├── netguard.py     # SSRF-guard: резолв + блок не-global IP, пиннинг
│   │       ├── geo.py          # Геолокация с in-memory TTL-кэшем
│   │       ├── checker.py      # Оркестратор параллельной проверки
│   │       ├── fetcher.py      # Загрузка и декодирование подписок
│   │       └── storage.py      # Thread-safe JSON-хранилище
│   ├── Dockerfile              # Python 3.12-slim + Xray-core 1.8.24 + sing-box 1.13.13
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # Next.js 14 + Tailwind CSS
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx      # Root layout
│   │   │   ├── page.tsx        # Главная страница (4 вкладки)
│   │   │   └── globals.css     # Tailwind + кастомные стили
│   │   ├── components/
│   │   │   ├── StatusBar.tsx   # Статус проверки + прогресс-бар
│   │   │   ├── SourceCard.tsx  # Карточка источника (раскрывающаяся)
│   │   │   ├── ConfigRow.tsx   # Строка конфига (статус, geo, копирование)
│   │   │   ├── ManualCheck.tsx # Ручная проверка ссылок
│   │   │   └── Toast.tsx       # Уведомления
│   │   └── lib/
│   │       ├── api.ts          # API-клиент + TypeScript типы
│   │       └── utils.ts        # cn(), relativeTime(), countryFlag(), latencyColor()
│   ├── next.config.js          # basePath=/vpn-monitor, standalone, rewrites
│   ├── Dockerfile              # Multi-stage: deps → build → runner (node:20-alpine)
│   ├── tailwind.config.ts
│   └── package.json
├── docker-compose.yml          # 2 сервиса, host network, healthcheck
```

---

## Backend — модули

| Модуль | Файл | Назначение |
|--------|------|------------|
| **Parser** | `services/parser.py` | Парсинг VPN-ссылок → outbound JSON + маркер движка (`_engine`). Xray: VLESS (Reality, TLS, gRPC, WS, xHTTP, TCP), VMess, Shadowsocks, Trojan. sing-box: Hysteria2, TUIC |
| **Runner** | `services/xray.py` | Диспетчер движков (xray-core / sing-box) по `_engine`: temp-конфиг, SOCKS-прокси, тест connectivity через 3 URL, замер латентности. Порт-менеджер с `socket.bind()` |
| **NetGuard** | `services/netguard.py` | SSRF-guard: резолв через `getaddrinfo`, блок не-global/multicast/reserved IP, пиннинг IP в outbound (anti-DNS-rebinding) |
| **Geo** | `services/geo.py` | Геолокация через ipwho.is API. In-memory кэш с TTL (3600с). DNS-resolve → IP → geo lookup |
| **Checker** | `services/checker.py` | Оркестратор: параллельная проверка 3 источников одновременно (`ThreadPoolExecutor`). Stop-event для остановки. Прогресс в реальном времени |
| **Fetcher** | `services/fetcher.py` | HTTP-загрузка подписок, автодетект base64, фильтрация ссылок |
| **Storage** | `services/storage.py` | Thread-safe JSON-хранилище с `threading.Lock`. Персистенция в `/app/data/vpn_data.json` |
| **Config** | `config.py` | Pydantic Settings с `VPN_` env-префиксом. Все параметры настраиваемые |

---

## API Endpoints

Все эндпоинты под `{basePath}/api/` = `/vpn-monitor/api/`

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/status` | Статус системы: is_checking, last_update, check_progress |
| `GET` | `/api/summary` | Сводка по всем источникам: alive/dead/unsupported/shutdown_ready/avg_latency |
| `GET` | `/api/results/{source_id}` | Результаты одного источника |
| `GET` | `/api/sources` | Список всех подписок |
| `POST` | `/api/test_link` | Проверить одну ссылку (body: `{"link": "vless://..."}`, rate limit: `VPN_RATE_LIMIT_TEST`/мин) |
| `GET` | `/health` | Health check (вне basePath) |

> Проверка запускается только фоновым планировщиком (каждые `VPN_CHECK_INTERVAL`
> сек). Ручных эндпоинтов запуска/остановки нет — перепроверка отдельных
> профилей идёт через `POST /api/test_link`.

---

## Источники подписок

| ID | Категория | Описание |
|----|-----------|----------|
| `BLACK_VLESS_mobile` | black | VLESS сжатая (150 шт) — обход стандартных блокировок РКН |
| `BLACK_VLESS_full` | black | VLESS полная — полный список |
| `BLACK_SS_ALL` | black | SS + Hysteria2 + VMess + Trojan — альтернативные протоколы |
| `WHITE_CIDR_all` | white | CIDR полная (все хостеры) — обход CIDR-блокировок |
| `WHITE_CIDR_checked` | white | CIDR (VK, Yandex, CDNVideo, Beeline) — проверенные |
| `WHITE_CIDR_mobile_1` | white | CIDR для телефона №1 (150 шт) |
| `WHITE_CIDR_mobile_2` | white | CIDR для телефона №2 (150 шт) |
| `WHITE_SNI` | white | SNI-подписка — обход SNI-блокировок |

---

## Конфигурация (env)

Все переменные с префиксом `VPN_`. Можно задать через `.env` или `docker-compose.yml`.

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `VPN_HOST` | `127.0.0.1` | Хост сервера |
| `VPN_PORT` | `8052` | Порт backend |
| `VPN_DEBUG` | `false` | Debug-логирование |
| `VPN_BASE_PATH` | `/vpn-monitor` | Базовый путь API |
| `VPN_XRAY_PATH` | `/app/xray/xray` | Путь к бинарнику Xray |
| `VPN_DATA_DIR` | `/app/data` | Директория данных |
| `VPN_CHECK_INTERVAL` | `21600` | Интервал автопроверки (сек, 6 ч) |
| `VPN_MAX_CONFIGS_PER_SOURCE` | `150` | Макс. конфигов на источник |
| `VPN_PARALLEL_SOURCES` | `3` | Параллельных источников |
| `VPN_INTER_TEST_DELAY` | `0.3` | Пауза между тестами (сек) |
| `VPN_XRAY_STARTUP_TIMEOUT` | `5.0` | Таймаут запуска Xray (сек) |
| `VPN_XRAY_TEST_TIMEOUT` | `8.0` | Таймаут теста connectivity (сек) |
| `VPN_PORT_BASE` | `10808` | Начальный порт SOCKS-прокси |
| `VPN_PORT_RANGE` | `200` | Диапазон портов |
| `VPN_GEO_CACHE_TTL` | `3600` | TTL geo-кэша (сек) |
| `VPN_RATE_LIMIT_TEST` | `20` | Rate limit: test_link (запросов/мин) |
| `VPN_CORS_ORIGINS` | `["http://localhost:3052","https://lmtools.ru"]` | CORS origins |

---

## Запуск

### Docker (рекомендуется)

```bash
docker compose up -d --build
```

### Dev-режим

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8052 --reload

# Frontend (в другом терминале)
cd frontend
npm install
npm run dev
```

---

## Frontend — компоненты

| Компонент | Описание |
|-----------|----------|
| **page.tsx** | Главная: 4 вкладки (Обзор, Для отключений, Обычный VPN, Ручная проверка). Polling статуса, управление проверкой |
| **StatusBar** | Индикатор статуса (idle/checking), прогресс-бар с процентами, кнопка «Стоп», счётчик живых |
| **SourceCard** | Раскрывающаяся карточка источника. Lazy-load конфигов. Фильтр: все/живые/мёртвые. Сортировка по латентности |
| **ConfigRow** | Строка конфига: статус-точка, протокол, адрес, geo (флаг + страна + ISP), латентность, кнопка копирования |
| **ManualCheck** | Textarea для вставки ссылок, последовательная проверка, результаты в реальном времени |
| **Toast** | Система уведомлений (success/error/info) с auto-dismiss 4с |

### Стек фронтенда

- **Next.js 14** — App Router, standalone output, basePath=/vpn-monitor
- **Tailwind CSS** — кастомная тёмная тема (bg-bg, accent, success, danger, warn, muted)
- **Lucide React** — иконки
- **TypeScript** — строгая типизация API-клиента

---

## Автор

Артур Абдурахманов — [github.com/axor91](https://github.com/axor91) ·
Telegram [@ar4u91](https://t.me/ar4u91). Проект спроектирован, написан и
эксплуатируется в одиночку (backend Python async + два VPN-движка, frontend
Next.js, Docker, прод за nginx); разработка AI-assisted (Claude Code + Codex)
под собственными гейтами качества.
