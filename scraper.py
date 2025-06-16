import datetime
import time
import requests
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry
from dateutil.parser import parse
from requests.adapters import HTTPAdapter
import random

def get_session():
    """This function creates a customized requests 
    session that automatically retries failed HTTP requests"""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=2,  # Increased backoff factor
        status_forcelist=[429, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_latest_news(max_articles=20):
    url = f"https://techcrunch.com/latest/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    }
    session = get_session()

    try:
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch main page: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find_all("a", class_="loop-card__title-link")[:max_articles]
    result = []

    for article in articles:
        article_url = article.get("href")
        article_title = article.get_text(strip=True)
        
        # Add random delay between requests (1-3 seconds)
        time.sleep(random.uniform(1, 3))
        
        try:
            article_response = session.get(article_url, headers=headers, timeout=15)
            article_response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch article: {article_url} - {e}")
            continue
            
        article_soup = BeautifulSoup(article_response.content, 'html.parser')

        try:
            author = article_soup.find("a", class_="wp-block-tc23-author-card-name__link").get_text(strip=True)
        except (AttributeError, TypeError):
            author = "Unknown"

        try:
            date = article_soup.find("time").get_text(strip=True)
        except (AttributeError, TypeError):
            date = "Unknown" 

        try:
            content_div = article_soup.find("div", class_="entry-content wp-block-post-content is-layout-constrained wp-block-post-content-is-layout-constrained")
            paragraphs = content_div.find_all("p")
            full_content = "\n".join([p.get_text(strip=True) for p in paragraphs])
        except (AttributeError, TypeError):
            full_content = "content not available"

        try:
            topic_list = []
            topics = article_soup.find("div", class_="tc23-post-relevant-terms__terms").find_all("a")
            for topic in topics:
                topic_list.append(topic.get_text(strip=True))
        except (AttributeError, TypeError):
            topic_list = ["topic not available"]
       
        try:
            category = article_soup.find("a", class_="is-taxonomy-category wp-block-tenup-post-primary-term").get_text(strip=True)
        except (AttributeError, TypeError):
            category = "Unknown"

        result.append({
            "title": article_title,
            "url": article_url,
            "author": author,
            "date": date,
            "category": category,
            "content": full_content,
            "topics": topic_list
        })

    return result




