import os
import requests
from flask import Flask, request, jsonify
from database import Database
import datetime
from utility import log
from command import StartCommand, HelpCommand, DefaultCommand, AddFundCommand, GetFundCommand, HoldingsCommand, TradeExecutionCommand, ExitCommand, OrdersCommand
import traceback

commands = {
    "/start": StartCommand,
    "/help": HelpCommand,
    "/fund": AddFundCommand,
    "/holdings": HoldingsCommand,
    "/balance": GetFundCommand,
    "/trade": TradeExecutionCommand,
    "/exit_trade": ExitCommand,
    "/orders": OrdersCommand
}

app = Flask(__name__)

db = Database()

BOT_TOKEN = os.getenv('BOT_TOKEN')
TEXT_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
PHOTO_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
ACTION_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"


def send_message(message):
    chat_id = message.get("chat_id", "default_value")
    try:
        text_message = message.get("type")
        response = message.get("response", "response")
        if text_message == "text":
            requests.post(ACTION_URL, json={
                          "chat_id": chat_id, "action": "typing"})
            response = requests.post(
                TEXT_URL, json={"chat_id": chat_id, "text": response})
            if response.status_code != 200:
                print(response.content)
            return None
        print("response type is other than text")
        requests.post(ACTION_URL, json={
                      "chat_id": chat_id, "action": "uploading_photo"})

    except Exception as e:
        log("exception in send message")
        log(Exception)
        requests.post(TEXT_URL, json={"chat_id": chat_id, "text": response})


@app.route("/", methods=["GET"])
def handle_home():
    return "Working"


@app.route("/trade", methods=["POST"])
def handle_trade():
    print("command recieved.")
    update = request.get_json()
    command = commands.get("/trade", DefaultCommand)
    print("command loaded.")
    response = command(update, db).execute()
    print("respose loaded.")
    send_message(response)
    print("response sent")
    return "OK", 200


@app.route("/get_position", methods=["POST"])
def handle_position():
    print("command recieved.")
    holdings = db.get_position("json")
    print("respone sent.")
    return jsonify(holdings), 200


@app.route("/exit_trade", methods=["POST"])
def handle_exit():
    print("command recieved.")
    update = request.get_json()
    command = commands.get("/exit_trade", DefaultCommand)
    print("command loaded.")
    response = command(update, db).execute()
    # print(response)
    print("respose loaded.")
    send_message(response)
    print("response sent")
    return "OK", 200


@app.route('/', methods=['POST'])
def handle_command():
    update = {}
    try:
        # db = Database()
        # current_datetime = datetime.datetime.now()
        # db.add_request(str(current_datetime) + " : " + str("request"))
        print("command recieved.")
        update = request.get_json()
        is_bot = update['message']['from']['is_bot']
        print("is_bot : " + str(is_bot))
        first_name = update['message']['from']['first_name']
        print("Name : " + first_name)
        if is_bot == False:

            text = update['message']['text']

            command = commands.get(text.split("\n")[0], DefaultCommand)

            print("command loaded.")

            response = command(update, db).execute()

            print("respose loaded.")

            send_message(response)

            print("response sent")
            return "OK", 200
        return "Drop the message", 200
    except Exception as e:
        current_datetime = datetime.datetime.now()
        where = str(current_datetime) + " : " + \
            str("exception in handle_command")
        log(where)
        update = str(current_datetime) + " : " + \
            str(update)
        log(update)
        print(traceback.format_exc())
        what = str(current_datetime) + " : " + str(e)
        log(what)
        return "Internal server error in main", 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 80)))
