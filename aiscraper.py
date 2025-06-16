import time
import streamlit as st
from duckduckgo_search import DDGS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from datetime import datetime
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_community.tools import  DuckDuckGoSearchRun
from langchain.agents import initialize_agent, Tool, AgentType
from dotenv import load_dotenv
import os

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Initialize session state for bookmarks if not exists
if 'bookmarks' not in st.session_state:
    st.session_state.bookmarks = []

# Function to save bookmarks
def save_bookmark(item, item_type="techtalker"):
    bookmark = {
        "type": item_type,
        "title": item.get("title", item.get("question", "Untitled")),
        "content": item.get("content", item.get("answer", "")),
        "url": item.get("url", ""),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": item.get("category", "Tech Talker"),
        "topics": item.get("topics", [])
    }
    st.session_state.bookmarks.append(bookmark)

# st.set_page_config(page_title="AI News Processor", page_icon="🖥️")
# tab1, tab2,tab3 = st.tabs(["🧑‍💻 TechTalker", "⌛ Timeline","📃Events"])

def search(topic):
    with DDGS() as ddg:
        results = ddg.text(f"{topic} news {datetime.now().strftime('%Y-%m')}", max_results=3)
        if results:
            return "\n\n".join([
                f"Title: {result['title']}\nURL: {result['href']}\nSummary: {result['body']}"
                for result in results
            ])
        return f"No news found for {topic}."

# Add caching for better performance
@st.cache_data(ttl=3600)  # Cache for 1 hour
def cached_search(topic):
    return search(topic)

# === TechTalker Tab ===
def techtalker_tab():
    st.title("🧑‍💻 TechTalker")

    tech_prompt = PromptTemplate(
        input_variables=["raw_news", "topic", "engagement", "length"],
        template="""
You are a knowledgeable, engaging tech news, blog, article, conference expert creating a detailed explainer about "{topic}" based on the raw news below.

Instructions:
1. Cover all major announcements, developments, and key details.
2. Include important stakeholders (companies, people) and their roles.
3. Summarize the background and context so the reader understands why this topic is significant.
4. Include actual quotes and specific data from sources or tech giants.
5. Clarify technical terms simply.
6. Organize your response clearly with paragraphs or numbered points.
7. Adjust your tone to be {engagement}/10 on a fun, playful scale — more means livelier and more emojis.
8. The report should be about {length} words long — more words for deeper details.
9. Provide a self-contained explanation assuming no prior knowledge.
10. Do NOT include filler phrases or meta-comments.
11. Respond in markdown format with headings, bullet points, and emojis where appropriate.
12. Relate the topic to current trends or future implications in the tech industry.
13. No matter the subject always relate it to technology and computing.
14. Extract difficult domain-specific terms from the text and explain them simply for a beginner.
provide link for further reading if available
Raw news input:
{raw_news}
"""
    )

    tech_chain = LLMChain(llm=llm, prompt=tech_prompt)

    def process_tech_news(topic, engagement, length):
        news = cached_search(topic)
        return tech_chain.run(raw_news=news, topic=topic, engagement=engagement, length=length)

    topic_input = st.text_input("Enter  topic:", placeholder="e.g artificial intelligence")
    expand = st.expander("⚙️ Settings", expanded=False)
    engagement_level = expand.slider("Tone Playfulness (Fun Level)", 0, 10, 5, key="engagement_slider")
    length_words = expand.slider("Report Length (Words)", 200, 800, 500, step=50, key="length_slider")

    # Initialize session state for the current response
    if 'current_techtalker_response' not in st.session_state:
        st.session_state.current_techtalker_response = None

    if st.button("🧠 Generate Explainer", type="primary"):
        if topic_input.strip():
            with st.spinner("Processing..."):
                output = process_tech_news(topic_input, engagement_level, length_words)
                st.session_state.current_techtalker_response = {
                    "title": f"Tech Talker: {topic_input}",
                    "content": output,
                    "question": topic_input,
                    "topics": [topic_input]
                }
                st.header(f"📝 About: {topic_input}")
                st.markdown(output)
        else:
            st.error("Please enter a topic!")

    # Show bookmark button only if there's a current response and it's not empty
    if st.session_state.current_techtalker_response and st.session_state.current_techtalker_response.get("content"):
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            if st.button("🔖 Bookmark This Response", key="bookmark_techtalker"):
                save_bookmark(st.session_state.current_techtalker_response, "techtalker")
                st.success("Response bookmarked!")
                # Clear the current response after bookmarking
                st.session_state.current_techtalker_response = None
                st.rerun()

def techtimeline_tab():
    st.title("⌛Discover Timeline")

    timeline_prompt = PromptTemplate(
        input_variables=["text", "topic", "engagement", "length"],
        template="""
You are a tech historian and futurist assistant.

Using  news content,blogs, articles, and any valuabe source , generate a clear, engaging timeline of the topic "{topic}" including:

- 📜 Key historical events or milestones
- ⚡ Recent updates or changes
- 🔮 Reasonable predictions about where it's going
- 🏆 For each key topic mentioned, include their major tech achievements or products during those years 
Format the timeline in markdown with:
- Date (approximate is okay)
- Event summary
- Emojis if helpful
- Keep it fun, factual, and informative
- Use a tone that is {engagement}/10 on a fun, playful scale — more means livelier and more emojis.
- The report should be about {length} words long — more words for deeper details.
- Separate sections or bullet points for topic achievements
- add product history for each topic mentioned in the news
provide link for further reading if available


News content:
{text}
"""
    )

    timeline_chain = LLMChain(llm=llm, prompt=timeline_prompt)

    def process_event_news(topic, engagement, length):
        news = cached_search(topic)
        return timeline_chain.run(text=news, topic=topic,engagement=engagement, length=length)

    timeline_input = st.text_input("Enter timeline topic:", placeholder="e.g artificial intelligence", key="timeline_topic_input")
    expand2 = st.expander("⚙️ Settings", expanded=False)
    timeline_engagement=expand2.slider("Tone Playfulness (Fun Level)", 0, 10, 5, key="timeline_engagement")
    timeline_length=expand2.slider("Timeline Depth (Not Used)", 200, 800, 500, step=50, key="timeline_length")

    # Initialize session state for the current response
    if 'current_timeline_response' not in st.session_state:
        st.session_state.current_timeline_response = None

    if st.button("📅 Generate Timeline", type="secondary"):
        if timeline_input.strip():
            with st.spinner("Generating timeline..."):
                timeline_output = process_event_news(timeline_input, timeline_engagement, timeline_length)
                st.session_state.current_timeline_response = {
                    "title": f"Tech Timeline: {timeline_input}",
                    "content": timeline_output,
                    "question": timeline_input,
                    "topics": [timeline_input],
                    "type": "timeline"
                }
                st.header(f"📅 Timeline for: {timeline_input}")
                st.markdown(timeline_output)
        else:
            st.error("Please enter a topic!")

    # Show bookmark button only if there's a current response
    if st.session_state.current_timeline_response and st.session_state.current_timeline_response.get("content"):
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            if st.button("🔖 Bookmark This Timeline", key="bookmark_timeline"):
                save_bookmark(st.session_state.current_timeline_response, "timeline")
                st.success("Timeline bookmarked!")
                # Clear the current response after bookmarking
                st.session_state.current_timeline_response = None
                st.rerun()