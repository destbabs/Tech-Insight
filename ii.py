import requests
from bs4 import BeautifulSoup
import time
import streamlit as st
from summarizer import summarize_text
from urllib.parse import urljoin

# Cache the Hacker News items fetching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_hacker_news_items():
    base_url = 'https://news.ycombinator.com/'
    response = requests.get(base_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.select('.athing')
    
    processed_items = []
    for item in items:
        title_tag = item.select_one('.titleline a')
        if title_tag:
            title = title_tag.text.strip()
            link = title_tag['href']
            if link.startswith('item?id='):
                link = urljoin(base_url, link)
            processed_items.append({
                'title': title,
                'link': link
            })
    return processed_items

# Cache article content fetching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_article_content(url):
    try:
        article_resp = requests.get(url, timeout=10)
        article_resp.raise_for_status()
        article_soup = BeautifulSoup(article_resp.text, 'html.parser')
        paragraphs = article_soup.find_all('p')
        return '\n'.join(p.get_text(strip=True) for p in paragraphs)
    except Exception as e:
        return None

def render_hacker_news_tab():
    st.header("Articles")
    
    # Initialize session state for pagination if not exists
    if 'hacker_news_page' not in st.session_state:
        st.session_state.hacker_news_page = 0
    
    # Fetch items with caching
    items = fetch_hacker_news_items()
    
    # Calculate start and end indices for current page
    start_idx = st.session_state.hacker_news_page * 10
    end_idx = start_idx + 10
    current_items = items[start_idx:end_idx]
    
    # Create a container for the articles
    articles_container = st.container()
    
    # Display current page items
    with articles_container:
        for item in current_items:
            with st.expander(f"{start_idx + current_items.index(item) + 1}. {item['title']}", expanded=False):
                st.markdown(f"[Read full article]({item['link']})")
                
                # Add a button to load content
                if st.button("Load Summary", key=f"load_{item['link']}"):
                    content = fetch_article_content(item['link'])
                    
                    if content:
                        with st.spinner('Generating summary...'):
                            summary = summarize_text(content)
                            st.markdown("### Summary")
                            st.write(summary)
                    else:
                        st.warning("No content could be extracted from this article.")
    
    # Navigation buttons in columns
    col1, col2 = st.columns([1, 1])
    
    # Add Previous button if not on first page
    with col1:
        if st.session_state.hacker_news_page > 0:
            if st.button("← Previous 10 Articles"):
                st.session_state.hacker_news_page -= 1
                st.rerun()
    
    # Add Next button if there are more items
    with col2:
        if end_idx < len(items):
            if st.button("Next 10 Articles →"):
                st.session_state.hacker_news_page += 1
                st.rerun()
