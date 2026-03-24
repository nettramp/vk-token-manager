🔑 VK Token Manager
Получение токенов VK ID через OAuth 2.1 с PKCE





📖 Описание
VK Token Manager — это веб-приложение для безопасного получения пользовательских токенов VK ID через современный протокол OAuth 2.1 с PKCE.
Приложение решает проблему авторизации в VK API для публикации постов на стену, загрузки фото и видео, а также управления сообществами.
✨ Особенности
✅ OAuth 2.1 — современный стандарт авторизации VK ID
✅ PKCE (Proof Key for Code Exchange) — повышенная безопасность
✅ HTTPS — шифрование всех данных
✅ Session Management — хранение состояния авторизации
✅ Web Interface — удобный интерфейс для получения токенов
✅ Service Token — поддержка сервисных ключей для серверных операций
🏗️ Архитектура
┌─────────────────────────────────────────────────────────────────────┐
│                           Пользователь                               │
│                         (Браузер HTTPS)                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                              Nginx                                   │
│                    (Порт 80/443, SSL Termination)                    │
│              /etc/nginx/sites-available/vk-token-manager             │
└────────────────────────────┬────────────────────────────────────────┘
                             │ proxy_pass :5000
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           Gunicorn                                   │
│                  (WSGI Server, 3 workers, :5000)                     │
│              /etc/systemd/system/vk-token-manager.service            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Flask App                                   │
│                      (app.py, Python 3.12)                           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  VKTokenManager                                             │    │
│  │  - generate_pkce()      # Код верификации PKCE              │    │
│  │  - generate_device_id() # Уникальный ID устройства          │    │
│  │  - get_auth_url()       # URL авторизации VK                │    │
│  │  - exchange_code_for_token() # Обмен кода на токен          │    │
│  │  - get_user_info()      # Информация о пользователе         │    │
│  └─────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│     VK ID OAuth 2.1     │     │    VK API 5.199         │
│  id.vk.com/authorize    │     │  api.vk.com/method      │
│  id.vk.com/oauth2/auth  │     │  (wall.post, etc.)      │
└─────────────────────────┘     └─────────────────────────┘

🔄 Как это работает
Шаг 1: Инициализация авторизации
Пользователь → Вводит Secret Key → /setup
     ↓
Приложение генерирует:
  - code_verifier (PKCE)
  - code_challenge (SHA256 хеш)
  - device_id (UUID)
  - state (защита от CSRF)
     ↓
Сохранение в Flask Session (2 часа)

Шаг 2: Перенаправление на VK
Приложение → Генерирует URL авторизации
     ↓
https://id.vk.com/authorize?
  client_id=54499818&
  redirect_uri=https://oauth.vk.com/blank.html&
  scope=wall,photos,video,email&
  code_challenge=...&
  code_challenge_method=S256&
  device_id=...&
  state=...
     ↓
Пользователь авторизуется на VK

Шаг 3: Получение кода

VK → Перенаправляет на oauth.vk.com/blank.html
     ↓
URL: https://oauth.vk.com/blank.html?
  code=vk2.a.xxx...&
  device_id=...&
  state=...
     ↓
Пользователь копирует code= из адресной строки

Шаг 4: Обмен кода на токен

Пользователь → Вставляет code → /submit_code
     ↓
Приложение отправляет POST запрос:
  https://id.vk.com/oauth2/auth
  {
    grant_type: authorization_code,
    code: vk2.a.xxx...,
    client_id: 54499818,
    client_secret: ***,
    redirect_uri: https://oauth.vk.com/blank.html,
    device_id: ...,
    code_verifier: ...  # PKCE верификация
  }
     ↓
VK возвращает:
  - access_token (60 минут)
  - refresh_token (180 дней)
  - id_token (JWT)
  - user_info

  Шаг 5: Использование токена

  access_token → VK API вызовы:
  - wall.post (публикация на стену)
  - photos.getWallUploadServer (загрузка фото)
  - video.save (загрузка видео)
  - users.get (информация о пользователе)


  📁 Структура проекта

  /var/www/vk-token-manager/
├── app.py                          # Основное Flask приложение
├── venv/                           # Python виртуальное окружение
├── .gitignore                      # Git исключения
├── templates/
│   ├── index.html                  # Главная страница (ввод Secret Key)
│   ├── enter_code.html             # Страница ввода кода авторизации
│   ├── authorize.html              # Страница перенаправления на VK
│   ├── tokens.html                 # Страница отображения токенов
│   ├── error.html                  # Страница ошибок
│   └── manual_code.html            # Резервная страница ввода кода
└── logs/                           # Логи приложения


Установка на VPS
Требования
Ubuntu 22.04+ / Debian 11+
Python 3.12+
Nginx
SSL сертификат (Let's Encrypt)
Домен с HTTPS
1. Установка зависимостей

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и Nginx
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx

# Создание директории
sudo mkdir -p /var/www/vk-token-manager
cd /var/www/vk-token-manager

# Виртуальное окружение
sudo python3 -m venv venv
source venv/bin/activate

# Установка зависимостей Python
pip install flask requests gunicorn

2. Клонирование проекта
# Клонирование из GitHub
git clone https://github.com/nettramp/vk-token-manager.git .

# Или скопируйте файлы вручную

3. Настройка systemd сервиса
sudo nano /etc/systemd/system/vk-token-manager.service

[Unit]
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
# Запуск сервиса
sudo systemctl daemon-reload
sudo systemctl start vk-token-manager
sudo systemctl enable vk-token-manager

4. Настройка Nginx
sudo nano /etc/nginx/sites-available/vk-token-manager

server {
    listen 80;
    server_name crossposter.ru www.crossposter.ru;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name crossposter.ru www.crossposter.ru;

    ssl_certificate /etc/letsencrypt/live/crossposter.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/crossposter.ru/privkey.pem;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Cookie $http_cookie;
    }

    access_log /var/log/nginx/vk-token-manager-access.log;
    error_log /var/log/nginx/vk-token-manager-error.log;
}

# Активация сайта
sudo ln -s /etc/nginx/sites-available/vk-token-manager /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# SSL сертификат
sudo certbot --nginx -d crossposter.ru -d www.crossposter.ru

⚙️ Настройка VK ID Console
1. Создание приложения
Перейдите на https://id.vk.com/business/console
Нажмите "+ Создать приложение"
Тип: Веб-сервис
Заполните паспортные данные (требуется для расширенных прав)
2. Настройка OAuth
Параметр
Значение
Базовый домен
crossposter.ru
Доверенный Redirect URL
https://oauth.vk.com/blank.html
Тип клиента
Конфиденциальный
Grant Type
Authorization Code
3. Настройка доступов
Во вкладке "Доступы" включите:
✅ Стена (wall)
✅ Фотографии (photos)
✅ Видео (video)
✅ Email
✅ Базовая информация
4. Получение ключей
Ключ
Где найти
Client ID
Главная страница приложения
Secret Key
Вкладка "Приложение" → "Защищённый ключ"
Service Key
Вкладка "Приложение" → "Сервисный ключ доступа"
📖 Использование
1. Запуск приложения
# Откройте в браузере
https://crossposter.ru
2. Ввод данных
Введите Secret Key из VK ID Console
Нажмите "Продолжить"
3. Авторизация
Нажмите "🔐 Открыть авторизацию VK" (откроется в новой вкладке)
Авторизуйтесь через VK
VK перенаправит на oauth.vk.com/blank.html?code=...
Скопируйте код из адресной строки (значение после code=)
4. Получение токена
Вернитесь на первую вкладку (НЕ закрывайте!)
Вставьте код в поле
Нажмите "✅ Получить токен"
Скопируйте токены для использования

Рекомендации
⚠️ Не передавайте токены третьим лицам
⚠️ Используйте HTTPS в production
⚠️ Обновляйте токен через refresh_token до истечения
⚠️ Храните Service Key только на сервере

📝 Лицензия
MIT License — свободное использование с указанием авторства.
👤 Автор
nettramp
GitHub: https://github.com/nettramp
Проект: https://github.com/nettramp/vk-token-manager
📞 Поддержка
Если возникли проблемы:
Проверьте логи (journalctl -u vk-token-manager -f)
Проверьте настройки VK Console
Убедитесь что HTTPS работает (curl -I https://ваш_домен.ru)
Создайте Issue на GitHub
🔗 Полезные ссылки
VK ID Документация
VK API Документация
OAuth 2.1 Spec
PKCE RFC 7636