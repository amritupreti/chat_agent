import os
import sys
from typing import Dict

from pymongo import MongoClient
from .common.custom_tools import SingleMessageCustomTool
from llama_stack_client.types.tool_param_definition_param import (
    ToolParamDefinitionParam,
)


class AlertsDataTool(SingleMessageCustomTool):
    """Tool to get alerts data from MongoDB"""

    def get_name(self) -> str:
        return "get_alerts_data"

    def get_description(self) -> str:
        return "Get alerts data from database"

    def get_params_definition(self) -> Dict[str, ToolParamDefinitionParam]:
        return {
            "hostname": ToolParamDefinitionParam(
                param_type="str",
                description="Hostname",
                required=False,
            ),
            "service": ToolParamDefinitionParam(
                param_type="str",
                description="Service name",
                required=False,
            ),
            "status": ToolParamDefinitionParam(
                param_type="str",
                description="Status",
                required=True,
            ),
        }

    async def run_impl(self, hostname: str, service: str, status: str):
        # Connect to MongoDB
        try:
            print("Connecting to MongoDB ", os.getenv('MONGODB_URI'))
            client = MongoClient(os.getenv('MONGODB_URI'))
            print("Connected to MongoDB")
            db = client['alertagility']
            collection = db['alertagility_alerts']
        except Exception:
            response =[]
            return response

        # Query the MongoDB collection
        query = {"status": "triggered"}
        if status != "":
            query = {"status": status}

        if hostname != "":
            query["hostname"] = hostname

        response = []
        try:
            data = collection.find(query)
        except Exception:
            return response
        
        for i in data:
            response.append(i)
        return response