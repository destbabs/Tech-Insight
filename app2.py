import streamlit as st
import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timedelta
import arxiv
from bs4 import BeautifulSoup
from summarizer import summarize_text
from components.bookmarks import save_bookmark

# Cache the arXiv search results
@st.cache_data(ttl=3600)  # Cache for 1 hour
def search_arxiv(query, max_results=10):
    """Search arXiv with retry logic."""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Construct the API URL
            base_url = 'http://export.arxiv.org/api/query'
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            # Add headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Make the request
            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                return None

# Cache the arXiv papers fetching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_arxiv_papers(max_results=10, days_back=7):
    """Fetch recent papers from arXiv with retry logic."""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Create search query
            search = arxiv.Search(
                query="cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.CV",
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in search.results():
                try:
                    # Get paper details
                    paper = {
                        "title": result.title,
                        "authors": [author.name for author in result.authors],
                        "abstract": result.summary,
                        "url": result.entry_id,
                        "pdf_link": result.pdf_url,
                        "date": result.published.strftime("%Y-%m-%d"),
                        "category": "Academic Paper",
                        "topics": [cat.split('.')[-1] for cat in result.categories],
                        "content": result.summary  # Using abstract as content for now
                    }
                    papers.append(paper)
                except Exception as e:
                    st.warning(f"Error processing paper {result.title}: {str(e)}")
                    continue
                    
            return papers
            
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                st.error(f"Failed to fetch papers after {max_retries} attempts: {str(e)}")
                return []

def save_bookmark(paper, item_type="academic_paper"):
    # Initialize bookmarks if not exists
    if 'bookmarks' not in st.session_state:
        st.session_state.bookmarks = []
        
    # Create a minimal bookmark first
    bookmark = {
        "type": item_type,
        "title": paper['title'],
        "url": paper['link'],
        "pdf_link": paper.get('pdf_link'),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": "Academic Paper",
        "authors": paper['authors'],
        "paper_id": paper['link'].split('/')[-1]  # Store paper ID for later content fetching
    }
    
    # Add to bookmarks immediately
    st.session_state.bookmarks.append(bookmark)
    st.success("Paper bookmarked successfully!")

def render_academic_papers_tab():
    # App title and description
    st.title("📚 Academic Research Paper Search")
    st.markdown("### Search for academic papers from arXiv by entering a topic or keyword")
    st.markdown("---")

    # Search input
    search_query = st.text_input("Enter a topic or keyword:", placeholder="e.g artificial intelligence")

    # Search button
    search_button = st.button("🔍 Search Papers")

    # Function to parse XML response from arXiv
    def parse_arxiv_response(xml_response):
        if xml_response is None:
            return []
        
        try:
            # Parse the XML
            root = ET.fromstring(xml_response)
            
            # Define namespace
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            
            # Extract entries
            entries = root.findall('atom:entry', namespace)
            
            results = []
            for entry in entries:
                # Skip if this is the OpenSearch entry
                if entry.find('atom:id', namespace).text.startswith('http://arxiv.org/api/'):
                    continue
                    
                # Extract paper details
                paper = {
                    'title': entry.find('atom:title', namespace).text.strip(),
                    'authors': [author.find('atom:name', namespace).text for author in entry.findall('atom:author', namespace)],
                    'summary': entry.find('atom:summary', namespace).text.strip(),
                    'link': entry.find('atom:id', namespace).text,
                    'pdf_link': next((link.get('href') for link in entry.findall('atom:link', namespace) 
                                    if link.get('title') == 'pdf'), None)
                }
                results.append(paper)
            
            return results
            
        except Exception as e:
            return []

    # Search and display results when button is clicked
    if search_button and search_query:
        with st.spinner("Searching for papers..."):
            # Fetch papers from arXiv
            xml_response = search_arxiv(search_query)
            papers = parse_arxiv_response(xml_response)
            
            # Display results
            if papers:
                st.success(f"Found {len(papers)} papers related to '{search_query}'")
                st.markdown("---")
                
                # Display each paper in a clean layout
                for i, paper in enumerate(papers):
                    with st.expander(f"📄 {paper['title']}"):
                        # Authors
                        st.markdown(f"**🧑‍🔬 Authors:** {', '.join(paper['authors'])}")
                        
                        # Abstract
                        st.markdown("**📝 Abstract:**")
                        st.markdown(paper['summary'])
                        
                        # Links and Bookmark
                        col1, col2, col3 = st.columns([0.4, 0.4, 0.2])
                        with col1:
                            st.markdown(f"[🔗 View on arXiv]({paper['link']})")
                        with col2:
                            if paper['pdf_link']:
                                st.markdown(f"[📑 Download PDF]({paper['pdf_link']})")
                        with col3:
                            if st.button("🔖 Bookmark", key=f"bookmark_{i}"):
                                save_bookmark(paper)
                    
                    # Add a separator between papers
                    if i < len(papers) - 1:
                        st.markdown("---")
            else:
                st.warning(f"No papers found for '{search_query}'. Try a different search term.")

    # Footer
    st.markdown("---")
    st.markdown("Powered by arXiv API")
