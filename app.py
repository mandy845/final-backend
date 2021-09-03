import hmac
import sqlite3
import datetime

from flask_cors import CORS

from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_mail import Message, Mail


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

            print(data)
            new_data.append(User(data[0], data[4], data[3], data[5]))
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

#   CONFIGURATIONS FOR THE MAIL AND APP TO WORK
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
# app.config['SECRET_KEY'] = "super-secret"
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PASSWORD'] = "@manda20W"
app.config['MAIL_USERNAME'] = "amandamakara7@gmail.com"

mail = Mail(app)

@app.route('/')
def welcome():
    response = {}
    response["message"] = "Hello"
    response["status_code"] = 200
    return response

@app.route('/protected')
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
                           "password) VALUES(?, ?, ?, ?, ?)", (first_name, last_name, email_address, username, password))
            conn.commit()
            response["message"] = "Successfully registered. Please check your email for more info"
            response["status_code"] = 201
            print(email_address, first_name)
            send_email("thank you for using our to-do list", "welcome we are here to help with your schedule ", email_address)

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


# getting chores added 
@app.route('/get-chores/', methods=["GET"])
def get_chore():
    response = {}
    with sqlite3.connect("list.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM to_do_list")
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
        cursor.execute("DELETE FROM to_do_list WHERE id=" + str(chores_id))
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

@app.route('/filter-product/<type_of_chores>/', methods=["GET"])
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


@app.route('/get-userlogin/<int:user_id>/', methods=["GET"])
def get_user(user_id):
    response = {}
    with sqlite3.connect("online.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM user WHERE user_id='{user_id}'")
        response["status_code"] = 200
        response["description"] = "chores  retrieved successfully"
        response["data"] = cursor.fetchone()
    return jsonify(response)


# the email will be sent to the user with the chores they added and scheduled time with the date
@app.route('/send-email/<int:user_id>/', methods=["POST"])
def reminder_email(user_id):
    print(user_id)
    response = {}
    with sqlite3.connect("list.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM user WHERE user_id='{user_id}'")
        user = cursor.fetchone()

    print(user)

    first_name = user[1] + user[2]
    email = user[3]
    print(email)
    with sqlite3.connect("list.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM to_do_list WHERE email_address='{email}'")
        chores = cursor.fetchone()

        print(chores)
        print(chores[2])
        print(chores[4])
        print(chores[5])

        types_of_chores = chores[2]
        time = chores[4]
        date = chores[5]

        send_email("you successfully added your schedule", "hey "
                   + first_name + " here is your Schedule " +
                   types_of_chores + " at " + time + " on the " + date, email)
        response["status_code"] = 200
        response["description"] = "chores  sent successfully"
    return jsonify(response)


def remind_user():
    date_1 = datetime.datetime(2021, 7, 26, 0, 5, 0)
    date_2 = datetime.datetime(2021, 7, 24, 0, 5, 0)

# Get interval between two datetimes as timedelta object
    diff = date_2 - date_1

# Get the interval in minutes
    diff_in_minutes = diff.total_seconds() / 60

    print('Difference between two datetimes in minutes:')
    print(diff_in_minutes)

    if diff_in_minutes <= 30:
        print("about to send.")
        send_email('Welcome to the keep your schedule on time (to-do list).', "amandamakara7@gmail.com", "Amanda")


#   FUNCTION WILL SEND AN EMAIL TO THE PROVIDED email_address

def send_email(subject, message, email_address):
    email_to_send = Message(subject, sender='amandamakara7@gmail.com',
                            recipients=[email_address])
    email_to_send.body = message
    mail.send(email_to_send)


# remind_user()


if __name__ == "__main__":
    app.debug = True
    app.run()




