import streamlit as st
import litellm
import os

# Configure Streamlit Page
st.set_page_config(page_title="Universal AI Assistant", page_icon="✨", layout="wide")

# Apply custom dark mode CSS for a premium aesthetic
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0F172A;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }
    
    /* Text Globals */
    p, h1, h2, h3, h4, h5, span {
        color: #F8FAFC !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Inputs */
    .stTextInput>div>div>input {
        background-color: #334155 !important;
        color: #F8FAFC !important;
        border-radius: 8px !important;
        border: 1px solid #475569 !important;
    }
    
    .stSelectbox>div>div>div {
        background-color: #334155 !important;
        color: #F8FAFC !important;
        border-radius: 8px !important;
        border: 1px solid #475569 !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: #3B82F6 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #2563EB !important;
        transform: scale(1.02);
    }
    
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR: UNIVERSAL BYOK SETTINGS ---
with st.sidebar:
    st.title("⚙️ AI Settings")
    st.markdown("Enter your API keys below. They are stored locally during this session.")
    
    # Provider Keys
    with st.expander("🔑 API Keys", expanded=True):
        openai_key = st.text_input("OpenAI API Key", type="password")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
            
        anthropic_key = st.text_input("Anthropic (Claude) API Key", type="password")
        if anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key
            
        # Very Important: We remove your hardcoded key so it isn't stolen on GitHub!
        # Instead, we load it safely from Streamlit Cloud Secrets.
        opus_secret = ""
        try:
            if "ANTHROPIC_API_KEY" in st.secrets:
                opus_secret = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            pass
            
        opus_key = st.text_input(
            "Anthropic (Claude) Opus 4.7 API Key", 
            type="password", 
            value=opus_secret,
            placeholder="Paste API Key here..."
        )
        if opus_key:
            os.environ["ANTHROPIC_API_KEY"] = opus_key
            
        gemini_key = st.text_input("Google Gemini API Key", type="password")
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
            
        deepseek_key = st.text_input("DeepSeek API Key", type="password")
        if deepseek_key:
            os.environ["DEEPSEEK_API_KEY"] = deepseek_key

    # Model Selection
    st.markdown("---")
    model_choice = st.selectbox(
        "🧠 Select Model",
        [
            # Anthropic
            "anthropic/claude-4.7-opus",
            "anthropic/opus4.7",
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20240620",
            # OpenAI
            "gpt-4o",
            "gpt-4-turbo",
            # Google
            "gemini/gemini-1.5-pro",
            "gemini/gemini-1.5-flash",
            # DeepSeek
            "deepseek/deepseek-chat"
        ]
    )
    
    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- MAIN CHAT INTERFACE ---
st.title("✨ Universal AI Assistant")
st.markdown(f"**Currently talking to:** `{model_choice}`")

# Display Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Type your message here..."):
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Generate AI Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Format messages for LiteLLM
            litellm_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            
            # Call LiteLLM with streaming
            # litellm automatically picks up keys from os.environ
            response_stream = litellm.completion(
                model=model_choice,
                messages=litellm_messages,
                stream=True
            )
            
            # Read from stream
            for chunk in response_stream:
                # Safely extract delta content
                if len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content is not None:
                        full_response += delta.content
                        message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # Save AI Response
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            # If nothing streamed successfully, remove the user's prompt so Anthropic doesn't crash on the next try due to 'consecutive user roles'
            if not full_response:
                st.session_state.messages.pop()
            
            st.error(f"Error communicating with {model_choice}. Please make sure you have entered the correct API key in the sidebar.\n\nDetails: {str(e)}")
