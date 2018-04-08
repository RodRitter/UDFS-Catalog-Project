# /usr/bin/env python3

import sqlite3
import random
import string
import httplib2
import json
import requests
from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash, make_response
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Classroom, Student
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from flask import jsonify

app = Flask(__name__)

client_secrets = json.loads(open("client_secrets.json", "r").read())
CLIENT_ID = client_secrets["web"]["client_id"]


# Helpers
def query_db(query):
    conn = sqlite3.connect("classroomdb.db")
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


# Converts tuple database results into a regular array
# that we can read with javascript
def convert_to_array(results):
    parsed = []
    for t in results:
        tuple_parsed = []
        for r in t:
            tuple_parsed.append(r)
        parsed.append(tuple_parsed)
    return parsed


# Routing
@app.route("/", methods=['GET', 'POST'])
@app.route("/classrooms", methods=['GET', 'POST'])
def recent():
    # Regular Page View
    if request.method == "GET":
        all_classrooms = query_db("SELECT id, name FROM classroom")
        last_students = query_db(
            "SELECT strftime('%d-%m-%Y %H:%M:%S', datetime(student.created_date)), \
            student.id, student.name, classroom.id, classroom.name \
            FROM student JOIN classroom \
            ON student.classroom_id=classroom.id \
            ORDER BY created_date DESC LIMIT 5")

        classrooms = convert_to_array(all_classrooms)
        students = convert_to_array(last_students)
        return render_template(
            "recent.html",
            STATE=create_state(),
            classrooms=classrooms,
            students=students)
    elif request.method == 'POST':
        return '/POST'
    else:
        # Not A Valid Request
        return "NOT VALID REQUEST"


@app.route("/classrooms/<int:id>", methods=["GET", "POST"])
def classrooms(id):
    # Regular Page View
    if request.method == "GET":
        classroom_query = query_db(
            "SELECT name \
            FROM classroom \
            WHERE classroom.id={}".format(id))

        classroom_name = convert_to_array(classroom_query)[0][0]
        student_query = query_db(
            "SELECT name, description, id \
            FROM student \
            WHERE classroom_id={}".format(id))

        students = convert_to_array(student_query)
        return render_template(
            "classroom.html",
            STATE=create_state(),
            classroom_name=classroom_name,
            students=students)
    elif request.method == 'POST':
        return '/POST'
    else:
        # Not A Valid Request
        return "NOT VALID REQUEST"


# Google OAuth
def create_state():
    state = "".join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session["state"] = state
    return state


@app.route("/gconnect", methods=["POST"])
def gconnect():
    # A new state is created whenever we load the login page
    # so we can only login from that page (prevents hijacking)
    if(request.args.get("state") != login_session["state"]):
        print("Invalid state parameter")
        response = make_response(json.dumps("Invalid state parameter"), 401)
        response.headers["Content-Type"] = "application/json"
        return response

    data = request.data.decode('utf8')
    credentials = json.loads(data)

    access_token = credentials['access_token']
    url = "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}"
    url = url.format(access_token)
    h = httplib2.Http()
    # Send our access token to Google and receive the user info we need
    result = json.loads(h.request(url, "GET")[1].decode("utf-8"))

    if result.get("error") is not None:
        print(result.get("error"))
        response = make_response(json.dumps(result.get("error")), 500)
        response.headers["Content-Type"] = "application/json"

    # Check if the posted user_id is the same as the requested one
    gplus_id = credentials["id_token_sub"]
    if result["user_id"] != gplus_id:
        print("Token's user ID doesn't match given user ID.")
        response = json.dumps("Token's user ID doesn't match given user ID.")
        response = make_response(response, 401)
        response.headers["Content-Type"] = "application/json"
        return response

    # Here we make sure that we are connecting the this app only
    if result["issued_to"] != CLIENT_ID:
        print("Token's client ID does not match app's.")
        response = json.dumps("Token's client ID does not match app's.")
        response = make_response(response, 401)
        response.headers["Content-Type"] = "application/json"
        return response

    # Check to see if someone is logged in already
    stored_access_token = login_session.get("access_token")
    stored_gplus_id = login_session.get("gplus_id")
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        print("Current user is already connected.")
        response = json.dumps("Current user is already connected.")
        response = make_response(response, 200)
        response.headers["Content-Type"] = "application/json"
        return response

    # Store token & ID for this session
    login_session["access_token"] = credentials["access_token"]
    login_session["gplus_id"] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {"access_token": credentials["access_token"], "alt": "json"}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)
    login_session["username"] = data["name"]
    login_session["picture"] = data["picture"]

    return redirect('/classrooms')


@app.route("/gdisconnect")
def gdisconnect():
    access_token = login_session.get("access_token")
    if access_token is None:
        print("No user is connected")
        response = json.dumps('Current user not connected.')
        response = make_response(response, 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = "https://accounts.google.com/o/oauth2/revoke?token={}"
    url = url.format(access_token)
    h = httplib2.Http()
    h.request(url, "GET")

    del login_session["gplus_id"]
    del login_session["username"]
    del login_session["picture"]
    return redirect('/')


if __name__ == "__main__":
    app.secret_key = "super secret key"
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
