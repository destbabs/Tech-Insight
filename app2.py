import streamlit as st
import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timedelta
import arxiv
from bs4 import BeautifulSoup
from summarizer import summarize_text
from components.bookmarks import save_bookmark
import re

# Cache the arXiv search results
@st.cache_data(ttl=3600)  # Cache for 1 hour
def search_arxiv(query, max_results=10, search_type="all"):
    """Search arXiv with improved query construction and retry logic."""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Clean and format the query
            query = query.strip()
            
            # Construct different search queries based on search type
            if search_type == "title":
                search_query = f'ti:"{query}"'
            elif search_type == "abstract":
                search_query = f'abs:"{query}"'
            elif search_type == "author":
                search_query = f'au:"{query}"'
            elif search_type == "category":
                # Map common terms to arXiv categories
                category_map = {
                    "ai": "cs.AI", "artificial intelligence": "cs.AI",
                    "machine learning": "cs.LG", "ml": "cs.LG",
                    "computer vision": "cs.CV", "cv": "cs.CV",
                    "nlp": "cs.CL", "natural language": "cs.CL",
                    "robotics": "cs.RO", "robots": "cs.RO",
                    "data science": "cs.LG", "deep learning": "cs.LG",
                    "neural networks": "cs.LG", "reinforcement learning": "cs.LG"
                }
                query_lower = query.lower()
                if query_lower in category_map:
                    search_query = f'cat:{category_map[query_lower]}'
                else:
                    search_query = f'cat:{query}'
            else:  # "all" - search in title, abstract, and keywords
                # Use OR to search in multiple fields for better relevance
                search_query = f'ti:"{query}" OR abs:"{query}" OR all:"{query}"'
            
            # Construct the API URL
            base_url = 'http://export.arxiv.org/api/query'
            params = {
                'search_query': search_query,
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',  # Changed from submittedDate to relevance
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

def calculate_relevance_score(paper, query):
    """Calculate relevance score based on query terms in title and abstract."""
    query_terms = query.lower().split()
    title_lower = paper['title'].lower()
    summary_lower = paper['summary'].lower()
    
    score = 0
    
    for term in query_terms:
        # Higher weight for title matches
        if term in title_lower:
            score += 3
        # Medium weight for abstract matches
        if term in summary_lower:
            score += 1
        # Bonus for exact phrase matches
        if query.lower() in title_lower:
            score += 5
        if query.lower() in summary_lower:
            score += 2
    
    return score

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
    """Save a paper to bookmarks with optimized performance."""
    try:
        # Initialize bookmarks if not exists
        if 'bookmarks' not in st.session_state:
            st.session_state.bookmarks = []
        
        # Check if bookmark already exists to prevent duplicates
        for existing in st.session_state.bookmarks:
            if existing.get('url') == paper.get('link'):
                st.warning("This paper is already bookmarked!")
                return False
        
        # Create bookmark with all necessary data
        bookmark = {
            "type": item_type,
            "title": paper['title'],
            "content": paper.get('summary', ''),  # Include abstract as content
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
        return True
        
    except Exception as e:
        st.error(f"Error saving bookmark: {str(e)}")
        return False

def render_academic_papers_tab():
    # App title and description
    st.title("📚 Academic Research Paper Search")
    st.markdown("### Search for academic papers from arXiv by entering a topic or keyword")
    st.markdown("---")

    # Cache control
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ Clear Cache", help="Clear cached results to get fresh papers"):
            st.cache_data.clear()
            st.success("Cache cleared! Search again for fresh results.")
            st.rerun()

    # Search configuration
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input("Enter a topic or keyword:", placeholder="e.g artificial intelligence")
    
    with col2:
        search_type = st.selectbox(
            "Search in:",
            ["all", "title", "abstract", "author", "category"],
            help="Choose where to search for your query"
        )
    
    with col3:
        max_results = st.selectbox(
            "Max results:",
            [5, 10, 15, 20],
            index=1,
            help="Maximum number of papers to return"
        )
        # Search tips
    with st.expander("💡 Search Tips", expanded=False):
        st.markdown("""
        **For better results:**
        - Use specific keywords (e.g., "transformer" instead of "AI")
        - Try searching in "title" for exact matches
        - Use "category" search for broad topics like "machine learning" or "computer vision"
        - Combine multiple terms with quotes: "deep learning" "computer vision"
        - Use author names in "author" search mode
        
        **Common categories:**
        - cs.AI: Artificial Intelligence
        - cs.LG: Machine Learning
        - cs.CV: Computer Vision
        - cs.CL: Natural Language Processing
        - cs.RO: Robotics
        """)
    # Search button
    search_button = st.button("🔍 Search Papers", use_container_width=True)
    
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
            st.error(f"Error parsing arXiv response: {str(e)}")
            return []

    # Search and display results when button is clicked
    if search_button and search_query:
        with st.spinner("Searching for papers..."):
            try:
                # Fetch papers from arXiv
                xml_response = search_arxiv(search_query, max_results, search_type)
                
                if xml_response is None:
                    st.error("Failed to fetch papers from arXiv. Please try again later.")
                    return
                
                papers = parse_arxiv_response(xml_response)
                
                # Calculate relevance scores and sort results
                if papers:
                    for paper in papers:
                        paper['relevance_score'] = calculate_relevance_score(paper, search_query)
                    
                    # Sort by relevance score (highest first)
                    papers.sort(key=lambda x: x['relevance_score'], reverse=True)
                    
                    # Filter out papers with very low relevance (score < 1)
                    relevant_papers = [p for p in papers if p['relevance_score'] >= 1]
                    
                    if relevant_papers:
                        st.success(f"Found {len(relevant_papers)} relevant papers for '{search_query}'")
                        st.markdown("---")
                        
                        # Display each paper in a clean layout
                        for i, paper in enumerate(relevant_papers):
                            with st.expander(f"📄 {paper['title']} (Relevance: {paper['relevance_score']})"):
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
                            if i < len(relevant_papers) - 1:
                                st.markdown("---")
                    else:
                        st.warning(f"No relevant papers found for '{search_query}'. Try a different search term or search type.")
                else:
                    st.warning(f"No papers found for '{search_query}'. Try a different search term.")
                    
            except Exception as e:
                st.error(f"An error occurred while searching: {str(e)}")
                st.info("Try clearing the cache and searching again.")



    # Footer
    st.markdown("---")
    st.markdown("Powered by arXiv API")
