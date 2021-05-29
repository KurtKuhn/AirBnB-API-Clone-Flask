import flask
import json
import requests
import constants
import os
from authlib.integrations.flask_client import OAuth

from flask import redirect
from flask import render_template
from flask import session
from flask import Flask, request, jsonify, _request_ctx_stack

from google.cloud import datastore
from google.oauth2 import id_token
from google.auth.transport import requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from google.auth.transport.requests import AuthorizedSession


from six.moves.urllib.request import urlopen

from jose import jwt

from authlib.integrations.flask_client import OAuth

# Google Authentican Stuff
app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

CLIENT_ID = constants.CLIENT_ID
CLIENT_SECRET = constants.CLIENT_SECRET
DOMAIN = constants.URI
redirect_uri = constants.URI

CLIENT_SECRETS_FILE = "client_secret.json"

# Use the client_secret.json file to identify the application requesting
# authorization. The client ID (from that file) and access scopes are required.
SCOPE = ['https://www.googleapis.com/auth/userinfo.profile',
         'openid',
         'https://www.googleapis.com/auth/userinfo.email']
client = datastore.Client()

# Local URl
CALLBACK_URL = 'http://localhost:5000/oauthcallback'

# When running locally, disable OAuthlib's HTTPs verification.
# ACTION ITEM for developers:
#     When running in production *do not* leave this option enabled.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Relax the SCOPE of OAUTH
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

API_SERVICE_NAME = 'drive'
API_VERSION = 'v2'

ALGORITHMS = ["RS256"]

oauth = OAuth(app)

# AUTH0 STUFF
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

def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

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

@app.route('/autho_login', methods=['POST'])
def login_user():
    content = request.get_json()
    username = content["username"]
    password = content["password"]
    body = {'grant_type': 'password', 'username': username,
            'password': password,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
            }
    headers = {'content-type': 'application/json'}
    url = 'https://' + DOMAIN + '/oauth/token'
    r = requests.post(url, json=body, headers=headers)
    return r.text, 200, {'Content-Type': 'application/json'}

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

@app.route('/')
def index():
    print("In index")
    return render_template("index.html")

@app.route('/authorize')
def authorize():

    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPE)

    #flow.redirect_uri = flask.url_for('http://127.0.0.1:5000/login', _external=True)
    # flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    flow.redirect_uri = 'http://localhost:5000/oauth2callback'

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state

    return flask.redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():

    state = request.args.get('state')
    # state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPE, state=state)

    flow.redirect_uri = 'http://localhost:5000/oauth2callback'

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    print(flask.session)

    return flask.redirect(flask.url_for('test_api_request'))


    # Auth 0 Authorization
    # token = oauth.fetch_token(
    #     'https://accounts.google.com/o/oauth2/token',
    #     authorization_response=request.url,
    #     client_secret=CLIENT_SECRET)
    # req = requests.Request()
    #
    # id_info = id_token.verify_oauth2_token(
    # token['id_token'], req, CLIENT_ID)
    # print ("Your JWT is: " + token['id_token'])
    # print ("Your unique id is " + id_info['sub'])
    #
    # jwt = token['id_token']
    # id = id_info['sub']
    #
    # return flask.render_template(
    #   "login.html",
    #    sub = id,
    #    jwt = jwt,
    #
    #  )



@app.route('/test')
def test_api_request():
  if 'credentials' not in flask.session:
    return flask.redirect('authorize')

  # Load credentials from the session.
  credentials = google.oauth2.credentials.Credentials( **flask.session['credentials'])

  authed_session = AuthorizedSession(credentials)
  response = authed_session.get('https://www.googleapis.com/auth/userinfo.profile')


  print(response)



  return ("working on this")

# @app.route('/ui_login')
# def ui_login():
#     print("ui_login")
#     return auth0.authorize_redirect(redirect_uri=CALLBACK_URL)
#
# @app.route('/dashboard')
# # @requires_auth
# def dashboard():
#     print(session)
#     return render_template('dashboard.html',
#                            userinfo=session['profile'],
#                            userinfo_pretty=json.dumps(session['jwt_payload'], indent=4))

# @app.route('/boats', methods=['POST', 'GET'])
# def add_boat():
#
#     if request.method == 'POST':
#
#         payload = verify_jwt(request)
#
#         content = request.get_json()
#         new_boat = datastore.entity.Entity(key=client.key(BOATS))
#         new_boat.update({"name": content["name"],
#                         "type": content["type"],
#                         "length": content["length"],
#                         "public": content["public"],
#                         "owner": payload["sub"]})
#
#         client.put(new_boat)
#         data = new_boat
#         data["id"] = str(new_boat.id)
#         # data["owner"] = payload["sub"]
#
#         return jsonify(data), 201
#
#     elif request.method == 'GET':
#
#         # Check to see if the authorization header exists
#         if 'Authorization' in request.headers:
#
#             payload = verify_jwt(request)
#
#             query = client.query(kind=BOATS)
#             results = list(query.fetch())
#             owners_list = []
#
#             for e in results:
#                 if e["owner"] == payload['sub']:
#                     e["id"] = str(e.key.id)
#                     owners_list.append(e)
#
#             if len(owners_list) == 0:
#                 return jsonify(results), 200
#
#             else:
#                 return jsonify(owners_list), 200
#
#         # Authorization header doesn't exist
#         else:
#
#             query = client.query(kind=BOATS)
#             results = list(query.fetch())
#             boats_list = []
#
#             for e in results:
#                 if e["public"] == True:
#                     e["id"] = str(e.key.id)
#                     boats_list.append(e)
#
#             return jsonify(boats_list), 200
#
#     else:
#         return jsonify({"Error": "Method not recognized"}), 405
#
# @app.route("/boats/<boat_id>", methods=['DELETE'])
# def delete_boat(boat_id):
#
#     if request.method == 'DELETE':
#
#         # Check to see if the payload exists
#         payload = verify_jwt(request)
#
#         # Get the current boat
#         boat_key = client.key(BOATS, int(boat_id))
#         current_boat = client.get(key=boat_key)
#
#         if current_boat == None:
#             return jsonify({"Error": "No boat exists with that id"}), 403
#
#         print(current_boat)
#
#         if current_boat["owner"] == payload["sub"]:
#             client.delete(boat_key)
#             return jsonify("", 204)
#
#         else:
#             return jsonify({"Error": "That boat belongs to another owner"}), 403
#
#     else:
#         return jsonify({"Error": "Invalid request type"}), 403
#
# @app.route("/owners/<owner_id>/boats", methods=['GET'])
# def get_owner_boats(owner_id):
#
#     if request.method == 'GET':
#
#         payload = verify_jwt(request)
#
#         if len(payload) == 0:
#             return jsonify({"Error": "Invalid JWT"}), 401
#
#         query = client.query(kind=BOATS)
#         results = list(query.fetch())
#
#         print(results)
#
#         owners_list = []
#
#         for e in results:
#             if e["owner"] == owner_id and e["public"] == True:
#                 e["id"] = str(e.key.id)
#                 owners_list.append(e)
#
#         if len(owners_list) == 0:
#             print("Error. No length")
#             return jsonify({"Error": "This owner has no public boats available"}), 200
#
#         else:
#             print("There are some boats!")
#             return jsonify(owners_list), 200
#
#     else:
#         return {"Error": "Method not recognized"}, 405
#
#
# @app.route('/lodgings/<id>', methods=['GET'])
# def lodgings_get(id):
#     if request.method == 'GET':
#         payload = verify_jwt(request)
#         lodging_key = client.key(BOATS, int(id))
#         lodging = client.get(key=lodging_key)
#         return json.dumps(lodging)
#     else:
#         return jsonify(error='Method not recogonized')


if __name__ == '__main__':

  # Specify a hostname and port that are set as a valid redirect URI
  # for your API project in the Google API Console.
  app.run('localhost', 8080, debug=True)