import asyncio
import os
from flask import Flask, request, jsonify
import fire

from .api import Agent

app = Flask(__name__)

MODEL = "Llama3.1-8B-Instruct"
CHATBOT = None
SELECTED_AGENT = "5f126596-87d8-4b9f-a44d-3a5b93bfc171"
CHAT_HISTORY = {}
CONTEXT = {}


def initialize(host: str, port: int):
    global CHATBOT
    CHATBOT = Agent(host, port)
    # asyncio.run(CHATBOT.initialize_agents(bank_ids))

@app.route('/apibot', methods=['GET'])
def getchat():
    a = CHAT_HISTORY[SELECTED_AGENT]
    print(a)
    conversation = []
    for i, (user1_msg, user2_msg) in enumerate(a):
        conversation.append({"from": "user1", "to": "user2", "body": user1_msg})
        conversation.append({"from": "user2", "to": "user1", "body": user2_msg})

    return conversation

@app.route('/apibot', methods=['POST'])
def chat():
    global SELECTED_AGENT, CONTEXT, CHAT_HISTORY
    
    # get all form post data
    form_data = request.form.to_dict()
    

    message = request.form.get('body', '')
    attachments = request.form.getlist('attachments')  # If attachments are submitted as multiple form fields
   
    response = asyncio.run(
        CHATBOT.chat(message, attachments)
    )
    
    chat_history = CHAT_HISTORY.get(SELECTED_AGENT, [])
    chat_history.append((message, response))
    CHAT_HISTORY[SELECTED_AGENT] = chat_history
    # CONTEXT[SELECTED_AGENT] = inserted_context
    # print("Response -> ", response)
    return jsonify({'response': "ok"})


def main(host: str = "localhost", port: int = 5000):
    initialize(host, port)
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    fire.Fire(main)
