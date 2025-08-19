# libraries
from flask import Flask, render_template, request, jsonify, current_app, abort
from flask_cors import CORS

# files imported
from chatbot import *

app = Flask(__name__)
CORS(app)

uri = 'wss://live-transcriber.zevo-tech.com:2053'

@app.get("/")
def index_get():
    return render_template("base.html")


@app.get("/start")
def start_conversation():
    # Initiaza conversatia
    return {"answer": "Bună ziua! Ați sunat la clinica {}, cu ce vă putem ajuta ?".format(clinica)}

@app.post("/get_answer")
def get_answer():
    response = question_respond(request.get_json().get("message"))
    responseMessage = {"answer": response}
    return jsonify(responseMessage)


if __name__ == "__main__":
    app.run(debug=True)
