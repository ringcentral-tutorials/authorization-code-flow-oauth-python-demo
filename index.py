from flask import Flask, render_template, request, session
import os, urllib

app = Flask(__name__)
app.secret_key = 'somesecretstring'

from ringcentral import SDK
rcsdk = None

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    from dotenv import Dotenv
    env = request.values.get('env')
    if env == "sandbox":
        dotenv = Dotenv("./environment/.env-sandbox")
    else:
        dotenv = Dotenv("./environment/.env-production")
    os.environ.update(dotenv)
    base_url = os.environ.get('RC_SERVER_URL') + '/restapi/oauth/authorize'
    params = (
        ('response_type', 'code'),
        ('redirect_uri', os.environ.get("RC_REDIRECT_URL")),
        ('client_id', os.environ.get("RC_CLIENT_ID")),
        ('state', 'initialState')
    )
    authorize_uri = base_url + '?' + urllib.urlencode(params)
    redirect_uri = os.environ.get('RC_REDIRECT_URL')
    return render_template('login.html', authorize_uri=authorize_uri, redirect_uri=redirect_uri)

@app.route('/oauth2callback', methods=['GET'])
def oauth2callback():
    global rcsdk
    rcsdk = SDK(os.getenv("RC_CLIENT_ID"), os.getenv("RC_CLIENT_SECRET"), os.getenv("RC_SERVER_URL"))
    platform = rcsdk.platform()
    auth_code = request.values.get('code')
    platform.login('', '', '', auth_code, os.getenv("RC_REDIRECT_URL"))
    tokens = platform.auth().data()
    session['tokens'] = tokens
    return "Login successfully"

@app.route('/logout', methods=['GET'])
def logout():
    platform = get_platform()
    if platform != None:
        platform.logout()
        session.pop('tokens', None)
    return render_template('index.html')

@app.route('/test', methods=['GET'])
def callapi():
    platform = get_platform()
    if platform != None:
        api = request.values.get('api')
        if api == "extension":
            resp = platform.get("/restapi/v1.0/account/~/extension")
            return resp.response()._content
        elif api == "extension-call-log":
            resp = platform.get("/restapi/v1.0/account/~/extension/~/call-log")
            return resp.response()._content
        elif api == "account-call-log":
            resp = platform.get("/restapi/v1.0/account/~/call-log")
            return resp.response()._content
        else:
            return render_template('test.html')
    else:
        return render_template('index.html')

def get_platform():
    global rcsdk
    if 'tokens' in session:
        platform = rcsdk.platform()
        platform.auth().set_data(session['tokens'])
        if platform.logged_in():
            return platform
    return None
