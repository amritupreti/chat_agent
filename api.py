import asyncio
import json
import os
import textwrap
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from .mongo import AlertsDataTool
from .common.client_utils import *
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient
from llama_stack_client.types import Attachment, SamplingParams, UserMessage
from llama_stack_client.types.agent_create_params import (
    AgentConfig,
    AgentConfigToolMemoryToolDefinition,
    AgentConfigToolMemoryToolDefinitionMemoryBankConfigUnionMember0,
    AgentConfigToolSearchToolDefinition,
)
from llama_stack_client.types.agents.agents_turn_stream_chunk import AgentsTurnStreamChunk
from llama_stack_client.types.memory_insert_params import Document
from termcolor import cprint

from .utils import data_url_from_file

load_dotenv()


class Agent:
    def __init__(self, host: str, port: int):
        self.agent_id = None
        self.session_id = None
        self.client = LlamaStackClient(
            base_url=f"http://{host}:{port}",
        )
        self.tool_definitions = [AlertsDataTool()]
        self.agent_config = asyncio.run(
            make_agent_config_with_custom_tools(
                model="Llama3.1-8B-Instruct",
                tool_config=QuickToolConfig(
                custom_tools=self.tool_definitions,
                prompt_format="function_tag",
                ),
                disable_safety=True,
            )
        )
        # self.agent_config = AgentConfig(
        #     model="Llama3.1-8B-Instruct",
        #     instructions="You are a helpful assistant",
        #     sampling_params=SamplingParams(strategy="greedy", temperature=1.0, top_p=0.9),
        #     tools=self.tool_definitions,
        #     tool_choice="auto",
        #     tool_prompt_format="function_tag",
        #     input_shields=[],
        #     output_shields=[],
        #     enable_session_persistence=True,
        # )
        self.create_agent(self.agent_config)

    def create_agent(self, agent_config: AgentConfig):
        agentic_system_create_response = self.client.agents.create(
            agent_config=agent_config,
        )
        self.agent_id = agentic_system_create_response.agent_id
        agentic_system_create_session_response = self.client.agents.session.create(
            agent_id=agentic_system_create_response.agent_id,
            session_name="test_session",
        )
        self.session_id = agentic_system_create_session_response.session_id

    def execute_turn(self, content: str):
        response = self.client.agents.turn.create(
            agent_id=self.agent_id,
            session_id=self.session_id,
            messages=[
                UserMessage(content=content, role="user"),
            ],
            stream=True,
        )
        for chunk in response:
            if chunk.event.payload.event_type != "turn_complete":
                yield chunk


    async def chat(self, message, attachments) -> str:
        # messages = []
        # atts = []
        # if attachments is not None:
        #     for attachment in attachments:
        #         atts.append(
        #             Attachment(
        #                 content=data_url_from_file(attachment),
        #                 # hardcoded for now since mimetype is inferred from data_url
        #                 mime_type="text/plain",
        #             )
        #         )
        # messages.append(UserMessage(role="user", content=message))
        response = self.execute_turn(message)
        for resp in response:
            print(resp)
            event = resp.event
            event_type = event.payload.event_type
            if event_type == "step_complete":
                content = event.payload.step_details.inference_model_response.content
                if content == "":
                    content = "Sorry, I don't have an answer for that. Ask me something else."
    
        return content











# class AgentChoice(Enum):
#     Memory = "Memory"
#     Mongo = "Mongo"


# class AgentStore:
#     def __init__(self, host, port, model) -> None:
#         self.model = model
#         self.client = LlamaStackClient(base_url=f"http://{host}:{port}")
#         self.agents = {}
#         self.sessions = {}
#         self.first_turn = {}
#         self.system_message = {}
#         self.agent_choice = AgentChoice.Memory
    

#     async def initialize_agents(self, bank_ids: List[str]) -> None:
#         # Create a live bank that holds live context
#         self.live_bank = self.create_live_bank()

#         self.bank_ids = bank_ids
#         # self.agents[AgentChoice.Memory] = await self.get_agent(
#         #     agent_type=AgentChoice.Memory,
#         #     agent_params={"bank_ids": self.bank_ids + [self.live_bank]},
        
#         # )
#         self.agents[self.agent_choice] = await self.get_agent(
#             agent_type=self.agent_choice,
#         )
#         print(self.agents)
#         self.create_session(self.agent_choice)

#     def create_live_bank(self):
#         self.live_bank = "live_bank"
#         self.client.memory_banks.register(
#             memory_bank={
#                 "identifier": self.live_bank,
#                 "embedding_model": "all-MiniLM-L6-v2",
#                 "chunk_size_in_tokens": 512,
#                 "overlap_size_in_tokens": 64,
#                 "provider_id": "meta-reference",
#             }
#         )
#         # FIXME: To avoid empty banks
#         self.append_to_live_memory_bank(
#             "This is a live bank. It holds live context for this chat"
#         )
#         return self.live_bank

#     async def get_agent(
#         self,
#         agent_type: AgentChoice,
#         agent_params: Optional[Dict[str, Any]] = None,
#     ) -> str:
#         if agent_type == AgentChoice.Mongo:
#             # MongoDB search tool definition
#             def mongo_search(query: str) -> str:
#                 return self.query_mongodb(query)

#             tools = [
#                 AgentConfigToolSearchToolDefinition(
#                     type="search",
#                     search_provider_id="mongo",
#                     search_index="mongo",
#                     search_field="key_field",  # The field you're searching
#                     search_response_field="content",  # The field MongoDB returns as content
#                     function=mongo_search  # Use the MongoDB search function
#                 )
#             ]
#             agent_config = AgentConfig(
#                 model=self.model,
#                 instructions="Use MongoDB to answer questions based on the database.",
#                 sampling_params=SamplingParams(
#                     strategy="greedy", temperature=0.0, top_p=0.95
#                 ),
#                 tools=tools,
#                 enable_session_persistence=True,
#             )
#         if agent_type == AgentChoice.Memory:
#             bank_ids = agent_params.get("bank_ids", [])
#             tools = [
#                 AgentConfigToolMemoryToolDefinition(
#                     type="memory",
#                     max_chunks=5,
#                     max_tokens_in_context=2048,
#                     memory_bank_configs=[
#                         AgentConfigToolMemoryToolDefinitionMemoryBankConfigUnionMember0(
#                             type="vector",
#                             bank_id=bank_id,
#                         )
#                         for bank_id in bank_ids
#                     ],
#                 ),
#             ]
#             user_instructions = ""
#             agent_config = AgentConfig(
#                 model=self.model,
#                 instructions="",
#                 sampling_params=SamplingParams(
#                     strategy="greedy", temperature=0.0, top_p=0.95
#                 ),
#                 tools=tools,
#                 enable_session_persistence=True,
#             )


#          if agent_type == AgentChoice.Mongo:
#             response = await get_agent_with_custom_tools(
#                 host=host,
#                 port=port,
#                 agent_config=agent_config,
#                 custom_tools=custom_tools,
#             )

#         if agent_type == AgentChoice.Memory:
#             response = self.client.agents.create(
#                 agent_config=agent_config,
#             )


#         agent_id = response.agent_id
#         # Use self.first_turn to keep track of whether it's the first turn for each agent or not
#         # This helps knowing whether to send the system message or not
#         self.first_turn[agent_id] = True
#         # Use self.system_message to keep track of the system message for each agent
#         self.system_message[agent_id] = user_instructions
#         return agent_id

#     def create_session(self, agent_choice: str) -> str:
#         agent_id = self.agents[agent_choice]
#         self.first_turn[agent_id] = True
#         response = self.client.agents.session.create(
#             agent_id=agent_id,
#             session_name=f"Session-{uuid.uuid4()}",
#         )
#         self.sessions[agent_choice] = response.session_id
#         return self.sessions[agent_choice]

#     async def build_index(self, file_dir: str) -> str:
#         """Build a memory bank from a directory of pdf files."""

#         # 1. create memory bank
#         bank = self.client.memory.create(
#             body={
#                 "name": "memory_bank",
#                 "config": {
#                     "bank_id": "memory_bank",
#                     "embedding_model": "all-MiniLM-L6-v2",
#                     "chunk_size_in_tokens": 512,
#                     "overlap_size_in_tokens": 64,
#                 },
#             },
#         )
#         self.client.memory_banks.register(
#             memory_bank={
#                 "identifier": "memory_bank",
#                 "embedding_model": "all-MiniLM-L6-v2",
#                 "chunk_size_in_tokens": 512,
#                 "overlap_size_in_tokens": 64,
#                 "provider_id": "meta-reference",
#             }
#         )
#         # cprint(f"Created bank: {json.dumps(bank, indent=4)}", color="green")

#         # 2. load pdfs from directory as raw text
#         paths = []
#         for filename in os.listdir(file_dir):
#             if filename.endswith(".pdf"):
#                 file_path = os.path.join(file_dir, filename)
#                 paths.append(file_path)

#         documents = [
#             Document(
#                 document_id=os.path.basename(path),
#                 content=data_url_from_file(path),
#             )
#             for path in paths
#         ]
#         # insert some documents
#         self.client.memory.insert(bank_id="memory_bank", documents=documents)

#         return "memory_bank"

#     async def chat(self, agent_choice, message, attachments) -> str:
#         assert (
#             agent_choice in self.agents
#         ), f"Agent of type {agent_choice} not initialized"
#         agent_id = self.agents[agent_choice]

#         messages = []
#         # If it's the first turn, send the system message along with the user message
#         if self.first_turn[agent_id]:
#             if self.system_message[agent_id]:
#                 messages.append(
#                     UserMessage(content=self.system_message[agent_id], role="user")
#                 )
#             self.first_turn[agent_id] = False

#         session_id = self.sessions[agent_choice]
#         atts = []
#         if attachments is not None:
#             for attachment in attachments:
#                 atts.append(
#                     Attachment(
#                         content=data_url_from_file(attachment),
#                         # hardcoded for now since mimetype is inferred from data_url
#                         mime_type="text/plain",
#                     )
#                 )
#         messages.append(UserMessage(role="user", content=message))
#         generator = self.client.agents.turn.create(
#             agent_id=self.agents[agent_choice],
#             session_id=self.sessions[agent_choice],
#             messages=messages,
#             attachments=atts,
#             stream=True,
#         )
#         for chunk in generator:
#             event = chunk.event
#             event_type = event.payload.event_type
#             # FIXME: Use the correct event type
#             if event_type == "turn_complete":
#                 turn = event.payload.turn

#         inserted_context = ""
#         for step in turn.steps:
#             # FIXME: Update to use typed step types instead of strings
#             if step.step_type == "memory_retrieval":
#                 inserted_context = step.inserted_context
#             if step.step_type == "tool_execution":
#                 inserted_context = "\n".join([tr.content for tr in step.tool_responses])

#         return turn.output_message.content, inserted_context

#     def append_to_live_memory_bank(self, text: str) -> None:
#         document = Document(
#             document_id=uuid.uuid4().hex,
#             content=text,
#         )
#         self.client.memory.insert(
#             bank_id=self.live_bank, documents=[document]
#         )

#     async def clear_live_bank(self) -> None:
#         # FIXME: This is a hack, ideally we should
#         # clear an existing bank instead of creating a new one
#         self.live_bank = self.create_live_bank()
#         self.agents[AgentChoice.Memory] = await self.get_agent(
#             agent_type=AgentChoice.Memory,
#             agent_params={"bank_ids": self.bank_ids + [self.live_bank]},
#         )
#         self.create_session(AgentChoice.Memory)
