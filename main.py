from uuid import uuid4
from fastapi import FastAPI, Form, Request
import asyncio
import random
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

# Enable CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

messages = []
message_queue = asyncio.Queue()
active_connections = []  # List to track active connections
CHATBOT_UUID = "2b5b3f75-8df6-11ef-99ad-67b363642d9b"
USER_UUID = "94066bf6-0172-4102-9c94-328608f82f42"
USER_API_KEY = "c5630cc2-86a9-433e-9d25-e5d6ad4f29b1"
CHATBOT_RESPONSES = [
    "Hello! How can I assist you today?",
    "I'm here to help. What do you need?",
    "Can you please provide more details?",
    "Sure, I can do that. Give me a moment.",
    "I'm sorry, I didn't understand that. Can you rephrase?",
    "Thank you for your patience.",
    "Is there anything else I can help with?",
    "Goodbye! Have a great day!",
]


@app.get("/api/chatbot")
def chatbot_messages():
    return messages


@app.post("/api/chatbot")
async def send_message(body: str = Form(...)):
    message = {
        "uuid": str(uuid4()),
        "body": body,
        "to": CHATBOT_UUID,
        "from": USER_UUID,
        "created_at": "2021-10-01T12:00:00Z",
    }

    messages.append(message)

    # Schedule the chatbot response to run independently
    asyncio.create_task(get_chatbot_response(message))

    return message


@app.get("/api/stream")
async def stream_messages(request: Request):
    # Add the connection to the active connections list
    event_generator = event_stream(request)
    return StreamingResponse(event_generator, media_type="text/event-stream")


@app.get("/api/stats")
def get_stats():
    return {
        "total_messages": len(messages),
        "active_connections": len(active_connections),
    }


async def event_stream(request: Request):
    global active_connections
    # Register the new connection
    active_connections.append(request)

    try:
        while True:
            message = await message_queue.get()
            if message:
                try:
                    # Send the message to the SSE client
                    yield f"data: {json.dumps(message)}\n\n"
                except Exception as e:
                    print(f"Error sending message: {e}")
    finally:
        # Clean up when the connection is closed
        active_connections.remove(request)


async def get_chatbot_response(message):
    await message_queue.put({"thinking": True})

    await asyncio.sleep(3)  # Simulate delay

    choice = random.choice(CHATBOT_RESPONSES)

    response = {
        "uuid": str(uuid4()),
        "body": choice,
        "to": USER_UUID,
        "from": CHATBOT_UUID,
        "created_at": "2021-10-01T12:00:00Z",
    }

    messages.append(response)
    await message_queue.put(response)  # Notify that the response is ready

    return response
