from flask import Flask, render_template_string, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("owner_dashboard.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS dashboard (
                    id INTEGER PRIMARY KEY,
                    date TEXT,
                    revenue REAL,
                    customers INTEGER,
                    inventory INTEGER)""")
    conn.commit()
    conn.close()

def add_update(revenue, customers, inventory):
    conn = sqlite3.connect("owner_dashboard.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO dashboard (date,revenue,customers,inventory) VALUES (?,?,?,?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M"), revenue, customers, inventory))
    conn.commit()
    conn.close()

def get_updates():
    conn = sqlite3.connect("owner_dashboard.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM dashboard ORDER BY id DESC LIMIT 5")
    rows = cur.fetchall()
    conn.close()
    return rows

@app.route("/", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        add_update(request.form["revenue"], request.form["customers"], request.form["inventory"])
        return redirect("/")
    updates = get_updates()
    template = """
    <h2>📊 Owner Dashboard Updates</h2>
    <form method="post">
      Revenue: <input name="revenue"><br>
      Customers: <input name="customers"><br>
      Inventory: <input name="inventory"><br>
      <button type="submit">Update</button>
    </form><hr>
    <h3>Recent Updates</h3>
    <ul>
    {% for u in updates %}
      <li>{{u[1]}} | 💰 {{u[2]}} | 👥 {{u[3]}} | 📦 {{u[4]}}</li>
    {% endfor %}
    </ul>
    """
    return render_template_string(template, updates=updates)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

import sqlite3

DB = "properties.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    location TEXT,
                    price REAL)""")
    conn.commit()
    conn.close()

def add_property(name, location, price):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO properties (name,location,price) VALUES (?,?,?)",
                (name, location, price))
    conn.commit()
    conn.close()

def view_properties():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM properties")
    rows = cur.fetchall()
    conn.close()
    return rows

def remove_property(pid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM properties WHERE id=?", (pid,))
    conn.commit()
    conn.close()

def menu():
    while True:
        print("\n🏠 Owner Property List")
        print("1. Add Property\n2. View Properties\n3. Remove Property\n4. Exit")
        choice = input("Enter choice: ")
        if choice == "1":
            n = input("Name: "); l = input("Location: "); p = float(input("Price: "))
            add_property(n, l, p)
        elif choice == "2":
            for r in view_properties():
                print(f"ID:{r[0]} | {r[1]} | {r[2]} | ${r[3]}")
        elif choice == "3":
            pid = int(input("Enter Property ID to remove: "))
            remove_property(pid)
        else:
            break

if __name__ == "__main__":
    init_db()
    menu()

import sqlite3

DB = "properties.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    location TEXT,
                    price REAL)""")
    conn.commit(); conn.close()

def add_property(name, location, price):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO properties (name,location,price) VALUES (?,?,?)",
                (name, location, price))
    conn.commit(); conn.close()

def get_sorted(order_by="name"):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM properties ORDER BY {order_by}")
    rows = cur.fetchall(); conn.close()
    return rows

def menu():
    while True:
        print("\n🏠 Owner Sorting Menu")
        print("1. Add Property\n2. View Sorted by Name\n3. View Sorted by Location\n4. View Sorted by Price\n5. Exit")
        choice = input("Enter choice: ")
        if choice == "1":
            n = input("Name: "); l = input("Location: "); p = float(input("Price: "))
            add_property(n, l, p)
        elif choice == "2":
            for r in get_sorted("name"):
                print(f"ID:{r[0]} | {r[1]} | {r[2]} | ${r[3]}")
        elif choice == "3":
            for r in get_sorted("location"):
                print(f"ID:{r[0]} | {r[1]} | {r[2]} | ${r[3]}")
        elif choice == "4":
            for r in get_sorted("price"):
                print(f"ID:{r[0]} | {r[1]} | {r[2]} | ${r[3]}")
        else:
            break

if __name__ == "__main__":
    init_db()
    menu()

