"""Subscription sources configuration."""

RAW_BASE = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main"

SUBSCRIPTION_SOURCES: dict[str, dict[str, str]] = {
    "BLACK_VLESS_mobile": {
        "url": f"{RAW_BASE}/BLACK_VLESS_RUS_mobile.txt",
        "category": "black",
        "label": "VLESS (сжатая, 150 шт)",
        "description": "Обычный VPN — обход стандартных блокировок РКН",
    },
    "BLACK_VLESS_full": {
        "url": f"{RAW_BASE}/BLACK_VLESS_RUS.txt",
        "category": "black",
        "label": "VLESS (полная)",
        "description": "Обычный VPN — полный список VLESS",
    },
    "BLACK_SS_ALL": {
        "url": f"{RAW_BASE}/BLACK_SS+All_RUS.txt",
        "category": "black",
        "label": "SS + Hysteria2 + VMess + Trojan",
        "description": "Обычный VPN — альтернативные протоколы",
    },
    "WHITE_CIDR_all": {
        "url": f"{RAW_BASE}/WHITE-CIDR-RU-all.txt",
        "category": "white",
        "label": "CIDR полная (все хостеры)",
        "description": "Для отключений мобильного — обход CIDR-блокировок по IP",
    },
    "WHITE_CIDR_checked": {
        "url": f"{RAW_BASE}/WHITE-CIDR-RU-checked.txt",
        "category": "white",
        "label": "CIDR (VK, Yandex, CDNVideo, Beeline)",
        "description": "Для отключений мобильного — проверенные хостеры",
    },
    "WHITE_CIDR_mobile_1": {
        "url": f"{RAW_BASE}/Vless-Reality-White-Lists-Rus-Mobile.txt",
        "category": "white",
        "label": "CIDR для телефона №1 (150 шт)",
        "description": "Для отключений мобильного — сжатая подписка №1",
    },
    "WHITE_CIDR_mobile_2": {
        "url": f"{RAW_BASE}/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
        "category": "white",
        "label": "CIDR для телефона №2 (150 шт)",
        "description": "Для отключений мобильного — сжатая подписка №2",
    },
    "WHITE_SNI": {
        "url": f"{RAW_BASE}/WHITE-SNI-RU-all.txt",
        "category": "white",
        "label": "SNI-подписка",
        "description": "Для отключений мобильного — обход SNI-блокировок",
    },
}
