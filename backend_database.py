from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage,HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3

load_dotenv()

llm = ChatGoogleGenerativeAI(model = 'gemini-3.6-flash')

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

con = sqlite3.connect(database = 'chatbot_1.db',check_same_thread=False) #would not check for same thread now , can be used by multiple threads

# Checkpointer
checkpointer = SqliteSaver(conn = con)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_threads():
    all_threads = set()
    for check in checkpointer.list(None):
        all_threads.add(check.config['configurable']['thread_id'])

    return list(all_threads)

'''result = chatbot.invoke(
    {'messages':[HumanMessage(content = "What is my name")]},
    config=CONFIG
)
print(result)'''