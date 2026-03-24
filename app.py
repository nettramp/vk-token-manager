from flask import Flask, render_template, request, session, jsonify
import requests
import secrets
import os
import hashlib
import base64
import uuid
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

VK_CONFIG = {
    'client_id': '54499818',
    'client_secret': '',
    'redirect_uri': 'https://oauth.vk.com/blank.html',
    'auth_url': 'https://id.vk.com/authorize',
    'token_url': 'https://id.vk.com/oauth2/auth',
    'user_info_url': 'https://id.vk.com/oauth2/user_info',
}

def generate_pkce():
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    return code_verifier, code_challenge

def generate_device_id():
    return uuid.uuid4().hex

class VKTokenManager:
    def __init__(self, client_id, client_secret):
        self.client_id = str(client_id).strip()
        self.client_secret = str(client_secret).strip()
        self.redirect_uri = 'https://oauth.vk.com/blank.html'
        self.auth_url = VK_CONFIG['auth_url']
        self.token_url = VK_CONFIG['token_url']
        self.user_info_url = VK_CONFIG['user_info_url']
    
    def get_auth_url(self, scope='wall,photos,video,email'):
        state = secrets.token_hex(16)
        code_verifier, code_challenge = generate_pkce()
        device_id = generate_device_id()
        
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
        
        query = urlencode(params)
        return f'{self.auth_url}?{query}', state
    
    def exchange_code_for_token(self, code, device_id):
        code_verifier = session.get('pkce_code_verifier')
        
        if not code_verifier:
            return {'error': 'Session expired. Please start over.'}
        
        response = requests.post(self.token_url, data={
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'device_id': device_id,
            'code_verifier': code_verifier,
        }, headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        
        return response.json()
    
    def get_user_info(self, access_token):
        response = requests.get(self.user_info_url, params={
            'access_token': access_token,
        })
        return response.json()
    
    def get_service_token(self):
        response = requests.post(self.token_url, data={
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }, headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        return response.json()

vk_manager = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/setup', methods=['POST'])
def setup():
    global vk_manager
    
    VK_CONFIG['client_id'] = request.form.get('client_id', '').strip()
    VK_CONFIG['client_secret'] = request.form.get('client_secret', '').strip()
    
    vk_manager = VKTokenManager(
        VK_CONFIG['client_id'],
        VK_CONFIG['client_secret']
    )
    
    auth_url, state = vk_manager.get_auth_url(scope='wall,photos,video,email')
    
    app.logger.info(f"DEBUG: Auth URL = {auth_url}")
    
    return render_template('enter_code.html', auth_url=auth_url)

@app.route('/submit_code', methods=['POST'])
def submit_code():
    global vk_manager
    
    code = request.form.get('code', '').strip()
    device_id = session.get('pkce_device_id')
    
    if not code:
        return render_template('error.html', error='Code not provided')
    
    if not device_id:
        return render_template('error.html', error='Session expired. Please start over.')
    
    token_data = vk_manager.exchange_code_for_token(code, device_id)
    
    if 'access_token' in token_data_:
        user_info = vk_manager.get_user_info(token_data['access_token'])
        return render_template('tokens.html', 
                             token_data=token_data,
                             user_info=user_info,
                             config=VK_CONFIG)
    else:
        app.logger.error(f"Token error: {token_data}")
        return render_template('error.html', error=token_data.get('error_description', 'Unknown error'))

@app.route('/get_service_token', methods=['POST'])
def get_service_token():
    global vk_manager
    
    if not vk_manager:
        return jsonify({'error': 'VK Manager not initialized'}), 400
    
    token_data = vk_manager.get_service_token()
    return jsonify(token_data)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)