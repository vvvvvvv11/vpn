# 🔒 VPN Telegram Bot

Бот для продажи VPN-доступа через ЮMoney с реферальной системой.

## 📦 Установка

```bash
# 1. Клонируйте / скопируйте файлы на сервер
cd vpn_bot

# 2. Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Настройте переменные окружения
cp .env.example .env
nano .env   # заполните все значения
```

## ⚙️ Настройка .env

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен от @BotFather |
| `BOT_USERNAME` | Username бота без @ |
| `SUPPORT_USERNAME` | Username поддержки без @ |
| `YOOMONEY_WALLET` | Номер кошелька ЮMoney |
| `YOOMONEY_TOKEN` | API-токен ЮMoney |

### Как получить YOOMONEY_TOKEN:
1. Зайдите на https://yoomoney.ru/transfer/myservices/http-notification
2. Выберите права: `operation-history`
3. Скопируйте токен в `.env`

## 🚀 Запуск

```bash
python bot.py
```

### Запуск через systemd (для сервера):
```ini
[Unit]
Description=VPN Telegram Bot
After=network.target

[Service]
WorkingDirectory=/path/to/vpn_bot
ExecStart=/path/to/vpn_bot/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 💰 Тарифы (изменить в config.py)

| Ключ | Название | Цена | Дней |
|---|---|---|---|
| `1m` | 1 месяц | 199₽ | 30 |
| `3m` | 3 месяца | 499₽ | 90 |
| `1y` | 1 год | 1490₽ | 365 |

## 👥 Реферальная система

- Пользователь получает ссылку вида `t.me/bot?start=USER_ID`
- За каждого оплатившего друга — уведомление в боте
- Бонусный месяц выдаётся вручную через поддержку (или можно автоматизировать)

## 📁 Структура файлов

```
vpn_bot/
├── bot.py          # Точка входа
├── handlers.py     # Все обработчики команд и кнопок
├── database.py     # SQLite база данных
├── yoomoney.py     # Проверка платежей ЮMoney
├── config.py       # Конфиг, тарифы, VPN-конфиг, туториал
├── .env            # Ваши секретные данные (не коммитить!)
└── requirements.txt
```
