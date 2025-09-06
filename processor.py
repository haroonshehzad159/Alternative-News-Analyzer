import nltk
import os
import re
import requests
import spacy
from newspaper import Article
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP
from collections import Counter


def setup_nltk():
    """
    Downloads all necessary NLTK data if not present.
    This is a robust function that works on any operating system.
    """
    # Define a list of the resources we absolutely need
    required_resources = {
        "tokenizers/punkt": "punkt",
        "corpora/stopwords": "stopwords",
        "sentiment/vader_lexicon": "vader_lexicon",
        "corpora/wordnet": "wordnet" 
    }
    
    # Check for each resource, and download it if it's missing
    for resource_path, resource_name in required_resources.items():
        try:
            nltk.data.find(resource_path)
            print(f"NLTK resource '{resource_name}' found.")
        except LookupError:
            print(f"NLTK resource '{resource_name}' not found. Downloading...")
            nltk.download(resource_name)



print("Loading spaCy model...")
try:
    nlp = spacy.load("en_core_web_sm")
    print("spaCy model loaded successfully.")
except OSError:
    print("spaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'")
    nlp = None



def fetch_article_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        article = Article(url, headers=headers)
        article.download()
        article.parse()
        return article.title, article.text
    except Exception as e:
        print(f"Error fetching article from {url}: {e}")
        return None, None

def analyze_sentiment_from_text(text_content):
    if not text_content: return None
    analyzer = SentimentIntensityAnalyzer()
    return analyzer.polarity_scores(text_content)

def extract_key_entities(text_content):
    if not nlp or not text_content: return []
    doc = nlp(text_content[:100000])
    entities = []
    labels_of_interest = ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "LOC"]
    for ent in doc.ents:
        if len(ent.text) > 3 and not ent.text.islower() and ent.text.count(' ') < 4:
            entities.append(ent.text.strip())
    if not entities: return []
    entity_counts = Counter(entities)
    return [ent for ent, count in entity_counts.most_common(5)]

# DEFINITIVE ROBUST VERSION of analyze_topics_from_text
def analyze_topics_from_text(text_content):
    if not text_content or len(text_content.strip()) < 100:
        return None
        
    sentences = sent_tokenize(text_content)
    min_sentence_length = 15
    sentences = [s for s in sentences if len(s) > min_sentence_length]

    # Set a very low minimum, we will handle failure inside the try block
    if len(sentences) < 5: 
        print("Article too short for meaningful topic analysis.")
        return None

    try:
        
        custom_stopwords = list(stopwords.words('english'))
        custom_stopwords.extend([
            'said', 'says', 'told', 'news', 'bbc', 'cnn', 'reuters', 'like', 'just', 'good', 'really', 'mr', 'mrs', 'ms', 
            'year', 'years', 'ago', 'day', 'week', 'month', 'people', 'time', 'also', 'get', 'one', 'two', 'three',
            'things', 'going', 'way', 'many', 'would', 'could', 'should', 'new', 'old', 'according', 'including',
            'first', 'last', 'next', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
        ])
        # This token_pattern ensures we only get actual words (no numbers)
        vectorizer_model = CountVectorizer(stop_words=custom_stopwords, ngram_range=(1, 2), token_pattern=r'(?u)\b[A-Za-z-]{3,}\b')
        
       
        umap_model = None
        if len(sentences) >= 15:
            umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine', random_state=42)
        elif len(sentences) >= 5: 
             umap_model = UMAP(n_neighbors=max(2, len(sentences) - 1), n_components=2, min_dist=0.0, metric='cosine', random_state=42)

        
        representation_model = KeyBERTInspired()

        topic_model = BERTopic(
            min_topic_size=2,
            nr_topics="auto",
            vectorizer_model=vectorizer_model,
            umap_model=umap_model, 
            representation_model=representation_model, 
            verbose=False
        )
        topics, _ = topic_model.fit_transform(sentences)
        
    except Exception as e:
        print(f"Error inside BERTopic, cannot generate topics. Error: {e}")
        return None

    topic_info = topic_model.get_topic_info()
    topic_info = topic_info[topic_info.Topic != -1]
    if topic_info.empty: return None

    formatted_topics = []
    for topic_id in topic_info["Topic"]:
        keywords = [word for word, _ in topic_model.get_topic(topic_id)]
        formatted_topics.append({"topic_id": topic_id, "keywords": keywords})
    return formatted_topics


def _create_intelligent_query(entities, topics):
    """Creates one single, powerful, and de-duplicated search query."""
    topic_keywords = []
    if topics:
        for topic in topics:
            # We take fewer keywords now because they are higher quality (n-grams)
            topic_keywords.extend(topic['keywords'][:2])
    
    # Prioritize entities, then topics
    base_terms = list(dict.fromkeys(entities + topic_keywords))
    
    # Intelligent De-duplication
    search_terms = []
    for term in base_terms:
        is_redundant = any(term != other and term in other for other in base_terms)
        if not is_redundant:
            search_terms.append(f'"{term}"' if ' ' in term and len(term) < 50 else term)
            
    if not search_terms:
        return None

    # Create one flexible query with the best 3-4 terms
    final_query = " AND ".join(search_terms[:3])
    return final_query

def find_alternative_articles(topics, raw_text):
    GNEWS_API_KEY = 'd2eae8b812af33338e4fc336dcdcbbc0'
    NEWSAPI_API_KEY = '277de6d1d0524b14868458d751e880be'

    key_entities = extract_key_entities(raw_text)
    search_query = _create_intelligent_query(key_entities, topics)
    
    if not search_query:
        print("Could not generate a search query.")
        return []

    # We will try both APIs to maximize our chances
    print(f"--- Attempting search with intelligent query: '{search_query}' ---")
    
    articles = _call_gnews_api(search_query, NEWSAPI_API_KEY) # Pass NewsAPI key to gnews call
    
    if not articles:
        print(f"GNews found no results. Falling back to NewsAPI.org...")
        articles = _call_newsapi_api(search_query, NEWSAPI_API_KEY)
    
    if not articles:
        # ULTIMATE FALLBACK: Try a broader search with just the single best term
        print(f"All searches failed. Trying ultimate fallback with single best term.")
        single_best_term = _create_intelligent_query(key_entities, topics).split(' AND ')[0]
        if single_best_term:
            articles = _call_gnews_api(single_best_term, GNEWS_API_KEY)
            if not articles:
                articles = _call_newsapi_api(single_best_term, NEWSAPI_API_KEY)

    # Remove duplicate articles
    if not articles: return []
    unique_articles = []
    seen_titles = set()
    for article in articles:
        if article['title'] and article['title'] not in seen_titles:
            unique_articles.append(article)
            seen_titles.add(article['title'])
    return unique_articles[:5]

# (_call_api, _call_gnews_api, _call_newsapi_api functions remain the same)
def _call_api(api_url, api_name):
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        formatted_articles = []
        for article_data in data.get('articles', []):
            if article_data.get('title') and article_data.get('source', {}).get('name'):
                formatted_articles.append({
                    'title': article_data.get('title'),
                    'source': article_data.get('source', {}).get('name'),
                    'url': article_data.get('url'),
                    'publishedAt': article_data.get('publishedAt', '').split('T')[0]
                })
        print(f"--> {api_name} found {len(formatted_articles)} articles.")
        return formatted_articles
    except requests.exceptions.Timeout:
        print(f"Error calling {api_name}: The request timed out.")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error calling {api_name}: {e}")
        return []

def _call_gnews_api(query, api_key):
    api_url = (f'https://gnews.io/api/v4/search?q={query}&lang=en&max=5&apikey={api_key}')
    return _call_api(api_url, "GNews.io")

def _call_newsapi_api(query, api_key):
    api_url = (f'https://newsapi.org/v2/everything?q={query}&language=en&sortBy=relevancy&pageSize=5&apiKey={api_key}')
    return _call_api(api_url, "NewsAPI.org")


if __name__ == '__main__':
    print("--- Running NLP Processor Standalone Test ---")
    setup_nltk()
    test_url = 'https://www.bbc.com/news/articles/cd0vvg09175o'
    title, raw_text = fetch_article_text(test_url)
    if raw_text:
        print(f"\nFetched Article: {title}")
        sentiment = analyze_sentiment_from_text(raw_text)
        print(f"\nSentiment Scores: {sentiment}")
        topics = analyze_topics_from_text(raw_text)
        if topics:
            print("\nFound Topics:")
            for topic in topics:
                print(f"  - Topic keywords: {', '.join(topic['keywords'])}")
        alt_articles = find_alternative_articles(topics, raw_text)
        if alt_articles:
            print("\nFound Alternative Articles:")
            for article in alt_articles:
                print(f"  - [{article['source']}] {article['title']}")
        else:
            print("No alternative articles found.")
    else:
        print("Failed to fetch article for testing.")