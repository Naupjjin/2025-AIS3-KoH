from flask import Flask, render_template, request, redirect, session, url_for, flash
import hashlib
import os
from functools import wraps
from db import get_connection, init_token_table, test_generate_random_game_scores

app = Flask(__name__)
app.secret_key = os.urandom(32)

POSTGRES_USER = "koh-admin"
POSTGRES_PASSWORD = "9c7f6b1b946aad1a6333dfb6e25f8d21945de8b33d5c67050cf66ec3a94b5dc2"

'''
在 pending 時候就要先切 NOW_ROUND 到下一 round
不然會有問題
'''
NOW_ROUND = 31

# 裝飾器：檢查是否登入
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "team_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# 裝飾器：檢查是否為管理員
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("user_panel"))
        return f(*args, **kwargs)
    return decorated_function

# 裝飾器：檢查是否為 users
def users_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("is_admin"):
            return redirect(url_for("admin_panel"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    if "team_id" not in session:
        return redirect(url_for("login"))

    if session.get("is_admin"):
        return redirect(url_for("admin_panel"))
    else:
        return redirect(url_for("user_panel"))


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

            if session["is_admin"]:
                return redirect(url_for("admin_panel"))
            else:
                return redirect(url_for("user_panel"))
        else:
            flash("Invalid token", "error")
    else:
        # 已登入自動跳轉
        if "team_id" in session:
            if session.get("is_admin"):
                return redirect(url_for("admin_panel"))
            else:
                return redirect(url_for("user_panel"))

    return render_template('login.html')


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/user_panel")
@login_required
def user_panel():
    if session.get("is_admin"):
        return redirect(url_for("admin_panel"))
    return render_template("user_panel.html", team_id=session["team_id"])


@app.route("/admin_panel")
@login_required
@admin_required
def admin_panel():
    return "you are admin"


@app.route("/game_history")
@login_required
def game_scores():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT round, team_id, game_scores FROM game_history")
    data = cur.fetchall()
    cur.close()
    conn.close()

    matrix = {}
    for r, t, s in data:
        matrix.setdefault(r, {})[t] = s

    rounds = sorted(matrix.keys())
    teams = sorted({team for r in matrix.values() for team in r})

    return render_template("game_history.html", matrix=matrix, rounds=rounds, teams=teams)


@app.route("/scoreboard")
@login_required
def scoreboard():
    conn = get_connection()
    cur = conn.cursor()
    # 取出所有分數資料：round, team_id, scores
    cur.execute("""
        SELECT round, team_id, scores
        FROM scores
        ORDER BY round ASC, team_id ASC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    data = {}
    rounds = set()
    for round_num, team_id, score in rows:
        rounds.add(round_num)
        if team_id not in data:
            data[team_id] = {}
        data[team_id][round_num] = score

    scoreboard = []
    rounds = sorted(rounds)
    for team_id, round_scores in data.items():
        scores_list = [round_scores.get(r, 0) for r in rounds]
        scoreboard.append({
            'team_id': team_id,
            'total': sum(scores_list),
            'scores': scores_list
        })

    scoreboard.sort(key=lambda x: x['total'], reverse=True)
    my_team_id = session.get('team_id')
    return render_template("scoreboard.html", scoreboard=scoreboard, rounds=rounds, my_team_id=my_team_id)



@app.route("/rules")
@login_required
def rules():
    return render_template("rules.html")


@app.route("/uploads", methods=["GET", "POST"])
@login_required
@users_required
def uploads():
    latest_script = None
    latest_time = None
    if request.method == "POST":
        file = request.files.get("file")
        if file:
            try:
                file_content = file.read().decode("utf-8", errors="ignore")

                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO scripts (round, teamid, scripts)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (round, teamid)
                    DO UPDATE SET scripts = EXCLUDED.scripts,
                                upload_time = CURRENT_TIMESTAMP
                    """,
                    (NOW_ROUND, session["team_id"], file_content)
                )
                conn.commit()
                cur.close()
                conn.close()

                return redirect(url_for("uploads"))
            except:
                return "Something Error, please check your upload scripts"
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT scripts, upload_time
        FROM scripts
        WHERE teamid = %s
        ORDER BY round DESC, upload_time DESC
        LIMIT 1
        """,
        (session["team_id"],)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        latest_script, latest_time = row
    return render_template("uploads.html", latest_script=latest_script, latest_time=latest_time)


@app.route("/result/<int:round_num>")
@login_required
@admin_required
def get_result(round_num):
    return f"/result : now round : {round_num}"


@app.route("/simulator/<int:round_num>")
@login_required
@admin_required
def simulator(round_num):
    return f"/simulator : now round : {round_num}"


@app.route("/new_round")
@login_required
@admin_required
def new_round():
    return "new round"


if __name__ == "__main__":
    init_token_table()
    test_generate_random_game_scores()
    app.run(host="0.0.0.0", port=48763, debug=True)
