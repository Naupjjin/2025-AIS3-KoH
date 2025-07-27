from flask import Flask

app = Flask(__name__)

@app.route("/simulate")
def simulate():
    return ""

@app.route("/")
def root():
    return "hello"

if __name__ == "__main__":
    app.run()