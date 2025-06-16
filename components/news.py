import time
import streamlit as st
import time
from scraper import get_latest_news
from summarizer import summarize_text
from components.bookmarks import save_bookmark

# Cache the news fetching for 1 hour
@st.cache_data(ttl=3600, show_spinner="Fetching articles...")
def fetch_articles():
    try:
        return get_latest_news()
    except Exception as e:
        st.error(f"Failed to fetch articles: {str(e)}")
        return []

# Cache summaries for 24 hours since they don't change
@st.cache_data(ttl=86400)
def get_cached_summary(content):
    try:
        return summarize_text(content)
    except Exception as e:
        return f"Could not summarize: {str(e)}"

def render_news_tab():
    """Render the latest news tab."""
    st.title("📰 Tech News Hub")
    
    # Fetch Articles
    articles = fetch_articles()

    # Extract Filters
    categories = sorted({a["category"] for a in articles if a["category"] != "Unknown"})
    all_topics = sorted({topic for a in articles for topic in a["topics"] if topic != "topic not available"})

    # Initialize session state for filters
    if "category_filter" not in st.session_state:
        st.session_state.category_filter = "All"
    if "topic_filter" not in st.session_state:
        st.session_state.topic_filter = "All"

    # Sidebar Filters
    filter_expand = st.expander("Filters", icon="🔎")
    if filter_expand.button("🔁 Reset Filters"):
        st.session_state.category_filter = "All"
        st.session_state.topic_filter = "All"
        st.rerun()
    
    selected_category = filter_expand.selectbox(
        "Filter by Category", ["All"] + categories, key="category_filter"
    )

    selected_topic = filter_expand.selectbox(
        "Filter by Topic", ["All"] + all_topics, key="topic_filter"
    )

    # Filter Articles
    def article_matches_filters(article):
        if selected_category != "All" and article["category"] != selected_category:
            return False
        if selected_topic != "All" and selected_topic not in article["topics"]:
            return False
        return True

    filtered_articles = [a for a in articles if article_matches_filters(a)]

    # Show Articles
    st.markdown(f"### Showing {len(filtered_articles)} article(s)")

    if not filtered_articles:
        st.warning("No articles match your filters.")

    for a in filtered_articles[:len(filtered_articles)]:
        st.markdown("---")  
        st.markdown(f"## 🎯 {a['title']}")
        st.markdown(f"**Date:** {a['date']}  |  **Author:** {a['author']}  |  **Category:** {a['category']}")
        st.markdown(f"[Read on TechCrunch]({a['url']})")
        st.markdown("...")
        try:
            # Use cached summary
            summary = get_cached_summary(a['content'])
            st.markdown(f"{summary}")
        except Exception as e:
            st.warning(f"Could not summarize article: {str(e)}")
        st.markdown(f"**Topics:** {', '.join(a['topics'])}")
        
        # Add bookmark button
        if st.button("🔖 Bookmark", key=f"bookmark_{a['title']}"):
            save_bookmark(a)
            st.success("Article bookmarked!")
        
        with st.spinner("Loading.."):
            time.sleep(0.9) 