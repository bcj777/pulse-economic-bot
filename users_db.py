import json
import os

DB_PATH = os.path.join(os.getcwd(), "data", "users.json")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f:
            json.dump([], f)


def get_users():
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except:
        return []


def add_user(user_id):
    users = get_users()

    if user_id not in users:
        users.append(user_id)

        with open(DB_PATH, "w") as f:
            json.dump(users, f)
