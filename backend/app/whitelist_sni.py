"""SNI domains known to remain accessible during mobile internet shutdowns in Russia."""

WHITELIST_SNI: set[str] = {
    # Соцсети / мессенджеры
    "vk.com", "ok.ru", "mail.ru", "my.mail.ru",
    # Госуслуги
    "gosuslugi.ru", "esia.gosuslugi.ru",
    # Яндекс
    "yandex.ru", "ya.ru", "yandex.net", "kinopoisk.ru", "dzen.ru",
    # Видео / кино
    "rutube.ru", "okko.tv", "ivi.ru",
    # Маркетплейсы
    "ozon.ru", "wildberries.ru", "avito.ru", "megamarket.ru",
    # Транспорт
    "rzd.ru", "tutu.ru", "aeroflot.ru", "pobeda.aero",
    # Банки / финансы
    "vtb.ru", "psbank.ru", "cbr.ru", "moex.com",
    # Ритейл / доставка
    "x5.ru", "vkusvill.ru", "cdek.ru", "samokat.ru",
    "obi.ru", "perekrestok.ru", "pyaterochka.ru",
    # Операторы связи
    "beeline.ru", "megafon.ru", "mts.ru", "tele2.ru",
    # Работа / недвижимость
    "hh.ru", "domclick.ru",
    # Навигация / погода
    "2gis.ru", "gismeteo.ru",
    # СМИ
    "rbc.ru", "ria.ru", "lenta.ru", "gazeta.ru", "tass.ru",
    "rambler.ru", "iz.ru", "kp.ru", "1tv.ru", "ntv.ru", "rt.com",
    "rg.ru", "mk.ru", "vedomosti.ru", "kommersant.ru",
}


def is_whitelist_sni(sni: str) -> bool:
    """Check if a given SNI domain matches the shutdown whitelist."""
    if not sni:
        return False
    sni = sni.lower().strip()
    if sni in WHITELIST_SNI:
        return True
    # Check if it's a subdomain of a whitelisted domain
    for domain in WHITELIST_SNI:
        if sni.endswith("." + domain):
            return True
    return False
