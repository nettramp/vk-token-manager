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