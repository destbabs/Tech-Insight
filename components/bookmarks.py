import streamlit as st
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from summarizer import summarize_text

def save_bookmark(item, item_type="article"):
    """Save an item to bookmarks."""
    try:
        # Initialize bookmarks if not exists
        if 'bookmarks' not in st.session_state:
            st.session_state.bookmarks = []
            
        # Check if bookmark already exists
        for existing in st.session_state.bookmarks:
            if existing.get('url') == item.get('url'):
                st.warning("This item is already bookmarked!")
                return False
                
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
        return True
    except Exception as e:
        st.error(f"Error saving bookmark: {str(e)}")
        return False

def remove_bookmark(bookmark):
    """Remove a bookmark from session state."""
    try:
        if 'bookmarks' in st.session_state:
            st.session_state.bookmarks.remove(bookmark)
            return True
        return False
    except Exception as e:
        st.error(f"Error removing bookmark: {str(e)}")
        return False

# Cache article content fetching for 24 hours since content rarely changes
@st.cache_data(ttl=86400)
def fetch_article_content(url):
    """Fetch and cache article content."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        article_resp = requests.get(url, headers=headers, timeout=10)
        article_resp.raise_for_status()
        article_soup = BeautifulSoup(article_resp.text, 'html.parser')
        paragraphs = article_soup.find_all('p')
        return '\n'.join(p.get_text(strip=True) for p in paragraphs)
    except Exception as e:
        return None

# Cache summaries for 24 hours since they don't change
@st.cache_data(ttl=86400)
def get_cached_summary(content):
    """Get cached summary of content."""
    try:
        return summarize_text(content)
    except Exception as e:
        return f"Could not summarize: {str(e)}"

def render_bookmarks_tab():
    st.title("🔖 Bookmarks")
    
    # Initialize bookmarks if not exists
    if 'bookmarks' not in st.session_state:
        st.session_state.bookmarks = []
    
    if not st.session_state.bookmarks:
        st.info("No bookmarks yet. Start bookmarking articles, papers, or responses to see them here!")
        return
    
    # Add clear all button
    if st.button("🗑️ Clear All Bookmarks", type="primary"):
        if st.session_state.bookmarks:
            st.session_state.bookmarks = []
            st.success("All bookmarks cleared!")
            st.rerun()
    
    # Group bookmarks by type
    bookmarks_by_type = {}
    for bookmark in st.session_state.bookmarks:
        bookmark_type = bookmark.get('type', 'unknown')
        if bookmark_type not in bookmarks_by_type:
            bookmarks_by_type[bookmark_type] = []
        bookmarks_by_type[bookmark_type].append(bookmark)
    
    # Display bookmarks by type
    for bookmark_type, bookmarks in bookmarks_by_type.items():
        # Format the type name for display
        type_display = bookmark_type.replace('_', ' ').title()
        st.subheader(f"📚 {type_display}")
        
        for idx, bookmark in enumerate(bookmarks):
            with st.expander(f"📌 {bookmark['title']}", expanded=False):
                # Display common fields
                st.markdown(f"**Date:** {bookmark.get('date', 'N/A')}")
                
                # Display type-specific content
                if bookmark_type == 'academic_paper':
                    # Display authors if available
                    if 'authors' in bookmark:
                        st.markdown(f"**Authors:** {', '.join(bookmark['authors'])}")
                    
                    # Add a button to load content
                    if st.button("📝 Load Abstract", key=f"load_abstract_{idx}"):
                        with st.spinner("Loading abstract..."):
                            content = fetch_article_content(bookmark['url'])
                            if content:
                                summary = get_cached_summary(content)
                                st.markdown("**Abstract:**")
                                st.markdown(summary)
                            else:
                                st.warning("Could not load abstract.")
                    
                    # Display links
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"[🔗 View Paper]({bookmark['url']})")
                    if bookmark.get('pdf_link'):
                        with col2:
                            st.markdown(f"[📑 Download PDF]({bookmark['pdf_link']})")
                
                elif bookmark_type == 'timeline':
                    st.markdown("**Timeline Content:**")
                    st.markdown(bookmark['content'])
                    if bookmark.get('url'):
                        st.markdown(f"[🔗 Read More]({bookmark['url']})")
                
                elif bookmark_type == 'techtalker':
                    st.markdown(bookmark['content'])
                    if bookmark.get('url'):
                        st.markdown(f"[🔗 Read More]({bookmark['url']})")
                
                else:  # Default display for other types
                    st.markdown(bookmark['content'])
                    if bookmark.get('url'):
                        st.markdown(f"[🔗 Read More]({bookmark['url']})")
                
                # Add remove button with confirmation
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🗑️ Remove", key=f"remove_{bookmark_type}_{idx}", type="secondary"):
                        if remove_bookmark(bookmark):
                            st.success("Bookmark removed!")
                            st.rerun()
            
            # Add separator between bookmarks
            if idx < len(bookmarks) - 1:
                st.markdown("---") 