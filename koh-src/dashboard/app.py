from flask import Flask, render_template, request, redirect, session, url_for, flash
import hashlib
import os
from db import get_connection, init_token_table

app = Flask(__name__)
app.secret_key = os.urandom(32)

POSTGRES_USER = "koh-admin"
POSTGRES_PASSWORD = "9c7f6b1b946aad1a6333dfb6e25f8d21945de8b33d5c67050cf66ec3a94b5dc2"


@app.route("/")
def home():
    return render_template('index.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = request.form.get("token") 
        token = hashlib.sha256(token.encode()).hexdigest()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT team_id, is_admin FROM teams WHERE team_token = %s", (token,))

        result = cur.fetchone()
        conn.close()

        if result:
            session["team_id"] = result[0]
            session["is_admin"] = result[1]

            return redirect(url_for("user_panel"))
        else:
            flash("Invalid token", "error")
    else:
        if "team_id" in session:
            if session["is_admin"] == False:
                return redirect(url_for("user_panel"))    
            else:
                return redirect(url_for("admin_panel"))        
        else:
            return render_template('login.html')

@app.route("/user_panel")
def user_panel():
    if "team_id" not in session:
        return redirect(url_for("login"))
    
    if session["is_admin"] == True:
        return redirect(url_for("admin_panel"))    

    return f"Welcome team {session['team_id']}! Admin: {session['is_admin']}"

@app.route("/admin_panel")
def admin_panel():
    if session.get("is_admin") != True:
        return redirect(url_for("user_panel"))    
    return "you are admin"

@app.route("/scoreboard")
def admin_panel(): 
    return "This is scoreboard"

@app.route("/uploads")
def uploads():

    return "This is uploads"

@app.route("/result/<int:round_num>")
def get_result(round_num):

    return f"/result : now round : {round_num}"

@app.route("/simulator/<int:round_num>")
def simulator(round_num):
    return f"/simulator : now round : {round_num}"

@app.route("/new_round")
def new_round():
    return "new round"

if __name__ == "__main__":
    init_token_table()
    app.run(host="0.0.0.0", port=48763, debug=True)
