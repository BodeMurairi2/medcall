#!/usr/bin/env python3

import uuid
import os
import json
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy

from langchain.agents.middleware import ModelFallbackMiddleware

from langchain_google_genai import ChatGoogleGenerativeAI

from langchain.messages import HumanMessage

from langgraph.checkpoint.memory import InMemorySaver

from external_integration.agents.utils.prompts import consultation_prompt
from external_integration.agents.schema.consultation_structure_output import structured_output_consultation
from external_integration.agents.schema.consultation_structure_output import structured_output_consultation

from external_integration.agents.tools.consultation_tool import (verify_registration,
                                                                 collect_user_personal_info,
                                                                 collect_medical_information
                                                                 )

load_dotenv()

# initialize consultation llm
consultation_llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_AI_MODEL"),
    api_key=os.getenv("GEMINI_API_KEY_X"),
    temperature=0.1,
    max_tokens=8000
)

consultation_fallback_llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_AI_MODEL"),
    api_key=os.getenv("GEMINI_API_KEY_X"),
    temperature=0.1,
    max_tokens=8000
)

# initialize memory
memory_thread = {
    "memory_id": str(uuid.uuid4()).split("-")[0],  # temporary memory thread ID
    "memory": InMemorySaver()
}

tools = [verify_registration, collect_user_personal_info, collect_medical_information]

# create Consultation Agent
consultation_agent = create_agent(
    model=consultation_llm,
    checkpointer=memory_thread["memory"],
    tools=tools,
    middleware=[],
    system_prompt=consultation_prompt,
    response_format=None
    )

# start Conversation
print("=== MedCall Consultation Agent ===")
print("Type 'exit' at any time to end.\n")

thread_id = input("Enter User ID (or phone number): ").strip()
phone_number = input("Enter your phone number\n").strip()
consultation_start = True
while consultation_start:
    user_input = input("User: ").strip()

    if user_input.lower() == "exit":
        print("\nExiting consultation...")
        break

    # before calling consultation_agent.invoke(...)
    result = verify_registration.invoke({"phone_number": phone_number})
    if not result.get("registered", False):
        print(json.dumps({
            "status": "complete",
            "current_message": "Sorry! You are not registered. Please use *384*41992# to register.",
            "tool_call": {},
            "consultation_sms": [],
            "doctor_questions": [],
            "patient_responses": [],
            "collected_data": {},
            "summary": "User not registered"
        }, indent=2))
        print("\nConsultation ended: user not registered.")
        break

    response = consultation_agent.invoke(
        {"messages": [HumanMessage(content=f"user question: {user_input}\nuser phone number: {phone_number}")]},
        config={"configurable": {"thread_id": thread_id}}
    )

    raw_content = response["messages"][-1].content
    #print("\nAgent:", response["messages"][-1].content)
    for message in raw_content:
        cleaned = message["text"].replace("```json", "").replace("```", "").strip() 
        parsed = json.loads(cleaned)
        print(json.dumps(parsed, indent=2))

"""
    cleaned = raw_content.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(cleaned)
        print("\nStructured Output:")
        print(json.dumps(parsed, indent=2))
    except Exception as e:
        print("\n❌ Failed to parse JSON")
        print("Error:", e)
        print("Raw:", raw_content)
"""
