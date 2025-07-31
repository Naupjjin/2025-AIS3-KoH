from flask import Flask, render_template, request, make_response, redirect, send_from_directory, url_for, flash,  abort, jsonify
import os
import threading
import time

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulator import Simulator

import logging

class IgnoreSpecificRoutesFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        if "/api/round_info" in msg:
            return False
        return True

logging.getLogger('werkzeug').addFilter(IgnoreSpecificRoutesFilter())


SIMULATOR = Simulator(1)
SIMULATE_START = False
ROUND_DURATION = 300
ROUND_START_TIME = None
NOW_ROUND = 0
STORED_SCRIPT = "ret #0"

app = Flask(__name__)
app.secret_key = os.urandom(32)

@app.route("/")
def root():
    return render_template("game.html")


@app.route("/api/round_info")
def round_timer():
    global NOW_ROUND, ROUND_START_TIME, ROUND_DURATION, NOW_ROUND
    if ROUND_START_TIME is None:
        return jsonify({"status": "no_round_started", "round": NOW_ROUND})
    
    elapsed = time.time() - ROUND_START_TIME
    remaining = max(0, ROUND_DURATION - elapsed)
    return jsonify({
        "status": "running",
        "round": NOW_ROUND,
        "elapsed_seconds": int(elapsed),
        "remaining_seconds": int(remaining),
        "expired": elapsed >= ROUND_DURATION,
        "simulate_finished": SIMULATOR.finished
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

@app.route("/get_score_records")
def get_score_records():
    res = make_response(SIMULATOR.dump_score_records())
    res.headers['Content-Type'] = "application/json"
    return res


@app.route("/uploads", methods=["GET", "POST"])
def uploads():
    global STORED_SCRIPT
    global SIMULATE_START

    MAX_SIZE = 100 * 1024
    if request.method == "POST":
        SIMULATE_START = False
        file = request.files.get("file")
        if file:
            try:
                content = file.read()
                if len(content) > MAX_SIZE:
                    return "File too large! Maximum 100 KB allowed.", 400

                file_content = content.decode("utf-8", errors="ignore")
                success, line = SIMULATOR.check_script(file_content)
                msg = None
                if success:
                    STORED_SCRIPT = file_content
                else:
                    msg = f"Script parse error at line '{line}'"

                return render_template("uploads.html", latest_script=STORED_SCRIPT, error = msg)
            except:
                return "Something Error, please check your upload scripts"
    
    return render_template("uploads.html", latest_script=STORED_SCRIPT)


@app.route("/start_simulate")
def start_simulate():
    global SIMULATOR, ROUND_START_TIME
    ROUND_START_TIME = time.time()
    print(f"== Start to Simulator ==")
    # initialize
    SIMULATOR = Simulator(1)
    SIMULATOR.finished = False

    def simulate_all(sim: Simulator, total_rounds=200):
        global SIMULATE_START
        for i in range(total_rounds):
            SIMULATOR.simulate()
        SIMULATOR.finished = True
    SIMULATOR.players[0].script = STORED_SCRIPT
    
    # simulate it
    t = threading.Thread(target=simulate_all, args=(SIMULATOR,), daemon=True)
    t.start()

    return f"Start simulation"

@app.route("/kill_simulation")
def kill_simulate():
    global SIMULATE_START
    SIMULATE_START = False
    return "killed simulation"



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=48763, debug=False)
