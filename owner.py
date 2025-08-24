from flask import Flask, render_template_string, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Database setup
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

# Insert new update
def add_update(revenue, customers, inventory):
    conn = sqlite3.connect("owner_dashboard.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO dashboard (date,revenue,customers,inventory) VALUES (?,?,?,?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M"), revenue, customers, inventory))
    conn.commit()
    conn.close()

# Fetch updates
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