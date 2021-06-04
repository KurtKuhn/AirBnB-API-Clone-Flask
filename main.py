from flask import Flask, jsonify, redirect, render_template, session, request
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.request import urlopen
from google.cloud import datastore
from jose import jwt


import requests
import json
import constants
import property
import renter
import jwt

app = Flask(__name__)
app.register_blueprint(property.bp)
app.register_blueprint(renter.bp)
app.secret_key = 'SECRET_KEY'

client = datastore.Client()

# Local URl
# CALLBACK_URL = 'http://localhost:5000/callback'

#Deployed URL
CALLBACK_URL = 'https://portfolio-315300.wn.r.appspot.com/callback'
oauth = OAuth(app)

#OAUTH2
CLIENT_ID = constants.CLIENT_ID
CLIENT_SECRET = constants.CLIENT_SECRET
DOMAIN = "simple-airbnb-api-clone.us.auth0.com"

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


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/testing_authorization', methods=["POST"])
def test_auth():

    payload = jwt.verify_jwt(request)
    print(payload)

    return payload

@app.route('/login', methods=['POST'])
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

@app.route('/ui_login')
def ui_login():
    return auth0.authorize_redirect(redirect_uri=CALLBACK_URL)

@app.route('/callback')
def callback_handling():

    # Handles response from token endpoint
    id_token = auth0.authorize_access_token()["id_token"]
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    query = client.query(kind=constants.user)
    results = list(query.fetch())

    user_flag = False

    for e in results:
        if e["user id"] == userinfo["sub"]:
            user_flag = True

    if not user_flag:

        new_user = datastore.entity.Entity(key=client.key(constants.user))
        new_user.update({"user id": userinfo["sub"],
                         "name": userinfo["name"],
                         "id": new_user.id,
                         "self": f'{constants.APP_URL}' + "/user/" + str(new_user.id) })

        client.put(new_user)

    # Store the user information in flask session.
    session['jwt_payload'] = userinfo

    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'JWT': id_token
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

@app.route("/delete_all", methods=['GET'])
def delete_all():

    properties = list(client.query(kind=constants.property).fetch())
    for property in properties:

        client.delete(property)

    renters = list(client.query(kind=constants.renter).fetch())
    for renter in renters:

        client.delete(renter)

    users = list(client.query(kind=constants.user).fetch())

    for user in users:
        client.delete(user)

    to_be_returned = ""
    status_code = 202
    return jsonify(to_be_returned), status_code

@app.route("/get_users", methods=['GET'])
def get_users():

    query = client.query(kind=constants.user)
    data = list(query.fetch())

    for e in data:
        e["id"] = e.key.id
        e["self"] = f'{constants.APP_URL}' + "/users/" + str(e.key.id)

    return jsonify(data), 200


if __name__ == '__main__':

  # Specify a hostname and port that are set as a valid redirect URI
  # for your API project in the Google API Console.
  app.run('localhost', 8080, debug=True)

