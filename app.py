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
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

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
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.redirect_uri = REDIRECT_URI

    def get_auth_url(self, scope: str):
        state = secrets.token_hex(16)
        code_verifier, code_challenge = generate_pkce()
        device_id = generate_device_id()

        # Сохраняем в сессию как резерв (на всякий случай)
        session['pkce_code_verifier'] = code_verifier
        session['pkce_state'] = state
        session['pkce_device_id'] = device_id
        session.permanent = True

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'scope': scope,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'device_id': device_id,
        }
        return f'{VK_AUTH_URL}?{urlencode(params)}', state, code_verifier, device_id

    def exchange_code_for_token(self, code: str, device_id: str, code_verifier: str):
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'device_id': device_id,
            'code_verifier': code_verifier,
        }
        response = requests.post(VK_TOKEN_URL, data=data,
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
        return response.json()

    def get_user_info(self, access_token: str):
        response = requests.post(VK_USER_INFO_URL, data={'access_token': access_token},
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
        return response.json()

    def refresh_token(self, refresh_token: str, device_id: str):
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'device_id': device_id,
        }
        response = requests.post(VK_TOKEN_URL, data=data,
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
        return response.json()

    def get_service_token(self):
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        response = requests.post(VK_TOKEN_URL, data=data,
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
        return response.json()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/setup', methods=['POST'])
def setup():
    client_id = request.form.get('client_id', '').strip()
    client_secret = request.form.get('client_secret', '').strip()
    scope = request.form.get('scope', 'wall,photos,video,email,groups').strip()

    if not client_id:
        return render_template('error.html', error='Укажите Client ID')

    session['client_id'] = client_id
    session['client_secret'] = client_secret
    session['scope'] = scope

    manager = VKTokenManager(client_id, client_secret)
    auth_url, state, code_verifier, device_id = manager.get_auth_url(scope)

    return render_template('enter_code.html', 
                           auth_url=auth_url,
                           client_id=client_id,
                           code_verifier=code_verifier,
                           device_id=device_id)


@app.route('/submit_code', methods=['POST'])
def submit_code():
   