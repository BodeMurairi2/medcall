#!/usr/bin/env python3

import uuid
import os
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

from external_integration.agents.utils.prompts import consultation_prompt
from external_integration.agents.tools.consultation_tool import (verify_registration,
                                                                 collect_user_personal_info,
                                                                 collect_medical_information
                                                                 )

load_dotenv()

consultation_llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_AI_MODEL"),
    api_key=os.getenv("GEMINI_API_KEY_V"),
    temperature=0.1,
    max_tokens=8000
)

consultation_fallback_llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_AI_MODEL"),
    api_key=os.getenv("GEMINI_API_KEY_X"),
    temperature=0.1,
    max_tokens=8000
)

memory_thread = {
    "memory_id": str(uuid.uuid4()).split("-")[0],
    "memory": InMemorySaver()
}

tools = [verify_registration, collect_user_personal_info, collect_medical_information]

def consultation_agent():
    """consultation agent"""
    return create_agent(
        model=consultation_llm,
        checkpointer=memory_thread["memory"],
        tools=tools,
        middleware=[],
        system_prompt=consultation_prompt,
        response_format=None
        )
