from langgraph.graph import MessagesState, END
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

from agents import conversation_node, clever_node


def process_input(user_request: str):
    # Graph definition
    workflow = StateGraph(MessagesState)
    workflow.add_edge(START, "agent_A")      # Start with agent_A
    workflow.add_node("agent_A", conversation_node)
    workflow.add_node("agent_B", clever_node)
    # Note: routing from A to B is done inside the methods
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)

    thread = {"configurable": {"thread_id": "1"}}
    events = graph.stream(
        {
            "messages": [
                (
                    "user",
                    user_request,
                )
            ],
        }, 
    thread)


    DEBUG = False
    for s in events:
        if DEBUG:
            print(s)
            print("----")
    return s['agent_A']['messages'][-1].content
