import json
from datetime import datetime
import os
from flask import Flask, render_template, request
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
import pika

app = Flask(__name__)

UPLOAD_FOLDER = './static/images'
COSMOS_URL = os.getenv('APPSETTING_COSMOS_URL')
MasterKey = os.getenv('APPSETTING_MasterKey')
STORAGE_ACCOUNT = os.getenv('APPSETTING_STORAGE_ACCOUNT')
CONN_KEY = os.getenv('APPSETTING_CONN_KEY')
DATABASE_ID = 'lab9messagesdb'
CONTAINER_ID = 'lab9messages'

BROKER_IP = os.getenv('BROKER_IP')
BROKER_PORT = os.getenv('BROKER_PORT')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

cosmos_db_client = cosmos_client.CosmosClient(COSMOS_URL, {'masterKey': MasterKey})
cosmos_db = cosmos_db_client.get_database_client(DATABASE_ID)
container = cosmos_db.get_container_client(CONTAINER_ID)

def read_cosmos():
    messages = list(container.read_all_items(max_item_count=10))
    return messages

def insert_cosmos(content, img_path):
    import uuid
    new_message = {
        'id': str(uuid.uuid4()),
        'content': content,
        'img_path': img_path,
        'timestamp': datetime.now().isoformat(" ", "seconds")
    }

    try:
        container.create_item(body=new_message)
    except exceptions.CosmosResourceExistsError:
        print("Resource already exists, didn't insert message.")

def publish_rabbitmq(new_message, blob_path, messagetype):
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(BROKER_IP, BROKER_PORT, '/', credentials))
    channel = connection.channel()
    exchange = 'your_last_name'
    channel.exchange_declare(exchange=exchange, exchange_type='direct')
    
    routing_key = "messageboard.messages.urgent" if messagetype == "urgent" else "messageboard.messages.noturgent"
    
    message_to_send = {"content": new_message, "blob_path": blob_path}
    message_json = json.dumps(message_to_send)
    
    channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message_json)
    
    connection.close()

@app.route("/handle_message", methods=['POST'])
def handleMessage():
    new_message = request.form['msg']
    img_path = ""

    if new_message:
        print("message here")
        if 'file' in request.files and request.files['file']:
            print("file here")
            image = request.files['file']
            img_path = os.path.join(UPLOAD_FOLDER, image.filename)
            image.save(img_path)
            messagetype = request.form['message-type']
            insert_cosmos(new_message, img_path)
            publish_rabbitmq(new_message, img_path, messagetype)

    return render_template('handle_message.html', message=new_message)

@app.route("/", methods=['GET'])
def htmlForm():
    data = read_cosmos()
    return render_template('home.html', messages=data)

if __name__ == "__main__":
    app.run(debug=True)
