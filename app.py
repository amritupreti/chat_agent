import asyncio
import os
from flask import Flask, request, jsonify
import fire

from .api import AgentChoice, AgentStore

app = Flask(__name__)

MODEL = "Llama3.1-8B-Instruct"
CHATBOT = None
SELECTED_AGENT = AgentChoice.Memory
BANK_ID = "5f126596-87d8-4b9f-a44d-3a5b93bfc171"
CHAT_HISTORY = {}
CONTEXT = {}

def initialize(host: str, port: int, model: str, bank_id_str: str):
    global CHATBOT
    CHATBOT = AgentStore(host, port, model)
    if bank_id_str:
        bank_ids = bank_id_str.split(",")
    else:
        bank_ids = []
    asyncio.run(CHATBOT.initialize_agents(bank_ids))

@app.route('/chat', methods=['POST'])
def chat():
    global SELECTED_AGENT, CONTEXT, CHAT_HISTORY
    data = request.json
    message = data.get('message', '')
    attachments = data.get('attachments', [])
    
    response, inserted_context = asyncio.run(
        CHATBOT.chat(SELECTED_AGENT, message, attachments)
    )
    chat_history = CHAT_HISTORY.get(SELECTED_AGENT, [])
    chat_history.append((message, response))
    CHAT_HISTORY[SELECTED_AGENT] = chat_history
    CONTEXT[SELECTED_AGENT] = inserted_context
    
    return jsonify({'response': response, 'context': inserted_context})

@app.route('/select_agent', methods=['POST'])
def select_agent():
    global SELECTED_AGENT
    data = request.json
    agent_choice = data.get('agent_choice', '')
    if agent_choice == "":
        agent_choice = "memory"
    print("Selecting Agetnt ", agent_choice)
    SELECTED_AGENT = AgentChoice[agent_choice]
    return jsonify({'message': f'Selected Agent: {SELECTED_AGENT}'})

def main(host: str = "localhost", port: int = 5000, model: str = MODEL, bank_ids: str = ""):
    initialize(host, port, model, bank_ids)
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    fire.Fire(main)
