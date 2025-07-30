from flask import Flask, render_template, request, make_response, redirect, session, url_for, flash,  abort, jsonify
import hashlib
import os
from functools import wraps
import threading
import time
import json
from flask_cors import CORS
from db import get_connection, test_generate_random_game_scores, init_team_scripts, save_game_scores_to_db, update_score_for_round

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulator.simulator import Simulator

SIMULATOR = Simulator(10)

app = Flask(__name__)
app.secret_key = os.urandom(32)
CORS(app)

API_KEY = "TOMORINISCUTETHISISAPIKEY"

POSTGRES_USER = "koh-admin"
POSTGRES_PASSWORD = "9c7f6b1b946aad1a6333dfb6e25f8d21945de8b33d5c67050cf66ec3a94b5dc2"
PENDING = 0

NOW_ROUND = 1
def updates_round(num):
    global NOW_ROUND
    NOW_ROUND = num


# 裝飾器：檢查是否登入
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "team_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def copy_last_round_scripts(new_round: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT MAX(round) FROM scripts WHERE round < %s;", (new_round,))
    last_round = cur.fetchone()[0]

    if last_round is None:
        conn.close()
        return

    cur.execute("""
        INSERT INTO scripts (round, teamid, scripts)
        SELECT %s AS round, teamid, scripts
        FROM scripts
        WHERE round = %s
        ON CONFLICT (round, teamid) DO NOTHING;
    """, (new_round, last_round))

    conn.commit()
    conn.close()

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

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get("KOH-API-KEY")
        if key != API_KEY:
            abort(403)  # Forbidden
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
    session.pop("team_id", None)
    session.pop("is_admin", None)

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
    return render_template("admin_panel.html")


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

@app.route("/round_info")
def round_info():
    return jsonify({
        "round": NOW_ROUND,
        "status": bool(PENDING)
    })

@app.route("/get_map")
def get_map():
    return jsonify(SIMULATOR.map)

@app.route("/get_scores")
def get_scores():
    return jsonify(SIMULATOR.dump_scores())

@app.route("/get_character_records")
def get_character_records():
    res = make_response(SIMULATOR.dump_character_records())
    res.headers['Content-Type'] = "application/json"
    return res

@app.route("/get_chest_records")
def get_chest_records():
    res = make_response(SIMULATOR.dump_chest_records())
    res.headers['Content-Type'] = "application/json"
    return res

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

    MAX_SIZE = 100 * 1024
    if request.method == "POST":
        if PENDING:
            flash("Current round is pending, uploads are disabled.", "error")
            return redirect(url_for("user_panel"))
        file = request.files.get("file")
        if file:
            try:
                content = file.read()
                if len(content) > MAX_SIZE:
                    return "File too large! Maximum 100 KB allowed.", 400

                file_content = content.decode("utf-8", errors="ignore")

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
def get_result(round_num):
    return f"/result : now round : {round_num}"


##### admin api

def get_map_path(round_num: int) -> str:

    maps_num = (round_num - 1) // 5 + 1 

    if maps_num > 20:
        maps_num = 20

    base_dir = os.path.dirname(os.path.abspath(__file__))
    map_file = f"map_{maps_num:02}.txt"
    return os.path.join(base_dir, "..", "simulator", "maps", map_file)


def simulator(round_num):
    global SIMULATOR
    print(f"== Start to Simulator : Round {round_num} ==")
    # initialize
    SIMULATOR = Simulator(10)
    SIMULATOR.finished = False
    SIMULATOR.finished = False

    # read maps
    maps_path = get_map_path(round_num)

    print(f"[Simulator {round_num}] load maps path \'{maps_path}\'")
    SIMULATOR.read_map(maps_path)

    # load player scripts
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT teamid, scripts 
        FROM scripts
        WHERE round = %s
    """, (round_num,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    def simulate_all(sim: Simulator, total_rounds=200):
        for i in range(total_rounds):
            SIMULATOR.simulate()
        SIMULATOR.finished = True  

    print(rows)
    for team_id, script in rows:
        if 0 < team_id and team_id <= len(SIMULATOR.players):
            SIMULATOR.players[team_id - 1].script = script
    
    # simulate it
    t = threading.Thread(target=simulate_all, args=(SIMULATOR,), daemon=True)
    t.start()

    # fetch result to json
    base_dir = os.path.dirname(os.path.abspath(__file__))

    playerinfo_path = os.path.join(base_dir, "player_info")
    chestinfo_path = os.path.join(base_dir, "chest_info")

    os.makedirs(playerinfo_path, exist_ok=True)
    os.makedirs(chestinfo_path, exist_ok=True)

    object_file = f"round_{round_num:02}.json"

    player_file = os.path.join(playerinfo_path, object_file)
    chest_file = os.path.join(chestinfo_path, object_file)

    while not SIMULATOR.finished:

        player_data = SIMULATOR.dump_character_records()
        chest_data = SIMULATOR.dump_chest_records()

        if isinstance(player_data, str):
            player_data = json.loads(player_data)
        if isinstance(chest_data, str):
            chest_data = json.loads(chest_data)

        with open(player_file, "w", encoding="utf-8") as f:
            json.dump(player_data, f, ensure_ascii=False, indent=2)

        with open(chest_file, "w", encoding="utf-8") as f:
            json.dump(chest_data, f, ensure_ascii=False, indent=2)

        time.sleep(1)

    player_data = SIMULATOR.dump_character_records()
    chest_data = SIMULATOR.dump_chest_records()
    if isinstance(player_data, str):
        player_data = json.loads(player_data)
    if isinstance(chest_data, str):
        chest_data = json.loads(chest_data)

    with open(player_file, "w", encoding="utf-8") as f:
        json.dump(player_data, f, ensure_ascii=False, indent=2)

    with open(chest_file, "w", encoding="utf-8") as f:
        json.dump(chest_data, f, ensure_ascii=False, indent=2)

    game_scores_list = SIMULATOR.dump_scores()
    t.join()

    save_game_scores_to_db(round_num, game_scores_list)
    update_score_for_round(round_num)

    return f"Success simulate {round_num}"

@app.route("/api/round_status/<int:round_num>")
@api_key_required
def round_status(round_num):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM scores WHERE round = %s", (round_num,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    if round_num > NOW_ROUND:
        status = "not_started"
    elif round_num == NOW_ROUND:
        if PENDING == 1:
            if count == 0:
                status = "pending"
            else:
                status = "completed"
        else:
            status = "active"
    else:
        status = "rejudge" if count == 0 else "completed"

    return {"round": round_num, "status": status}

@app.route("/api/rejudge/<int:round_num>")
@api_key_required
def rejudge(round_num):

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM game_history WHERE round = %s", (round_num,))
    cur.execute("DELETE FROM scores WHERE round = %s", (round_num,))
    conn.commit()
    cur.close()
    conn.close()

    try:
        t = threading.Thread(target=simulator, args=(round_num,))
        t.daemon = True
        t.start()
        return {"status": "ok", "message": f"rejudge round {round_num} started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/api/start_round/<int:round_num>")
@api_key_required
def round_start(round_num):
    global PENDING
    PENDING = 0
    updates_round(round_num)
    copy_last_round_scripts(round_num)

    return {"status": "ok", "message": f"round {round_num} start!"}



@app.route("/api/pending/<int:round_num>")
@api_key_required
def round_pending(round_num):
    global PENDING
    PENDING = 1
    updates_round(round_num)

    ### Start Simulator
    try:
        t = threading.Thread(target=simulator, args=(round_num,))
        t.daemon = True  
        t.start()
        return {"status": "ok", "message": f"simulator startup for round {round_num}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


@app.route("/admin/start_round/<int:round_num>")
@login_required
@admin_required
def admin_start_round(round_num):
    global PENDING
    PENDING = 0
    updates_round(round_num)
    copy_last_round_scripts(round_num)

    return jsonify({"status": "ok", "message": f"round {round_num} start!"})


@app.route("/admin/pending/<int:round_num>")
@login_required
@admin_required
def admin_pending(round_num):
    global PENDING
    PENDING = 1
    updates_round(round_num)

    try:
        t = threading.Thread(target=simulator, args=(round_num,))
        t.daemon = True  
        t.start()
        return jsonify({"status": "ok", "message": f"simulator startup for round {round_num}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/admin/rejudge/<int:round_num>")
@login_required
@admin_required
def admin_rejudge(round_num):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM game_history WHERE round = %s", (round_num,))
    cur.execute("DELETE FROM scores WHERE round = %s", (round_num,))
    conn.commit()
    cur.close()
    conn.close()

    try:
        t = threading.Thread(target=simulator, args=(round_num,))
        t.daemon = True
        t.start()
        return jsonify({"status": "ok", "message": f"rejudge round {round_num} started"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/admin/round_status/<int:round_num>")
@login_required
@admin_required
def admin_round_status(round_num):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM scores WHERE round = %s", (round_num,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    if round_num > NOW_ROUND:
        status = "not_started"
    elif round_num == NOW_ROUND:
        if PENDING == 1:
            if count == 0:
                status = "pending"
            else:
                status = "completed"
        else:
            status = "active"
    else:
        status = "rejudge" if count == 0 else "completed"

    return {"round": round_num, "status": status}

if __name__ == "__main__":
    if NOW_ROUND == 1:
        # init_token_table()
        init_team_scripts()
    app.run(host="0.0.0.0", port=48763, debug=False)
