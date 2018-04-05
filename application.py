# /usr/bin/env python3

from flask import Flask, render_template, request, redirect, jsonify, url_for, flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open("client_secrets.json", "r").read())["web"]["client_id"]


@app.route("/")
@app.route("/login")
def loginPage():
    if 'username' in login_session:
        return redirect('/recent')
    state = "".join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session["state"] = state
    return render_template("login.html", STATE=state)


@app.route("/recent")
def recentPage():
    if 'username' not in login_session:
        return redirect('/login')

    return render_template("recent.html", session=login_session)


@app.route("/gconnect", methods=["POST"])
def gconnect():
    # A new state is created whenever we load the login page
    # so we can only login from that page (prevents hijacking)
    if(request.args.get("state") != login_session["state"]):
        print("Invalid state parameter")
        response = make_response(json.dumps("Invalid state parameter"), 401)
        response.headers["Content-Type"] = "application/json"
        return response

    code = request.data

    # Create a flow using the client_secrets that can be used to
    # easily handle oauth with Google
    try:
        oauth_flow = flow_from_clientsecrets("client_secrets.json", scope="")
        oauth_flow.redirect_uri = "postmessage"
        # Create a credentials object with an access token.
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        print("Failed to upgrade authorization code")
        response = make_response(json.dumps("Failed to upgrade authorization code"), 401)
        response.headers["Content-Type"] = "application/json"
        return response
    
    access_token = credentials.access_token
    url = "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}".format(access_token)
    h = httplib2.Http()
    # Send our access token to Google and receive the user info we need
    result = json.loads(h.request(url, "GET")[1].decode("utf-8"))

    if result.get("error") is not None:
        print(result.get("error"))
        response = make_response(json.dumps(result.get("error")), 500)
        response.headers["Content-Type"] = "application/json"

    # Check if the posted user_id is the same as the requested one
    gplus_id = credentials.id_token["sub"]
    if result["user_id"] != gplus_id:
        print("Token's user ID doesn't match given user ID.")
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers["Content-Type"] = "application/json"
        return response
    
    # Here we make sure that we are connecting the this app only
    if result["issued_to"] != CLIENT_ID:
        print("Token's client ID does not match app's.")
        response = make_response(json.dumps("Token's client ID does not match app's."), 401)
        response.headers["Content-Type"] = "application/json"
        return response
    
    # Check to see if someone is logged in already
    stored_access_token = login_session.get("access_token")
    stored_gplus_id = login_session.get("gplus_id")
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        print("Current user is already connected.")
        response = make_response(json.dumps("Current user is already connected."),200)
        response.headers["Content-Type"] = "application/json"
        return response
    
    # Store token & ID for this session
    login_session["access_token"] = credentials.access_token
    login_session["gplus_id"] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {"access_token": credentials.access_token, "alt": "json"}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)
    login_session["username"] = data["name"]
    login_session["picture"] = data["picture"]

    return render_template("recent.html")


@app.route("/gdisconnect")
def gdisconnect():
    access_token = login_session.get("access_token")
    if access_token is None:
        print("No user is connected")
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = "https://accounts.google.com/o/oauth2/revoke?token={}".format(access_token)
    h = httplib2.Http()
    result = h.request(url, "GET")[0]

    if result["status"] == "200":
        del login_session["gplus_id"]
        del login_session["username"]
        del login_session["picture"]
        return redirect('/login')
    else:
        print("Failed to revoke token from given user")
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


if __name__ == "__main__":
    app.secret_key = "super secret key"
    app.debug = True
    app.run(host = "0.0.0.0", port = 5000)
