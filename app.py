from flask import Flask
import simulator
import psycopg2

app = Flask(__name__)
SIMULATOR = simulator.Simulator(0)

@app.route("/new_round")
def simulate():
    return ""

@app.route("/")
def root():
    return "hello"

if __name__ == "__main__":
    app.run()