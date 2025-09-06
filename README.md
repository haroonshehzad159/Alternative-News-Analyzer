# Alternative News Perspective Analyzer

## 🚀 Live Application

You can access and use the live version of this application, deployed on Streamlit Community Cloud, here:

**[https://alternative-news-source-hamza.streamlit.app/](https://alternative-news-source-hamza.streamlit.app/)** 

---

## 📖 Project Overview

This project is a web-based application designed to combat the effects of "filter bubbles" and promote media literacy. In an age of algorithmic content curation, it's easy to be exposed to only a single viewpoint. This tool empowers users to see the bigger picture.

By simply providing a URL to a news article, the application performs a sophisticated Natural Language Processing (NLP) analysis to:
1.  **Extract Key Topics:** Identifies the core themes and concepts of the article, moving beyond simple keywords to understand the context.
2.  **Analyze Sentiment:** Calculates the overall emotional tone of the article (positive, negative, neutral).
3.  **Find Alternative Perspectives:** Intelligently searches for related articles from a wide range of news sources.
4.  **Provide Comparative Analysis:** Displays the alternative articles alongside their own sentiment scores, allowing for a direct comparison of how different outlets are reporting on the same event.

This project was developed as part of an MSc thesis.

## ✨ Features

-   **Simple URL Input:** Easy-to-use interface, just paste a link to get started.
-   **Contextual Topic Modeling:** Uses `BERTopic` to find high-quality, meaningful topics, including important two-word phrases (n-grams).
-   **Robust Sentiment Analysis:** Employs `NLTK VADER` for fast and effective sentiment scoring.
-   **Intelligent Article Search:**
    -   Leverages `spaCy` for Named Entity Recognition to find the most important people, places, and organizations.
    -   Combines entities and topic keywords to create a powerful and relevant search query.
    -   Uses a dual-API fallback system (`GNews.io` and `NewsAPI.org`) to maximize the chances of finding relevant articles.
-   **Clean, Comparative UI:** A modern user interface built with Streamlit that presents complex information in a clear and easy-to-understand format.
-   **Resilient and Robust:** Gracefully handles short articles, article fetching failures, and API errors without crashing.

## 🛠️ Technology Stack

This project integrates a number of modern data science and web development technologies:

-   **Backend & NLP:** Python
-   **Web Framework:** Streamlit (for the deployed version), Flask (for local development)
-   **Core NLP Libraries:**
    -   **Topic Modeling:** `bertopic`
    -   **Entity Recognition:** `spaCy`
    -   **Sentiment & Text Processing:** `nltk`
    -   **Article Scraping:** `newspaper3k`
-   **Data Handling:** `pandas`
-   **APIs:** GNews.io, NewsAPI.org
-   **Deployment:** Streamlit Community Cloud
-   **Version Control:** Git & GitHub

## 🏃‍♀️ How to Run Locally

This project can be run in two modes:

### 1. Run with Streamlit (Recommended)

1.  Clone the repository:
    ```bash
    git clone https://github.com/Hamza-ijaz504/Alternative-News-Source.git
    ```
2.  Navigate to the project directory:
    ```bash
    cd Alternative-News-Source
    ```
3.  Create and activate a Python virtual environment.
4.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
5.  Download the necessary NLP models:
    ```bash
    python -m spacy download en_core_web_sm
    python -c "import nltk; nltk.download('all')"
    ```
6.  Run the Streamlit app:
    ```bash
    streamlit run streamlit_app.py
    ```
    The application will open in your web browser.

### 2. Run with Flask (Original Development Server)

Follow steps 1-5 above. Then, run the Flask app:
```bash
flask run

The application will be available at http://127.0.0.1:5000.