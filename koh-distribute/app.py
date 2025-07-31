from flask import Flask, render_template, request, make_response, redirect, send_from_directory, url_for, flash,  abort, jsonify
import os
import threading
from flask_cors import CORS

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulator import Simulator

SIMULATOR = Simulator(1)
SIMULATE_START = False
STORED_SCRIPT = "ret #0"

app = Flask(__name__)
app.secret_key = os.urandom(32)
CORS(app)

@app.route("/")
def root():
    return render_template("game.html")



@app.route("/round_info")
def round_info():
    return jsonify({
        "round": 0,
        "status": SIMULATE_START,
        "local": True
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
                STORED_SCRIPT = file_content

                return redirect(url_for("uploads"))
            except:
                return "Something Error, please check your upload scripts"
    
    return render_template("uploads.html", latest_script=STORED_SCRIPT)


@app.route("/start_simulate")
def start_simulate():
    global SIMULATOR
    global SIMULATE_START
    SIMULATE_START = True
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
