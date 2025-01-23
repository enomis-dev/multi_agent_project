import os

from typing import Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from prompts import AGENT_A_PROMPT, AGENT_B_PROMPT

# llm model
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Conversation agent and node
agent_A = create_react_agent(
    llm,
    tools = [],
    state_modifier=AGENT_A_PROMPT,
)

# Clever agent and node
agent_B = create_react_agent(
    llm,
    tools = [],
    state_modifier=AGENT_B_PROMPT
)


def get_next_node(last_message: BaseMessage, goto: str) -> str:
    """
    Determines the next node in the decisional flow from agent A to agent B.

    Parameters:
        last_message (BaseMessage): The most recent message sent by the agent. 
                                    If None or contains "I need to consult agent B",
                                    the method returns the `goto` value.
        goto (str): The destination node to proceed to if the condition is met.

    Returns:
        str: The next node in the flow, either `goto` or `END`.
    """
    if not last_message or "I need to consult agent B" in last_message.content:
        return goto
    return END

# Agent A main method
def conversation_node(state: MessagesState) -> Command[Literal["agent_B", END]]:
    """
    Handles the main conversation logic for Agent A.

    Agent A processes the current conversation state, determines the next step 
    in the flow, and optionally transitions to Agent B.

    Parameters:
        state (MessagesState): The current state of the conversation, including 
                               a list of previous messages.

    Returns:
        Command[Literal["agent_B", END]]: A command specifying:
            - `update`: The updated conversation state with Agent A's response.
            - `goto`: The next node in the flow, either "agent_B" or `END`.
    """
    result = agent_A.invoke(state)

    goto = get_next_node(result["messages"][-1], "agent_B")

    return Command(
        update={
            "messages": [
                AIMessage(result["messages"][-1].content, name="agent_A")
            ]
        },
        goto=goto,
    )

# Agent B main method
def clever_node(state: MessagesState) -> Command[Literal["agent_A"]]:
    """
    Handles the main conversation logic for Agent B.

    Agent B processes the user's question, generates a response, and always
    transitions the flow back to Agent A.

    Parameters:
        state (MessagesState): The current state of the conversation, including 
                               a list of previous messages.

    Returns:
        Command[Literal["agent_A"]]: A command specifying:
            - `update`: The updated conversation state with Agent B's response.
            - `goto`: The next node in the flow, which is always "agent_A".
    """
    # Forward user question
    new_state = {"messages": [
        HumanMessage(state["messages"][-2].content)
    ]}
    result = agent_B.invoke(new_state)
    update = result["messages"][-1].content

    return Command(
        update={
            "messages": [
                AIMessage(update, name="researcher")
            ]
        },
        goto="agent_A",
    )
