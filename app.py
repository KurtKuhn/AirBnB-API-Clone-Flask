
import requests
import constants
import os
import json

from six.moves.urllib.request import urlopen

from jose import jwt

from flask import Flask, jsonify, redirect, render_template, session

from authlib.integrations.flask_client import OAuth
from google.cloud import datastore

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

CLIENT_ID = constants.CLIENT_ID
CLIENT_SECRET = constants.CLIENT_SECRET
DOMAIN = "simple-airbnb-api-clone.us.auth0.com"
client = datastore.Client()

# Local URl
CALLBACK_URL = 'http://localhost:5000/callback'
oauth = OAuth(app)

ALGORITHMS = ["RS256"]
oauth = OAuth(app)
auth0 = oauth.register(
    'auth0',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    api_base_url="https://" + DOMAIN,
    access_token_url="https://" + DOMAIN + "/oauth/token",
    authorize_url="https://" + DOMAIN + "/authorize",
    client_kwargs={
        'scope': 'openid profile email',
    },
)


# This code is adapted from
# https://auth0.com/docs/quickstart/backend/python/01-authorization?_ga=2.46956069.349333901.1589042886-466012638.1589042885#create-the-jwt-validation-decorator

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

def verify_jwt(request):

    auth_header = request.headers['Authorization'].split();
    token = auth_header[1]

    jsonurl = urlopen("https://" + DOMAIN + "/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Invalid header. "
                             "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Invalid header. "
                             "Use an RS256 signed JWT Access Token"}, 401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=CLIENT_ID,
                issuer="https://" + DOMAIN + "/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                             "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                             "description":
                                 "incorrect claims,"
                                 " please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                             "description":
                                 "Unable to parse authentication"
                                 " token."}, 401)

        return payload
    else:
        raise AuthError({"code": "no_rsa_key",
                         "description":
                             "No RSA key in JWKS"}, 401)

@app.route('/')
def index():
    print("In index")
    return render_template("index.html")

@app.route('/ui_login')
def ui_login():
    print("ui_login")
    return auth0.authorize_redirect(redirect_uri=CALLBACK_URL)

@app.route('/callback')
def callback_handling():

    # Handles response from token endpoint
    id_token = auth0.authorize_access_token()["id_token"]
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    # Store the user information in flask session.
    session['jwt_payload'] = userinfo

    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'auth0': id_token
    }
    return redirect('/dashboard')

@app.route('/dashboard')
# @requires_auth
def dashboard():
    print(session)
    return render_template('dashboard.html',
                           userinfo=session['profile'],
                           userinfo_pretty=json.dumps(session['jwt_payload'], indent=4),
                           userprofile_pretty=json.dumps(session['profile'], indent=4))

if __name__ == '__main__':

  # Specify a hostname and port that are set as a valid redirect URI
  # for your API project in the Google API Console.
  app.run('localhost', 8080, debug=True)

