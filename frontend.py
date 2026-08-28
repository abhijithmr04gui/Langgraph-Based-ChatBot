import streamlit as st
from langchain_core.messages import HumanMessage
from backend_database import chatbot, retrieve_threads
import uuid


def gen_thread_id():
    return str(uuid.uuid4())


def reset_chat():
    thread_id = gen_thread_id()

    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []


def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)


def load_convo(thread_id):
    state = chatbot.get_state(
        config={'configurable': {'thread_id': thread_id}}
    )

    return state.values.get('messages', [])


# Extract only text from Gemini streaming chunks
def get_text(chunk):
    content = chunk.content

    # Normal string content
    if isinstance(content, str):
        return content

    # Gemini may return a list of content blocks
    if isinstance(content, list):
        text = ""

        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text += item.get("text", "")

        return text

    return ""


st.title('AI Based Chatbot')
st.write("Welcome to my Langraph based Smart Chatbot")


# Initialize session state
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []


if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = gen_thread_id()


if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_threads()


add_thread(st.session_state['thread_id'])


# Sidebar
st.sidebar.title('Chat Bot History')


if st.sidebar.button('New Chat'):
    reset_chat()


st.sidebar.header('Conversation History')


for thread_id in st.session_state['chat_threads'][::-1]:

    if st.sidebar.button(str(thread_id), icon='😊'):

        st.session_state['thread_id'] = thread_id

        messages = load_convo(thread_id)

        temp_messages = []

        for msg in messages:

            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'

            temp_messages.append({
                'role': role,
                'content': msg.content
            })

        st.session_state['message_history'] = temp_messages


# Display conversation
for message in st.session_state['message_history']:

    with st.chat_message(message['role']):
        st.write(message['content'])


# Chat input
user_input = st.chat_input("Type here")


if user_input:

    # Add user message to UI history
    st.session_state['message_history'].append({
        'role': 'user',
        'content': user_input
    })

    with st.chat_message('user'):
        st.write(user_input)


    CONFIG = {
        'configurable': {
            'thread_id': st.session_state['thread_id']
        }
    }


    # Generate assistant response
    with st.chat_message('assistant'):

        ai_message = st.write_stream(
            get_text(message_chunk)
            for message_chunk, metadata in chatbot.stream(
                {
                    'messages': [
                        HumanMessage(content=user_input)
                    ]
                },
                config=CONFIG,
                stream_mode='messages'
            )
        )


    # Save assistant response to UI history
    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': ai_message
    })