# Tech Insight

A Streamlit application that scrapes and displays tech update with AI-powered summarization and bookmarking capabilities.

## Project Structure

```
Tech-News/
├── components/              # UI components
│   ├── __init__.py
│   ├── bookmarks.py        # Bookmarks functionality
│   └── news.py            # News display functionality
├── main.py                 # Main application file
├── aiscraper.py           # AI-powered news scraping
├── scraper.py             # Basic news scraping
├── summarizer.py          # Text summarization
└── requirements.txt       # Project dependencies
```

## Features

- 📰 Latest tech news from TechCrunch
- 🤖 AI-powered article summarization
- 🔖 Bookmarking system for articles and AI responses
- 🔍 Filtering and sorting capabilities
- 🎯 Topic-based filtering
- 📱 Responsive design

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env`:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```
4. Run the application:
   ```bash
   streamlit run main.py
   ```

## Components

- **News Tab**: Displays latest tech news with filtering and summarization
- **Tech Talker**: AI-powered news analysis and discussion
- **Bookmarks**: Save and organize your favorite articles and AI responses

## Dependencies

- Streamlit
- BeautifulSoup4
- LangChain
- Google Generative AI
- DuckDuckGo Search 
