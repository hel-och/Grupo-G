import json
from flask import Flask, render_template, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/datos")
def datos():
    try:
        with open("empleos.json", "r", encoding="utf-8") as archivo:
            empleos = json.load(archivo)
        return jsonify(empleos)
    except:
        return jsonify([])


if __name__ == "__main__":
    app.run(debug=True)
