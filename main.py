from langgraph.graph import MessagesState, END
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

from agents import conversation_node, clever_node

# Graph definition
workflow = StateGraph(MessagesState)
workflow.add_edge(START, "agent_A")      # Start with agent_A
workflow.add_node("agent_A", conversation_node)
workflow.add_node("agent_B", clever_node)
# Note: routing from A to B is done inside the methods
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

# Save graph image
image_bytes = graph.get_graph().draw_mermaid_png()
output_file_path = "output_image.png"
# Save the bytes to a file
with open(output_file_path, "wb") as file:
    file.write(image_bytes)


thread = {"configurable": {"thread_id": "1"}}
events = graph.stream(
    {
        "messages": [
            (
                "user",
                "Computer running slow?",
            )
        ],
    }, 
thread)


DEBUG = True
for s in events:
    if DEBUG:
        print(s)
        print("----")


print("Final answer")
print(s['agent_A']['messages'][-1].content)