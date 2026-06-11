import sys
import os

# Add root to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_agent import get_agent_executor

def ask_ai(question):
    """
    Legacy wrapper function to query the AI assistant.
    Now routes calls directly through the timetable Agent Executor.
    """
    try:
        executor = get_agent_executor()
        result = executor.invoke({
            "input": question,
            "chat_history": []
        })
        return result["output"]
    except Exception as e:
        return f"AI Agent Error: {e}"