# 🔑 VK Token Manager

**Безопасное получение пользовательских токенов VK ID через OAuth 2.1 + PKCE**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

VK Token Manager — удобное веб-приложение, которое помогает получить **пользовательский access_token** и **refresh_token** для VK API (стена, фото, видео, сообщества и т.д.) с использованием современного и безопасного протокола **OAuth 2.1 + PKCE**.

---

## ✨ Особенности

- ✅ **OAuth 2.1** — актуальный стандарт VK ID
- ✅ **PKCE (Proof Key for Code Exchange)** — защита от перехвата кода авторизации
- ✅ **HTTPS** + Session Management (состояние хранится 2 часа)
- ✅ Удобный веб-интерфейс
- ✅ Поддержка **Service Token** для серверных операций
- ✅ Автоматическое получение `access_token` (60 мин), `refresh_token` (180 дней) и `id_token`

---

## 🏗️ Архитектура

```ascii
┌─────────────────────┐
│   Пользователь      │
│  (Браузер + HTTPS)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│       Nginx         │
│  (SSL Termination)  │
│  порт 80 → 443      │
└──────────┬──────────┘
           │ proxy_pass
           ▼
┌─────────────────────┐
│     Gunicorn        │
│  (3 workers :5000)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     Flask App       │
│     (Python 3.12)   │
│  • generate_pkce()  │
│  • get_auth_url()   │
│  • exchange_code()  │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌────────────┐  ┌────────────┐
│ VK ID      │  │  VK API    │
│ OAuth 2.1  │  │ 5.199      │
│ id.vk.com  │  │ api.vk.com │
└────────────┘  └────────────┘

🔄 Как это работает (пошагово)
Шаг 1: Подготовка
Пользователь вводит Secret Key → приложение генерирует:

code_verifier (секретный ключ PKCE)
code_challenge (SHA-256 хеш)
device_id (уникальный UUID)
state (защита от CSRF)

Всё сохраняется в сессии Flask.
Шаг 2–5: Полный поток авторизации
asciiПользователь ──→ Ввод Secret Key ──→ /setup
                    │
                    ▼
          Генерация PKCE + state
                    │
                    ▼
          Открытие VK Авторизации
                    │
https://id.vk.com/authorize?...code_challenge=...&state=...
                    │
                    ▼
         Пользователь логинится в VK
                    │
                    ▼
https://oauth.vk.com/blank.html?code=vk2.a.xxxx...
                    │
                    ▼
Пользователь копирует code → вставляет в приложение
                    │
                    ▼
          POST /submit_code
                    │
                    ▼
   Обмен кода на токены (с code_verifier)
                    │
                    ▼
   Получение: access_token + refresh_token + user_info

📁 Структура проекта
text/var/www/vk-token-manager/
├── app.py                      # Основное Flask-приложение
├── venv/                       # Виртуальное окружение
├── templates/
│   ├── index.html              # Главная (ввод Secret Key)
│   ├── enter_code.html         # Ввод кода из VK
│   ├── authorize.html
│   ├── tokens.html             # Отображение полученных токенов
│   ├── error.html
│   └── manual_code.html
├── logs/                       # Логи
└── .gitignore

🚀 Установка на VPS (Ubuntu 22.04+ / Debian 11+)
1. Установка зависимостей
Bashsudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx
2. Развёртывание проекта
Bashsudo mkdir -p /var/www/vk-token-manager
cd /var/www/vk-token-manager
sudo python3 -m venv venv
source venv/bin/activate
pip install flask requests gunicorn

# Клонирование
git clone https://github.com/nettramp/vk-token-manager.git .
3. Настройка systemd-сервиса
Создайте файл:
Bashsudo nano /etc/systemd/system/vk-token-manager.service
Содержимое:
ini[Unit]
Description=VK Token Manager Gunicorn Instance
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/vk-token-manager
Environment="PATH=/var/www/vk-token-manager/venv/bin"
ExecStart=/var/www/vk-token-manager/venv/bin/python -m gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
Запуск:
Bashsudo systemctl daemon-reload
sudo systemctl start vk-token-manager
sudo systemctl enable vk-token-manager
4. Настройка Nginx + SSL
Подробная конфигурация (с редиректом http → https) — в оригинальном файле.
После настройки:
Bashsudo certbot --nginx -d crossposter.ru -d www.crossposter.ru

⚙️ Настройка приложения в VK ID Console

Перейдите → https://id.vk.com/business/console
Создайте приложение типа «Веб-сервис»
Укажите:
Базовый домен: crossposter.ru
Доверенный Redirect URL: https://oauth.vk.com/blank.html
Тип клиента: Конфиденциальный

Во вкладке Доступы включите: wall, photos, video, email
Скопируйте:
Client ID
Secret Key (защищённый ключ)
Service Key (сервисный ключ)



📖 Как пользоваться

Откройте https://crossposter.ru
Вставьте Secret Key и нажмите «Продолжить»
Нажмите «🔐 Открыть авторизацию VK»
Авторизуйтесь в VK (откроется новая вкладка)
Скопируйте code=vk2.a.xxxx... из адресной строки (oauth.vk.com/blank.html)
Вернитесь в приложение, вставьте код и нажмите «✅ Получить токен»

Готово! Теперь у вас есть access_token и refresh_token.

⚠️ Рекомендации по безопасности

Никому не передавайте свои токены
Всегда используйте HTTPS в продакшене
Обновляйте access_token через refresh_token
Service Key храните только на сервере
Не оставляйте приложение открытым без необходимости


📝 Лицензия
MIT License — свободное использование с указанием авторства.

👤 Автор
nettramp
GitHub: https://github.com/nettramp
Проект: https://github.com/nettramp/vk-token-manager

📞 Поддержка
При возникновении проблем:

Проверьте логи: journalctl -u vk-token-manager -f
Убедитесь, что работает HTTPS (curl -I https://ваш-домен.ru)
Создайте Issue на GitHub

Полезные ссылки:

Документация VK ID
VK API 5.199
OAuth 2.1 Spec
PKCE (RFC 7636)