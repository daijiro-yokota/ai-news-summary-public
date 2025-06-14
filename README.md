**Article Summarizer and Slack Notifier**

This Python project fetches recent articles (example: RevenueCat blog), summarizes them using OpenAI's GPT model, evaluates relevance to the user, extracts keywords, and posts summaries to a Slack channel if they meet the criteria.

**Features**

1. Article Discovery: Scrapes the RevenueCat blog homepage for new posts (excluding author pages and RSS feeds).
2. Content Extraction: Parses each article’s title, body text, and publication date.
3. Summarization: Uses GPT-4 to produce a concise 3–4 sentence summary, ensuring alignment with the title.
4. Keyword Extraction: Pulls 3–5 marketing-relevant keywords from the summary.
5. Relevance Scoring: Evaluates each summary’s relevance (0–100) for marketing audiences based on a predefined prompt.
6. Slack Integration: Posts summaries that meet a configurable relevance threshold to Slack with title, date, summary, relevance score, and keywords.

**Prerequisites**
- Python 3.8+
- A Slack incoming webhook URL
- An OpenAI API key with access to GPT-4 models

**Installation**

Step 1: Clone the repository:
-- git clone https://github.com/your-org/revenuecat-summarizer.git
-- cd revenuecat-summarizer

Step 2: (Optional) Create and activate a virtual environment:
-- python3 -m venv venv
-- source venv/bin/activate

Step 3: Install dependencies:
-- pip install -r requirements.txt

Step 4: Configure environment variables (in a .env file or your shell):
-- OPENAI_API_KEY
-- SLACK_WEBHOOK_URL

**Usage**

Run the script directly:

python summarizer.py

By default, it will:

1. Fetch articles from the last 7 days (168 hours).
2. Summarize and extract keywords.
3. Score relevance.
4. Post to Slack if score ≥ 70.

Customizing the Threshold

Edit the threshold parameter in the process_revenuecat_articles() call at the bottom of summarizer.py to adjust the relevance cutoff.

Project Structure

- main.py # Main script
- README.md # This file

**Functions Overview**

- get_revenuecat_articles(): Returns list of blog URLs to process.
- extract_revenuecat_article(url): Parses the title, content, and date.
- summarize_article(title, content): Calls the OpenAI API to summarize.
- extract_keywords(summary): Calls the OpenAI API to extract keywords.
- evaluate_relevance(summary_text): Calls the OpenAI API to score relevance.
- process_revenuecat_articles(threshold): Orchestrates the pipeline and returns high-scoring articles.

**Contributing**

Fork the repository and create your feature branch.
Write clear, concise commit messages.
Submit a pull request with a description of your changes.

**License**

This project is licensed under the MIT License. See the LICENSE file for details.
