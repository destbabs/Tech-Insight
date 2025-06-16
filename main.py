import streamlit as st
import time
from dotenv import load_dotenv
import os
from components.news import render_news_tab
from components.bookmarks import render_bookmarks_tab
from aiscraper import techtalker_tab, techtimeline_tab
from ii import render_hacker_news_tab
from app2 import render_academic_papers_tab
import json
from datetime import datetime


st.set_page_config(
    page_title="Tech Insight",
    page_icon="🧑‍💻",
    layout="wide"
)

load_dotenv()

# Initialize session state for bookmarks if not exists
if 'bookmarks' not in st.session_state:
    st.session_state.bookmarks = []

# Function to save bookmarks
def save_bookmark(item, item_type="article"):
    bookmark = {
        "type": item_type,
        "title": item.get("title", item.get("question", "Untitled")),
        "content": item.get("content", item.get("answer", "")),
        "url": item.get("url", ""),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": item.get("category", "Bookmark"),
        "topics": item.get("topics", [])
    }
    st.session_state.bookmarks.append(bookmark)

# Function to remove bookmark
def remove_bookmark(index):
    st.session_state.bookmarks.pop(index)

# Main app content
with st.sidebar:
    st.title("🚀 Tech Insight")
    
    # Refresh Button
    if st.button("🔄 Refresh All", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # About Section in Expander
    with st.expander("ℹ️ About Tech Insight", expanded=False):
        st.markdown("""
        **Tech Insight** is your one-stop destination for the latest in technology news and trends.
        
        **Features:**
        - 📰 Latest tech news and updates
        - 🤖 AI-powered news analysis
        - 📚 Academic research papers
        - ⌛ Tech timelines and history
        - 🔖 Save and organize your interests
        
        **Stay informed about:**
        - Artificial Intelligence
        - Emerging Technologies
        - Industry Trends
        - Research Breakthroughs
        - Tech Innovations
        """)
        
        # Version Info
        st.caption("Version 1.0.0 | Made with ❤️")

# Initialize session state for tab selection
if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = "📰 Latest News"

# -------- Tabs --------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📰 Latest News", 
    "🔥 Tech Talker", 
    "📚 Academic Papers",
    "⌛ Tech Timeline",
    "💻 Hacker News",
    "🔖 Bookmarks"
    
])

# -------- Render Selected Tab --------
with tab1:
    render_news_tab()
with tab2:
    techtalker_tab()
with tab3:
    render_academic_papers_tab()
with tab4:
    techtimeline_tab()
with tab5:
    render_hacker_news_tab()
with tab6:
    render_bookmarks_tab() 

