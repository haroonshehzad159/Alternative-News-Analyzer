
from flask import Flask, render_template, request
import processor

# Create an instance of the Flask application
app = Flask(__name__)


print("Initializing NLP models...")

print("Initialization complete.")



@app.route('/')
def index():
    """Renders the main homepage with the input form."""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Handles the form submission, runs the full NLP pipeline, and renders the results.
    """
    url = request.form['url']
    
    # Fetch the original article's content
    title, raw_text = processor.fetch_article_text(url)
    
    # Handle fetching errors gracefully
    if not raw_text:
        error_message = "Error: Could not fetch or parse the article from the initial URL. The website might be blocking automated requests or requires JavaScript to load its content."
        return render_template('error.html', error_message=error_message)

    # Perform the core NLP analysis on the original article
    sentiment = processor.analyze_sentiment_from_text(raw_text)
    topics = processor.analyze_topics_from_text(raw_text)
    
    # Find alternative articles using the new intelligent search strategy
    
    alternative_articles = processor.find_alternative_articles(topics, raw_text)
    
    # Analyze sentiment for each of the successfully found alternative articles
    successful_alternatives = []
    if alternative_articles:
        for article in alternative_articles:
            print(f"Fetching and analyzing alternative: {article['url']}")
            _ , alt_raw_text = processor.fetch_article_text(article['url'])
            if alt_raw_text:
                article['sentiment'] = processor.analyze_sentiment_from_text(alt_raw_text)
                successful_alternatives.append(article)
            else:
                print(f"--> Failed to fetch content for: {article['title']}")
    
    # Render the final results page with all the collected data
    return render_template(
        'results.html', 
        article_title=title, 
        sentiment=sentiment, 
        topics=topics,
        alternative_articles=successful_alternatives
    )


if __name__ == '__main__':
    
    processor.setup_nltk()
    app.run(debug=True)