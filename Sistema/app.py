import json
import os
from flask import Flask, render_template, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_JSON = os.path.join(BASE_DIR, "empleos.json")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/datos")
def datos():
    try:
        with open(RUTA_JSON, "r", encoding="utf-8") as archivo:
            empleos = json.load(archivo)
        return jsonify(empleos)
    except:
        return jsonify([])


if __name__ == "__main__":
    app.run(debug=True)
