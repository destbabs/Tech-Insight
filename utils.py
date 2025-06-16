import streamlit as st

def save_bookmark(item, item_type="article"):
    """Save an item to bookmarks in session state."""
    if 'bookmarks' not in st.session_state:
        st.session_state.bookmarks = []
        
    bookmark = {
        "type": item_type,
        "title": item.get("title", item.get("question", "Untitled")),
        "content": item.get("content", item.get("answer", "")),
        "url": item.get("url", ""),
        "date": item.get("date", ""),
        "category": item.get("category", "Bookmark"),
        "topics": item.get("topics", [])
    }
    st.session_state.bookmarks.append(bookmark)
    return True

def remove_bookmark(index):
    """Remove a bookmark from session state."""
    if 'bookmarks' in st.session_state and 0 <= index < len(st.session_state.bookmarks):
        st.session_state.bookmarks.pop(index)
        return True
    return False 