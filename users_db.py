import json
import os

DB_FILE = "users.json"


def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)


def get_users():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def add_user(user_id):
    users = get_users()

    if user_id not in users:
        users.append(user_id)

        with open(DB_FILE, "w") as f:
            json.dump(users, f)
