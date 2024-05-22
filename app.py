import json
from datetime import datetime
import os
from flask import Flask, render_template, request


app = Flask(__name__)


from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)


mongo_client = MongoClient("localhost", 27017)
db = mongo_client.flask_db
messages = db.messages

@app.route('/insert_message', methods=['POST'])
def insert_message():
    username = request.form['username']
    message = request.form['message']
    img_path = request.form['img_path'] 
    insert_mongo(username, message, img_path)
    return jsonify({"status": "Message inserted"}), 201

def insert_mongo(username, message, img_path):
    new_message = {
        "username": username,
        "message": message,
        "img_path": img_path
    }
    messages.insert_one(new_message)

@app.route('/get_messages', methods=['GET'])
def get_messages():
    latest_messages = read_mongo()
    return jsonify(latest_messages), 200

def read_mongo():
    return list(messages.find().sort([('_id', -1)]).limit(10))

def handle_message(username, message, img_path):
    insert_mongo(username, message, img_path)

if __name__ == '__main__':
    app.run(debug=True)

