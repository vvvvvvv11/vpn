import os

# ── Тарифы ───────────────────────────────────────────────────────────────
PLANS = {
    "1m": {"label": "1 месяц",  "price": 199,  "days": 30},
    "3m": {"label": "3 месяца", "price": 499,  "days": 90},
    "1y": {"label": "1 год",    "price": 1490, "days": 365},
}

# ── Реквизиты для оплаты скриншотом ──────────────────────────────────────
# Меняй здесь — изменится во всём боте автоматически
PAYMENT_CARD    = os.getenv("PAYMENT_CARD",    "2200 7021 3346 1595")  # номер карты
PAYMENT_BANK    = os.getenv("PAYMENT_BANK",    "Т-Банк")             # банк
PAYMENT_NAME    = os.getenv("PAYMENT_NAME",    "Владислав С.")              # имя получателя
PAYMENT_SBP     = os.getenv("PAYMENT_SBP",     "-")     # СБП (если есть)

# ── VPN конфиг ────────────────────────────────────────────────────────────
VPN_CONFIG = (
    "vless://350396b3-913b-4de7-97c8-ba8c5764e67d@185.130.112.120:6443"
    "?encryption=none"
    "&flow=xtls-rprx-vision"
    "&security=reality"
    "&sni=ads.x5.ru"
    "&fp=chrome"
    "&pbk=EC_gDR0zwFKeVnGhy2RD1GePSUYyDhRjxCM2wCGktTk"
    "&sid=ad7dab462a323acb"
    "&type=tcp"
    "&headerType=none"
    "#RU-LTE-AllOperators"
)

# ── Туториал iOS ──────────────────────────────────────────────────────────
TUTORIAL_IOS = """
📱 <b>Установка VPN на iPhone (Happ)</b>

1️⃣ Скачай <b>Happ</b> из App Store
   👉 https://apps.apple.com/app/happ-proxy-utility/id6504287215

2️⃣ Открой приложение → нажми <b>«+»</b> в правом верхнем углу

3️⃣ Выбери <b>«Import from clipboard»</b>

4️⃣ Вставь конфиг, который я отправил выше 👆

5️⃣ Нажми <b>Connect</b> — готово! ✅

━━━━━━━━━━━━━━━━━━━━
❓ Поддержка: @{support}
"""

# ── Туториал Android ──────────────────────────────────────────────────────
TUTORIAL_ANDROID = """
📱 <b>Установка VPN на Android (v2rayNG)</b>

1️⃣ Скачай <b>v2rayNG</b> из Google Play
   👉 https://play.google.com/store/apps/details?id=com.v2ray.ang

2️⃣ Открой приложение → нажми <b>«+»</b> в правом верхнем углу

3️⃣ Выбери <b>«Import config from clipboard»</b>

4️⃣ Вставь конфиг, который я отправил выше 👆

5️⃣ Нажми на строку с конфигом → нажми ▶️ внизу — готово! ✅

━━━━━━━━━━━━━━━━━━━━
❓ Поддержка: @{support}
"""

# ── Туториал подписки iOS ─────────────────────────────────────────────────
TUTORIAL_SUBSCRIPTION_IOS = """
📱 <b>Установка всех серверов на iPhone (Happ)</b>

1️⃣ Скачай <b>Happ</b> из App Store
   👉 https://apps.apple.com/app/happ-proxy-utility/id6504287215

2️⃣ Скопируй ссылку-подписку выше 👆

3️⃣ Открой Happ → нажми <b>«+»</b> → выбери <b>«Import from URL»</b>

4️⃣ Вставь ссылку → нажми <b>Import</b>

5️⃣ Все серверы добавятся автоматически! ✅

━━━━━━━━━━━━━━━━━━━━
❓ Поддержка: @{support}
"""

# ── Туториал подписки Android ─────────────────────────────────────────────
TUTORIAL_SUBSCRIPTION_ANDROID = """
📱 <b>Установка всех серверов на Android (v2rayNG)</b>

1️⃣ Скачай <b>v2rayNG</b> из Google Play
   👉 https://play.google.com/store/apps/details?id=com.v2ray.ang

2️⃣ Открой приложение → нажми <b>☰</b> → <b>«Subscription settings»</b>

3️⃣ Нажми <b>«+»</b> → вставь ссылку-подписку 👆 → сохрани

4️⃣ Вернись → нажми <b>☰</b> → <b>«Update subscription»</b>

5️⃣ Все серверы появятся в списке! ✅

━━━━━━━━━━━━━━━━━━━━
❓ Поддержка: @{support}
"""

# ── Обратная совместимость ────────────────────────────────────────────────
TUTORIAL_TEXT             = TUTORIAL_IOS
TUTORIAL_SUBSCRIPTION_TEXT = TUTORIAL_SUBSCRIPTION_IOS

# ── ENV ───────────────────────────────────────────────────────────────────
SUPPORT_USERNAME      = os.getenv("SUPPORT_USERNAME",     "vladossqqqq")
YOOMONEY_WALLET       = os.getenv("YOOMONEY_WALLET",      "4100119441681698")
BOT_USERNAME          = os.getenv("BOT_USERNAME",         "your_bot")
SUBSCRIPTION_BASE_URL = os.getenv("SUBSCRIPTION_BASE_URL", "")
ADMIN_ID              = os.getenv("ADMIN_ID",             "7984183942")
