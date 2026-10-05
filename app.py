import os
import uuid

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# ============================================================
# Configuration
# ============================================================

load_dotenv()

BASE_URL = os.getenv("LLAMA_BASE_URL")
API_KEY = os.getenv("LLAMA_API_KEY")
MODEL = os.getenv("LLAMA_MODEL", "deepseek-r1:1.5b")

SYSTEM_PROMPT = """
You are Sarweshwar, my personal AI assistant.

Your job is to:
- Answer questions helpfully and accurately.
- Remember the conversation within the current chat.
- Maintain context from previous messages.
- Be concise when the question is simple.
- Give detailed explanations when the question requires them.
- Use Markdown whenever it improves readability.
"""


# ============================================================
# OpenAI Client
# ============================================================

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(page_title="Sarweshwar", page_icon="🕉️", layout="centered")


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    .sarweshwar-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0;
    }

    .sarweshwar-subtitle {
        text-align: center;
        color: #888;
        margin-top: 0.2rem;
        margin-bottom: 2rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Chat Management
# ============================================================


def create_chat(title="New Chat"):
    """
    Creates a new conversation and returns its ID.
    """

    chat_id = str(uuid.uuid4())

    st.session_state.chats[chat_id] = {
        "title": title,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
    }

    return chat_id


def get_current_chat():
    """
    Returns the currently selected conversation.
    """

    return st.session_state.chats[st.session_state.current_chat_id]


def delete_chat(chat_id):
    """
    Delete a specific conversation.
    """

    if chat_id in st.session_state.chats:

        del st.session_state.chats[chat_id]

    # If no chats remain, create a new one
    if not st.session_state.chats:

        new_chat_id = create_chat()

        st.session_state.current_chat_id = new_chat_id

    # If deleted chat was active, switch to another chat
    elif st.session_state.current_chat_id == chat_id:

        st.session_state.current_chat_id = next(iter(st.session_state.chats))


def clear_current_chat():
    """
    Clear messages from the current conversation
    without deleting the conversation itself.
    """

    current_chat = get_current_chat()

    current_chat["messages"] = [{"role": "system", "content": SYSTEM_PROMPT}]

    current_chat["title"] = "New Chat"


# ============================================================
# Initialize Session State
# ============================================================

if "chats" not in st.session_state:

    st.session_state.chats = {}

    first_chat_id = create_chat(title="New Chat")

    st.session_state.current_chat_id = first_chat_id


if "current_chat_id" not in st.session_state:

    st.session_state.current_chat_id = next(iter(st.session_state.chats))


# ============================================================
# Generate Response
# ============================================================


def generate_response(messages):

    response = client.chat.completions.create(
        model=MODEL, messages=messages, stream=True
    )

    for chunk in response:

        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta

        if delta.content:
            yield delta.content


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:

    st.title("🕉️ Sarweshwar")

    st.caption("Your personal AI assistant")

    st.divider()

    # --------------------------------------------------------
    # New Chat
    # --------------------------------------------------------

    if st.button("＋ New Chat", use_container_width=True):

        new_chat_id = create_chat()

        st.session_state.current_chat_id = new_chat_id

        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # Chat History
    # --------------------------------------------------------

    st.subheader("💬 Chat History")

    chat_items = list(st.session_state.chats.items())

    if not chat_items:

        st.caption("No conversations yet.")

    for chat_id, chat in reversed(chat_items):

        title = chat["title"]

        # Highlight current chat
        if chat_id == st.session_state.current_chat_id:

            button_label = f"● {title}"

        else:

            button_label = f"  {title}"

        if st.button(button_label, key=f"chat_{chat_id}", use_container_width=True):

            st.session_state.current_chat_id = chat_id

            st.rerun()

    st.divider()

    # --------------------------------------------------------
    # Current Chat Controls
    # --------------------------------------------------------

    st.subheader("⚙️ Current Chat")

    if st.button("🧹 Clear Conversation", use_container_width=True):

        clear_current_chat()

        st.rerun()

    if st.button("🗑️ Delete Chat", use_container_width=True):

        current_id = st.session_state.current_chat_id

        delete_chat(current_id)

        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # Model Information
    # --------------------------------------------------------

    st.subheader("🤖 Model")

    st.code(MODEL)

    st.caption("Chat history is currently stored in " "Streamlit session state.")


# ============================================================
# Get Current Chat
# ============================================================

current_chat = get_current_chat()

messages = current_chat["messages"]


# ============================================================
# Main Header
# ============================================================

st.markdown(
    '<div class="sarweshwar-title">' "🕉️ Sarweshwar" "</div>", unsafe_allow_html=True
)

st.markdown(
    '<div class="sarweshwar-subtitle">' "Your personal AI assistant" "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# Display Current Conversation
# ============================================================

for message in messages:

    if message["role"] == "system":
        continue

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# ============================================================
# User Input
# ============================================================

prompt = st.chat_input("Ask Sarweshwar anything...")


if prompt:

    # --------------------------------------------------------
    # Add user message
    # --------------------------------------------------------

    messages.append({"role": "user", "content": prompt})

    # --------------------------------------------------------
    # Automatically generate chat title
    # --------------------------------------------------------

    if current_chat["title"] == "New Chat":

        # Use first ~40 characters
        title = prompt.strip()

        if len(title) > 40:
            title = title[:40] + "..."

        current_chat["title"] = title

    # --------------------------------------------------------
    # Display user message
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(prompt)

    # --------------------------------------------------------
    # Generate assistant response
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        response_placeholder = st.empty()

        full_response = ""

        try:

            for token in generate_response(messages):

                full_response += token

                response_placeholder.markdown(full_response)

            # ------------------------------------------------
            # Save assistant response
            # ------------------------------------------------

            messages.append({"role": "assistant", "content": full_response})

        except Exception as e:

            st.error(f"Error communicating with the model:\n\n{e}")
