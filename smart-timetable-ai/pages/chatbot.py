import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.notification_utils import inject_custom_css

# Try importing the AI agent and LangChain components
try:
    from ai_agent import get_agent_executor
    from langchain_core.messages import HumanMessage, AIMessage
    has_dependencies = True
    import_error_msg = ""
except ImportError as e:
    has_dependencies = False
    import_error_msg = str(e)

st.set_page_config(page_title="AI Timetable Agent - Smart Timetable AI", layout="wide")
inject_custom_css()

if not has_dependencies:
    st.error(
        "❌ **Missing Dependencies**: The required AI Agent or LangChain packages are not installed in your active Python environment.\n\n"
        f"**Error details**: {import_error_msg}\n\n"
        f"Your current Python interpreter is: `{sys.executable}`\n\n"
        "To resolve this, open your terminal and run:\n"
        "```bash\n"
        "pip install langchain langchain-core langchain-community langchain-google-genai python-dotenv plotly\n"
        "```\n"
        "Or activate your virtual environment before launching Streamlit:\n"
        "```powershell\n"
        "venv\\Scripts\\activate\n"
        "pip install -r requirements.txt\n"
        "```"
    )
    st.stop()

st.title("🤖 AI Timetable Assistant")
st.write("Talk to the agentic scheduler using natural language. The AI can check slots, create schedules, detect overlaps, and resolve conflicts automatically.")

# Sidebar instructions & Quick Suggestions
with st.sidebar:
    st.header("⚡ Agent Control Panel")
    
    # Reset conversation
    if st.button("🗑️ Clear Conversation History"):
        st.session_state.chat_messages = []
        st.success("Chat history cleared.")
        st.rerun()
        
    st.markdown("---")
    st.subheader("💡 Try typing these:")
    
    suggestions = [
        "What is my schedule for today?",
        "Find a free 2-hour slot tomorrow",
        "Schedule DBMS Class tomorrow from 10:00 to 11:30 AM",
        "Plan study sessions for my upcoming DBMS Exam",
        "Move event ID 1 to Friday evening at 18:00"
    ]
    
    for sug in suggestions:
        if st.button(sug, key=f"sug_{sug}"):
            st.session_state.pending_input = sug
            st.rerun()

# Initialize Chat State
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# If suggestion clicked, copy it to a temporary input holder
user_query = ""
if "pending_input" in st.session_state and st.session_state.pending_input:
    user_query = st.session_state.pending_input
    st.session_state.pending_input = ""

# Render conversation logs
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Capture new chat inputs (either via regular typing or sidebar suggestion)
chat_input = st.chat_input("Ask the AI to schedule classes, study sessions, etc...")
if chat_input:
    user_query = chat_input

if user_query:
    # 1. Display user query
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.chat_messages.append({"role": "user", "content": user_query})
    
    # 2. Query Agent Executor
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_placeholder.markdown("🧠 *Analyzing timetable, checking conflicts, and formulating response...*")
        
        try:
            # Check dependency imports
            import langchain_core
            
            # Map history list to LangChain format
            langchain_history = []
            for m in st.session_state.chat_messages[:-1]: # exclude latest user query
                if m["role"] == "user":
                    langchain_history.append(HumanMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    langchain_history.append(AIMessage(content=m["content"]))
                    
            agent_executor = get_agent_executor()
            
            # Invoke agent
            result = agent_executor.invoke({
                "input": user_query,
                "chat_history": langchain_history
            })
            
            response_text = result["output"]
            response_placeholder.markdown(response_text)
            
            # Add to state
            st.session_state.chat_messages.append({"role": "assistant", "content": response_text})
            
        except ImportError as ie:
            # Catch our custom ImportError raised in ai_agent.py when packages are missing
            err_msg = str(ie)
            response_placeholder.error(err_msg)
        except Exception as e:
            err_msg = str(e)
            # Detect standard API key invalid issues
            if "API_KEY_INVALID" in err_msg or "API key not found" in err_msg:
                response_placeholder.error(
                    "❌ **API Key Error**: The Google Gemini API key seems to be invalid or unconfigured.\n\n"
                    "Please create a `.env` file in the root workspace directory and add:\n"
                    "`GEMINI_API_KEY=your_actual_api_key_here`"
                )
            else:
                response_placeholder.error(f"❌ **Error executing request**: {err_msg}")