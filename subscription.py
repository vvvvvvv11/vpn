import base64

VLESS_CONFIGS = [
    # 🇷🇺 LTE | Все операторы
    "vless://350396b3-913b-4de7-97c8-ba8c5764e67d@185.130.112.120:6443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=ads.x5.ru&fp=chrome&pbk=EC_gDR0zwFKeVnGhy2RD1GePSUYyDhRjxCM2wCGktTk&sid=ad7dab462a323acb&type=tcp&headerType=none#%F0%9F%87%B7%F0%9F%87%BA%20LTE%20%7C%20%D0%92%D1%81%D0%B5%20%D0%BE%D0%BF%D0%B5%D1%80%D0%B0%D1%82%D0%BE%D1%80%D1%8B",

    # 🇺🇸 США - 1
    "vless://f10f08d7-f9cc-4780-9634-a4efe3880777@ru1.casevpnserver.net:2772?encryption=none&flow=xtls-rprx-vision&security=reality&sni=pf.vk.com&fp=chrome&pbk=haERzggnSzKSAl4a05BD6Il_Nsu7f4paP9WE9O-bC2c&type=tcp&headerType=none#%F0%9F%87%BA%F0%9F%87%B8%20%D0%A1%D0%A8%D0%90%20-%201",

    # 🇷🇺 Белый Список - 1
    "vless://f10f08d7-f9cc-4780-9634-a4efe3880777@ru1.casevpnserver.net:2777?encryption=none&flow=xtls-rprx-vision&security=reality&sni=eh.vk.com&fp=chrome&pbk=haERzggnSzKSAl4a05BD6Il_Nsu7f4paP9WE9O-bC2c&type=tcp&headerType=none#%F0%9F%87%B7%F0%9F%87%BA%20%D0%91%D0%B5%D0%BB%D1%8B%D0%B9%20%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA%20-%201",

    # 🇵🇱 Польша | Instagram
    "vless://350396b3-913b-4de7-97c8-ba8c5764e67d@144.31.2.238:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=github.com&fp=chrome&pbk=EC_gDR0zwFKeVnGhy2RD1GePSUYyDhRjxCM2wCGktTk&sid=ad7dab462a323acb&type=tcp&headerType=none#%F0%9F%87%B5%F0%9F%87%B1%20%D0%9F%D0%BE%D0%BB%D1%8C%D1%88%D0%B0%20%7C%20Instagram",

    # 🇷🇺 YouTube без рекламы
    "vless://350396b3-913b-4de7-97c8-ba8c5764e67d@45.146.166.249:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=github.com&fp=chrome&pbk=EC_gDR0zwFKeVnGhy2RD1GePSUYyDhRjxCM2wCGktTk&sid=ad7dab462a323acb&type=tcp&headerType=none#%F0%9F%87%B7%F0%9F%87%BA%20YouTube%20%D0%B1%D0%B5%D0%B7%20%D1%80%D0%B5%D0%BA%D0%BB%D0%B0%D0%BC%D1%8B",
]


def get_subscription_content() -> str:
    """Возвращает base64-encoded список всех конфигов (один на строку)."""
    raw = "\n".join(VLESS_CONFIGS)
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


def get_subscription_link(base_url: str) -> str:
    return f"{base_url}/sub/{get_subscription_content()}"


def get_all_configs_text() -> str:
    """Все конфиги текстом — для отправки прямо в чате."""
    return "\n".join(VLESS_CONFIGS)
