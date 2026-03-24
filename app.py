from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import requests
import secrets
import os
import hashlib
import base64
import uuid
from urllib.parse import urlencode
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_SECURE'] = False          # ← ИСПРАВЛЕНО для локального запуска
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'        # более лояльно для dev

VK_AUTH_URL = 'https://id.vk.com/authorize'
VK_TOKEN_URL = 'https://id.vk.com/oauth2/auth'
VK_USER_INFO_URL = 'https://id.vk.com/oauth2/user_info'
REDIRECT_URI = 'https://oauth.vk.com/blank.html'


def generate_pkce():
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    return code_verifier, code_challenge


def generate_device_id():
    return uuid.uuid4().hex


class VKTokenManager:
    # ... (методы get_auth_url, exchange_code_for_token, get_user_info, refresh_token, get_service_token — без изменений)

    def exchange_code_for_token(self, code: str, device_id: str):
        code_verifier = session.get('pkce_code_verifier')
        if not code_verifier:
            return {'error': 'Сессия истекла. Начните заново.'}

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'device_id': device_id,               # теперь берём из формы (или сессии)
            'code_verifier': code_verifier,
        }
        response = requests.post(VK_TOKEN_URL, data=data,
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
        return response.json()

# ... (все остальные маршруты без изменений, кроме /submit_code ниже)


@app.route('/submit_code', methods=['POST'])
def submit_code():
    code = request.form.get('code', '').strip()
    device_id = request.form.get('device_id', '').strip() or session.get('pkce_device_id')

    if not code or not device_id:
        return render_template('error.html', error='Не указан code или device_id')

    client_id = session.get('client_id')
    if not client_id:
        return redirect(url_for('index'))

    manager = VKTokenManager(client_id, session.get('client_secret', ''))

    token_data = manager.exchange_code_for_token(code, device_id)

    if 'access_token' in token_data:
        user_info = manager.get_user_info(token_data['access_token'])
        return render_template('tokens.html',
                               token_data=token_data,
                               user_info=user_info,
                               client_secret=session.get('client_secret', ''))
    else:
        error_msg = token_data.get('error_description') or token_data.get('error') or 'Неизвестная ошибка'
        app.logger.error(f"VK error: {token_data}")
        return render_template('error.html', error=error_msg)