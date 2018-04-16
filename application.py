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
from database_setup import Base, Classroom, Student, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from sqlalchemy import create_engine

app = Flask(__name__)

client_secrets = json.loads(open("client_secrets.json", "r").read())
CLIENT_ID = client_secrets["web"]["client_id"]

engine = create_engine('sqlite:///classroomdb.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Helpers
def query_result_to_json(result):
    json = []
    if type(result) is not list:
        return result.serialize
    for r in result:
        json.append(r.serialize)
    return json


# API Endpoints
@app.route("/api/classroom", methods=['GET', 'POST'])
def endpoint_classrooms():
    if request.method == 'GET':
        classroom = session.query(Classroom).all()
        classrooms = query_result_to_json(classroom)
        return jsonify(classrooms)
    if request.method == 'POST':
        if login_session.get('user_id'):
            name = request.args.get('name')
            if name:
                new_classroom = Classroom(
                    name=name,
                    user_id=login_session.get('user_id'))
                session.add(new_classroom)
                session.commit()
                json_classroom = query_result_to_json(new_classroom)
                return jsonify(json_classroom)
        return jsonify([])
    else:
        return "Restricted Method"


@app.route("/api/classroom/<int:id>", methods=['GET', 'POST', 'DELETE'])
def endpoint_classroom(id):
    if request.method == 'GET':
        classroom = session.query(Classroom).filter(Classroom.id == id).first()
        if classroom:
            classroom_json = query_result_to_json(classroom)
            return jsonify(classroom_json)
        else:
            return jsonify([])

    elif request.method == 'POST':
        if login_session.get('user_id'):
            name = request.args.get('name')
            desc = request.args.get('description')
            if name and desc:
                new_student = Student(
                    name=name,
                    description=desc,
                    user_id=login_session.get('user_id'),
                    classroom_id=id)
                session.add(new_student)
                session.commit()
                json_student = query_result_to_json(new_student)
                return jsonify(json_student)
        return jsonify([])
    elif request.method == 'DELETE':
        if login_session.get('user_id'):
            classroom = session.query(Classroom)
            classroom = classroom.filter(Classroom.id == id).first()
            session.delete(classroom)
            session.commit()
    else:
        return "Restricted Method"


@app.route("/api/student", methods=['GET'])
def endpoint_students():
    if request.method == 'GET':
        students_query = session.query(Student).all()

        if(students_query):
            students = query_result_to_json(students_query)
            return jsonify(students)
        else:
            return jsonify([])
    else:
        return "Restricted Method"


@app.route("/api/student/<int:id>", methods=['GET', 'DELETE'])
def endpoint_student(id):
    if request.method == 'GET':
        students_query = session.query(Student)
        students_query = students_query.filter(Student.id == id).first()
        if(students_query):
            students = query_result_to_json(students_query)
            return jsonify(students)
        else:
            return jsonify([])
    if request.method == 'DELETE':
        if login_session.get('user_id'):
            classroom = session.query(Classroom)
            classroom = classroom.filter(Classroom.id == id).first()
            session.delete(classroom)
            session.commit()
            classroom_json = query_result_to_json(classroom)
            return jsonify(classroom_json)
        return jsonify([])
    else:
        return "Restricted Method"


# New Classroom Route
@app.route("/")
@app.route("/classrooms", methods=['GET', 'POST'])
def recent():
    if request.method == 'GET':
        classrooms_result = session.query(Classroom).all()

        classrooms = query_result_to_json(classrooms_result)
        students_result = session.query(Student)
        students_result = students_result.order_by(Student.created_date.desc())
        students_result = students_result.limit(5).all()
        students_results_json = {}
        students_results_json = query_result_to_json(students_result)

        for s in students_results_json:
            classroom_result = session.query(Classroom)
            cid = s['classroom_id']
            classroom_result = classroom_result.filter(Classroom.id == cid)
            classroom_result = classroom_result.first()
            s['classroom_name'] = classroom_result.name

        return render_template(
            "recent.html",
            STATE=create_state(),
            classrooms=classrooms,
            students=students_results_json)
    if request.method == 'POST':
        if login_session.get('user_id'):
            name = request.form.get('name')
            if name:
                new_classroom = Classroom(
                    name=name,
                    user_id=login_session.get('user_id'))
                session.add(new_classroom)
                session.commit()
        return redirect('/')


# New Student Route
@app.route("/classrooms/<int:id>", methods=['GET', 'POST'])
def classrooms(id):
    if request.method == 'GET':
        if login_session.get('user_id'):
            classroom_result = session.query(Classroom)
            classroom_result = classroom_result.filter(Classroom.id == id)
            classroom_result = classroom_result.first()

            classroom = query_result_to_json(classroom_result)

            students_result = session.query(Student)
            student_cid = Student.classroom_id
            students_result = students_result.filter(student_cid == id)
            students_result = students_result.all()

            students = ""
            if students_result:
                students = query_result_to_json(students_result)

            return render_template(
                "classroom.html",
                STATE=create_state(),
                classroom=classroom,
                students=students)
        else:
            return redirect('/')
    elif request.method == 'POST':
        if login_session.get('user_id'):
            name = request.form.get('name')
            desc = request.form.get('description')
            print(name)
            print(desc)
            if name:
                new_student = Student(
                    name=name,
                    description=desc,
                    user_id=login_session.get('user_id'),
                    classroom_id=id)
                session.add(new_student)
                session.commit()
        return redirect("/classrooms/{}".format(id))


# Update Student Route
@app.route("/students/<int:id>", methods=['POST'])
def student_update(id):
    if request.method == 'POST':
        student = session.query(Student).filter(Student.id == id).first()

        if login_session.get('user_id') and student:
            name = request.form.get('name')
            desc = request.form.get('description')

            if name:
                student.name = name
            if desc:
                student.description = desc

            session.add(student)
            session.commit()
        return redirect('/classrooms/{}'.format(student.classroom_id))


# Delete Student Route
@app.route("/students/<int:id>/delete", methods=['POST'])
def student_delete(id):
    if request.method == 'POST':
        student = session.query(Student).filter(Student.id == id).first()
        if login_session.get('user_id') and student:
            session.delete(student)
            session.commit()
        return redirect('/classrooms/{}'.format(student.classroom_id))


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
    login_session["email"] = data["email"]

    user_result = session.query(User)
    user_result = user_result.filter(User.email == login_session["email"])
    user_result = user_result.first()

    if user_result:
        user = query_result_to_json(user_result)
        login_session["user_id"] = user['id']
    else:
        new_user = User(email=login_session["email"])
        session.add(new_user)
        session.commit()
        user_result = session.query(User)
        user_result = user_result.filter(User.email == login_session["email"])
        user_result = user_result.first()
        user = query_result_to_json(user_result)
        login_session["user_id"] = user['id']

    return redirect('/')


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
    del login_session["user_id"]
    return redirect('/')


if __name__ == "__main__":
    app.secret_key = "super secret key"
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
