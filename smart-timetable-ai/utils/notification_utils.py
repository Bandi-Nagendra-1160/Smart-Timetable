import streamlit as st

def inject_custom_css():
    """Injects premium CSS styles to customize the default Streamlit theme, giving it a modern glassmorphism feel."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Font family overrides */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Premium Glassmorphic Cards */
    div.css-1r6g72y, div.stMetric {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 18px 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    
    div.stMetric:hover {
        transform: translateY(-4px);
        border-color: rgba(144, 202, 249, 0.3);
    }
    
    /* Styled header banner */
    .hero-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
    }
    
    /* Button animations */
    .stButton>button {
        border-radius: 8px !important;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%) !important;
        color: white !important;
        font-weight: 500 !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(30, 60, 114, 0.3) !important;
    }
    
    .stButton>button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(30, 60, 114, 0.5) !important;
        color: #e0e0e0 !important;
    }
    
    /* Sidebar styling */
    .css-1cd4c4e, [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Interactive status badges */
    .badge-pending {
        background-color: rgba(255, 193, 7, 0.15);
        color: #ffc107;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        border: 1px solid rgba(255, 193, 7, 0.3);
    }
    .badge-completed {
        background-color: rgba(40, 167, 69, 0.15);
        color: #28a745;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        border: 1px solid rgba(40, 167, 69, 0.3);
    }
    .badge-high {
        background-color: rgba(220, 53, 69, 0.15);
        color: #dc3545;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        border: 1px solid rgba(220, 53, 69, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

def show_toast_notification(message, icon="🔔"):
    """Displays a native Streamlit toast notification."""
    st.toast(message, icon=icon)

def show_conflict_warning(conflicts):
    """Renders a styled error box detailing overlapping timetable slots."""
    for conflict in conflicts:
        st.error(
            f"⚠️ **Scheduling Conflict Detected!**\n\n"
            f"Your proposed event overlaps with an existing schedule:\n"
            f"- **Subject**: {conflict['subject']}\n"
            f"- **Type**: {conflict['event_type']}\n"
            f"- **Time**: {conflict['start_time']} - {conflict['end_time']}\n"
            f"- **Priority**: {conflict['priority']}"
        )

def show_success_banner(message):
    """Renders a styled success banner."""
    st.success(message, icon="✅")

def show_info_banner(message):
    """Renders a styled information banner."""
    st.info(message, icon="ℹ️")
