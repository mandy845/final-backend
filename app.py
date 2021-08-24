import hmac
import sqlite3
import datetime

from flask_cors import CORS

from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity


class User(object):

    def __init__(self, id, username, email_address, password):
        self.id = id
        self.username = username
        self.password = password
        self.email_address = email_address


# create registration and login table for the user
def init_user_table():
    conn = sqlite3.connect('list.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user"
                 "(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "email_address TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


# fetch the information from the table
def fetch_users():
    with sqlite3.connect('list.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4], data[5]))
    return new_data


def init_schedule_table():
    with sqlite3.connect('list.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS To_do_list"
                     " (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "Name TEXT NOT NULL,"
                     "type_of_chores TEXT NOT NULL, "
                     "Email_address TEXT,"
                     "scheduled_time TEXT,"
                     "scheduled_date TEXT)")
    print("schedule table created successfully.")


init_user_table()
init_schedule_table()

users = fetch_users()


username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'


jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


# registration info  for postman to get the data through request.json
@app.route('/user-registration/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":

        first_name = request.json['first_name']
        last_name = request.json['last_name']
        email_address = request.json['email_address']
        username = request.json['username']
        password = request.json['password']

        with sqlite3.connect("list.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user("
                           "first_name,"
                           "last_name,"
                           "email_address,"
                           "username,"
                           "password) VALUES(?, ?, ?, ?,?)", (first_name, last_name, email_address, username, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201
        return response

#  creating the scheduled chores


@app.route('/create-chores/', methods=["POST"])
def create_chores():
    response = {}
    if request.method == "POST":
        Name = request.json['Name']
        types_of_chores = request.json['type_of_chores']
        email_address = request.json['email_address']
        date = request.json["scheduled_date"]
        time = request.json["scheduled_time"]
        print("fdgdhgjkh")

        with sqlite3.connect('list.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO to_do_list("
                           "Name,"
                           "type_of_chores,"
                           "email_address,"
                           "scheduled_date,"
                           "scheduled_time) VALUES(?, ?, ?, ?, ?)", (Name, types_of_chores, email_address, date, time))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "to-do list added successfully"
            return response


# getting chores added by id
@app.route('/get-chores/', methods=["GET"])
def get_chore():
    response = {}
    with sqlite3.connect("list.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM to-do list")
        chores = cursor.fetchall()

        response['status_code'] = 200
        response['data'] = chores
        return response


# Deleting chores by id

@app.route("/delete-chores/<int:chores_id>")
def delete_chores(chores_id):
    response = {}
    with sqlite3.connect("list.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM to-do list WHERE id=" + str(chores_id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = "chore list deleted successfully."
        return response


# editing the chores list by id

@app.route('/edit-chores/<int:chores_id>/', methods=["PUT"])
def edit_chores(chores_id):
    response = {}
    if request.method == "PUT":
        with sqlite3.connect('list.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("name") is not None:
                put_data["name"] = incoming_data.get("name")
                with sqlite3.connect('list.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE To-do list SET name =? WHERE id=?", (put_data["name"], chores_id))
                    conn.commit()
                    response['message'] = "Update was successful"
                    response['status_code'] = 200
                    if incoming_data.get("name") is not None:
                        put_data['name'] = incoming_data.get('name')
                        with sqlite3.connect('list.db') as conn:
                            cursor = conn.cursor()
                            cursor.execute("UPDATE To-do list SET name =? WHERE id=?", (put_data["name"], chores_id))
                            conn.commit()
                            response["name"] = " Name updated successfully"
                            response["status_code"] = 200
                            return response


# filtering chores by the type of chores

@app.route('/filter-product/<type>/', methods=["GET"])
def filter_product(type_of_chores):
    response = {}
    with sqlite3.connect("list.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM To-do list WHERE type_of_chores LIKE '%" + type_of_chores + "%'")
        posts = cursor.fetchall()
        response['status_code'] = 200
        response['data'] = posts
        return jsonify(response)


# getting chores by the id
@app.route('/get-chores/<int:chores_id>/', methods=["GET"])
def get_product(chores_id):
    response = {}
    with sqlite3.connect("online.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM To-do list WHERE id=" + str(chores_id))
        response["status_code"] = 200
        response["description"] = "chores  retrieved successfully"
        response["data"] = cursor.fetchone()
        return jsonify(response)


if __name__ == "__main__":
    app.debug = True
    app.run()




