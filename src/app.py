import streamlit as st
import os
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
from prompts import AGENT_A_PROMPT, AGENT_B_PROMPT

from typing import Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langchain_openai import ChatOpenAI


class CustomAgent:
    def __init__(self, prompt, llm):
        """
        Initialize the agent with a prompt and custom state
        
        Args:
            agent: React agent
            consulted_B (boolean): True if agent B has been consulted
        """
        self.agent = create_react_agent(
                        llm,
                        tools = [],
                        state_modifier=prompt,
                    )
        self.consulted_B = False

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
    # if agent B has been consulted, return answer by B
    if not agent_A.consulted_B:
        result = agent_A.agent.invoke(state)
        msg = result["messages"][-1]
    else:
        msg = state["messages"][-1]

    # decide if consult agent B
    goto = get_next_node(msg, "agent_B")

    if goto == 'agent_B':
        agent_A.consulted_B = True
    else:
        agent_A.consulted_B = False

    return Command(
        update={
            "messages": [
                AIMessage(msg.content, name="agent_A")
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
    # Forward user question (take message before agent A)
    new_state = {"messages": [
        HumanMessage(state["messages"][-2].content)
    ]}
    result = agent_B.agent.invoke(new_state)
    update = result["messages"][-1].content

    return Command(
        update={
            "messages": [
                AIMessage(update, name="researcher")
            ]
        },
        goto="agent_A",
    )


def process_input(graph, messages, thread: dict):
    """
    Processes user input through the compiled graph and returns the response.
    """
    events = graph.stream(
        {
            "messages": messages,
        }, 
    thread
    )

    # DEBUG flag to optionally print all states (useful for debugging)
    DEBUG = False
    for s in events:
        if DEBUG:
            print(s)
            print("----")
    return s['agent_A']['messages'][-1].content



# extra side bar for requesting openai key
# with st.sidebar:
#    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
#    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
#    "[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
#    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"

st.title("💬 Chatbot")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Initialize LangChain chat model
openai_api_key = os.environ["OPENAI_API_KEY"]
llm = ChatOpenAI(model="gpt-4o", temperature=0.7, openai_api_key=openai_api_key)
# Conversation agent and node
agent_A = CustomAgent(AGENT_A_PROMPT, llm)
agent_B = CustomAgent(AGENT_B_PROMPT, llm)

# Graph definition
workflow = StateGraph(MessagesState)
workflow.add_edge(START, "agent_A")  # Start with agent_A
workflow.add_node("agent_A", conversation_node)
workflow.add_node("agent_B", clever_node)
# Note: routing from A to B is done inside the methods
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
# Thread configuration
thread = {"configurable": {"thread_id": "1"}}

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = process_input(graph, st.session_state.messages, thread)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)
