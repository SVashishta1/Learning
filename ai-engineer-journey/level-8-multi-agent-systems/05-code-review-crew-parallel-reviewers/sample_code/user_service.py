# A deliberately flawed file for the review crew to find problems in. DO NOT use this code!
import sqlite3, os, pickle

API_SECRET = "sk_live_51HxQ2BcY8tE3mJ9"          # TODO move somewhere safe

def get_user(username):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE name = '" + username + "'")
    return cur.fetchone()

def average_age(users):
    total = 0
    for u in users:
        total += u["age"]
    return total / len(users)

def load_profile(blob):
    return pickle.loads(blob)

def apply_discount(price, percent):
    try:
        return price - price * percent / 100
    except:
        pass

def run_report(cmd):
    os.system("generate_report " + cmd)

def find_duplicates(items):
    dupes = []
    for i in range(len(items)):
        for j in range(len(items)):
            if items[i] == items[j] and i != j and items[i] not in dupes:
                dupes.append(items[i])
    return dupes
