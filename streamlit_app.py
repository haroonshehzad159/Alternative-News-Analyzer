import streamlit as st
import processor 
import spacy
import time 


st.set_page_config(
    page_title="Alternative News Analyzer",
    page_icon="📰",
    layout="wide" 
)


@st.cache_resource
def load_models_and_setup():
    print("Performing one-time setup of NLP models...")
    processor.setup_nltk()
    try:
        spacy.load("en_core_web_sm")
        print("spaCy model 'en_core_web_sm' is already available.")
    except OSError:
        print("spaCy model not found. Downloading 'en_core_web_sm'...")
        spacy.cli.download("en_core_web_sm")
        print("spaCy model downloaded successfully.")
    return True

load_models_and_setup()


st.markdown("""
<style>
    /* General Styling */
    .stApp {
        background-color: #f0f2f5;
    }
    .st-emotion-cache-17nzaf5 { /* Specific class for Streamlit's container border */
        border-color: #CBD5E0;
        border-radius: 0.75rem;
    }
    h1, h2, h3 {
        font-weight: 600;
    }
    /* Style for the input box */
    div[data-testid="stTextInput"] input {
        border-color: #CBD5E0;
        transition: border-color 0.3s ease-in-out;
    }
    /* Style for the input box when it's being used or focused */
    div[data-testid="stTextInput"] input:focus {
        border-color: #E53E3E; /* Red outline on focus as requested */
        box-shadow: 0 0 0 1px #E53E3E;
    }
</style>
""", unsafe_allow_html=True)



if 'stage' not in st.session_state:
    st.session_state.stage = 'input'


def display_sentiment_card(sentiment_scores):
    """A reusable function to display fully colorful sentiment scores."""
    if not sentiment_scores:
        st.info("Sentiment could not be analyzed.")
        return

    
    neg_color = f"rgba(229, 62, 62, {sentiment_scores['neg'] * 2 + 0.15})"
    neu_color = f"rgba(113, 128, 144, {sentiment_scores['neu'] * 0.7 + 0.15})"
    pos_color = f"rgba(56, 178, 172, {sentiment_scores['pos'] * 2 + 0.15})"
    
    comp_val = sentiment_scores['compound']
    if comp_val >= 0.05: comp_bg = "rgba(56, 178, 172, 0.2)"
    elif comp_val <= -0.05: comp_bg = "rgba(229, 62, 62, 0.2)"
    else: comp_bg = "rgba(113, 128, 144, 0.1)"

    st.markdown(f"""
    <div style="display: flex; justify-content: space-around; text-align: center; gap: 10px; margin-top: 10px; padding: 10px;">
        <div style="background-color: {neg_color}; border-radius: 8px; padding: 10px; flex-grow: 1; color: #333;">
            <div style="font-size: 0.9em;">Negative</div><div style="font-size: 1.5em; font-weight: 600;">{sentiment_scores['neg']:.3f}</div>
        </div>
        <div style="background-color: {neu_color}; border-radius: 8px; padding: 10px; flex-grow: 1; color: #333;">
            <div style="font-size: 0.9em;">Neutral</div><div style="font-size: 1.5em; font-weight: 600;">{sentiment_scores['neu']:.3f}</div>
        </div>
        <div style="background-color: {pos_color}; border-radius: 8px; padding: 10px; flex-grow: 1; color: #333;">
            <div style="font-size: 0.9em;">Positive</div><div style="font-size: 1.5em; font-weight: 600;">{sentiment_scores['pos']:.3f}</div>
        </div>
        <div style="background-color: {comp_bg}; border-radius: 8px; padding: 10px; flex-grow: 1; color: #333;">
            <div style="font-size: 0.9em;">Compound</div><div style="font-size: 1.5em; font-weight: 600;">{sentiment_scores['compound']:.3f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def start_new_analysis():
    st.session_state.stage = 'input'
    keys_to_clear = ['url', 'original_article', 'topics', 'alternatives', 'error']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()



# SHOW THE INPUT SCREEN
if st.session_state.stage == 'input':
    # Use columns to create a more centered input area within the wide layout
    left_co, main_co, right_co = st.columns([1, 2, 1])
    with main_co:
        st.title("📰 Alternative News Analyzer")
        st.markdown("Enter the URL of a news article to discover different perspectives. This tool will analyze its core topics and sentiment, then find related articles from a variety of sources.")
        
        url_input = st.text_input("Enter News Article URL", placeholder="https://www.bbc.com/news/...", key="url_input_box")
        
        # Button is sized to content, not full width
        if st.button('Analyze Article', type="primary"):
            if url_input:
                st.session_state.url = url_input
                st.session_state.stage = 'processing'
                st.rerun()
            else:
                st.warning("Please enter a URL to analyze.")


# SHOW THE PROCESSING SCREEN
elif st.session_state.stage == 'processing':
    st.title("🔍 Analyzing Article...")
    
    # Create placeholders for the progress bar and the status log
    progress_bar = st.progress(0, text="Initializing...")
    status_log = st.empty()
    
    log_messages = []

    # Fetching
    log_messages.append("1. Fetching the article content...")
    status_log.info("\n".join(log_messages))
    title, raw_text = processor.fetch_article_text(st.session_state.url)
    time.sleep(1)
    
    if not raw_text:
        st.error("Could not fetch the article. The URL might be invalid, or the site may be blocking access.")
        if st.button("Try Another Article", type="primary"):
            start_new_analysis()
        st.stop() 

    log_messages.append(f"✅ Fetching complete: **{title}**")
    status_log.info("\n".join(log_messages))
    progress_bar.progress(25, text="Fetching complete...")

    # Main Analysis
    log_messages.append("\n2. Analyzing topics and sentiment...")
    status_log.info("\n".join(log_messages))
    st.session_state.original_article = {'title': title, 'sentiment': processor.analyze_sentiment_from_text(raw_text)}
    st.session_state.topics = processor.analyze_topics_from_text(raw_text)
    time.sleep(1)
    log_messages.append("✅ Analysis of original article complete!")
    status_log.info("\n".join(log_messages))
    progress_bar.progress(50, text="Main analysis complete...")
    
    # Searching
    log_messages.append("\n3. Searching for alternative articles...")
    status_log.info("\n".join(log_messages))
    alternatives = processor.find_alternative_articles(st.session_state.topics, raw_text)
    time.sleep(1)
    log_messages.append(f"✅ Search complete! Found {len(alternatives)} potential articles.")
    status_log.info("\n".join(log_messages))
    progress_bar.progress(75, text="Search complete...")
    
    # Analyzing Alternatives
    log_messages.append("\n4. Analyzing each alternative article...")
    status_log.info("\n".join(log_messages))
    processed_alternatives = []
    if alternatives:
        for i, article in enumerate(alternatives):
            _, alt_raw_text = processor.fetch_article_text(article['url'])
            if alt_raw_text:
                article['sentiment'] = processor.analyze_sentiment_from_text(alt_raw_text)
                article['description'] = alt_raw_text[:250] + "..."
                processed_alternatives.append(article)
    
    log_messages.append("✅ Analysis of alternative articles complete!")
    status_log.info("\n".join(log_messages))
    progress_bar.progress(100, text="Analysis Finished!")
    
    st.session_state.alternatives = processed_alternatives
    
    # The final "sparks" and redirect
    st.balloons()
    time.sleep(2)
    
    st.session_state.stage = 'results'
    st.rerun()
# SHOW THE RESULTS SCREEN
elif st.session_state.stage == 'results':
    st.title("📊 Analysis Results")
    
    with st.container(border=True):
        st.header("Original Article Analysis")
        st.subheader(st.session_state.original_article['title'])
        display_sentiment_card(st.session_state.original_article['sentiment'])
    
    st.header("Extracted Topics")
    if st.session_state.topics:
        for topic in st.session_state.topics:
            st.info(f"{', '.join(topic['keywords'])}")
    else:
        st.warning("No distinct topics could be extracted from this article.")
        
    st.header("Alternative Articles")
    if st.session_state.alternatives:
        for article in st.session_state.alternatives:
            with st.container(border=True):
                st.subheader(f"[{article['source']}] {article['title']}")
                if article.get('description'):
                    st.caption(article['description'])
                st.markdown(f"*[Read full article]({article['url']})* - Published: {article['publishedAt']}")
                display_sentiment_card(article['sentiment'])
    else:
        st.info("No alternative articles could be found for the extracted topics.")

    # Button is sized to content
    if st.button("Analyze Another Article", type="primary"):
        start_new_analysis()

# Error Stage
elif st.session_state.stage == 'error':
    st.error(st.session_state.error)
    if st.button("Try Again", type="primary"):
        start_new_analysis()