from flask import Flask
import psycopg2

app = Flask(__name__)

@app.route("/")
def simulate():
    return ""

@app.route("/")
def root():
    return "hello"

if __name__ == "__main__":
    app.run()