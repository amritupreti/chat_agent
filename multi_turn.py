# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed in accordance with the terms of the Llama 3 Community License Agreement.
import os
import sys
from typing import List, Optional

from pydantic import BaseModel

from .common.client_utils import *  # noqa: F403
from termcolor import cprint


class UserTurnInput(BaseModel):
    message: UserMessage
    attachments: Optional[List[Attachment]] = None


def prompt_to_turn(
    content: str, attachments: Optional[List[Attachment]] = None
) -> UserTurnInput:
    return UserTurnInput(
        message=UserMessage(content=content, role="user"), attachments=attachments
    )


# Function to extract response message
def extract_response_message(turn_create_responses):
    response_message = ""

    for response in turn_create_responses:
        # Check if the response is of type 'TurnCompletePayload'
        if hasattr(response.event.payload, 'event_type') and response.event.payload.event_type == 'turn_complete':
            # Extracting the content of the final message
            response_message = response.event.payload.turn.output_message.content

    return response_message

async def execute_turns(
    agent_config: AgentConfig,
    custom_tools: List[CustomTool],
    turn_inputs: List[UserTurnInput],
    host: str = "localhost",
    port: int = 5000,
):
    agent = await get_agent_with_custom_tools(
        host=host,
        port=port,
        agent_config=agent_config,
        custom_tools=custom_tools,
    )
    resp = []
    while len(turn_inputs) > 0:
        turn = turn_inputs.pop(0)

        iterator = agent.execute_turn(
            [turn.message],
            turn.attachments,
        )
        cprint(f"User> {turn.message.content}", color="white", attrs=["bold"])
        response = ""
        async for chunk in iterator:
            print(chunk)
            if isinstance(chunk, ToolResponseMessage):
                response = chunk.content
            else:
                event = chunk.event
                event_type = event.payload.event_type
                if event_type == "step_complete":
                    response = event.payload.step_details.inference_model_response.content

    return response