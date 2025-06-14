import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import json
import time
from datetime import datetime, timedelta

# OpenAI API client
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

# 1️⃣ Get articles from a website (example: RevenueCat blog)
def get_revenuecat_articles():
    url = "https://www.revenuecat.com/blog/"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    links = set()
    excluded = {"https://www.revenuecat.com/blog/rss.xml"} ## Exlcude the URLs you don't want to scrape. 

    for a in soup.find_all("a", href=True): ## Exclude URLs with the same prefix you don't want to scrape. 
        href = a["href"]
        if href in excluded:
            continue
        if (
            href.startswith("/blog/")
            and not any(href.startswith(prefix) for prefix in ["/blog/author/", "/blog/rss.xml"])
            and href != "/blog/"
        ):
            links.add(f"https://www.revenuecat.com{href}")

    return list(links)

# 2️⃣ Extract content and publish date
def extract_revenuecat_article(url):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "No Title"
        paragraphs = soup.find_all("p")
        content = "\n".join(p.get_text(strip=True) for p in paragraphs)[:15000]
        time_tag = soup.find("time")
        publish_date = None
        if time_tag and time_tag.has_attr("datetime"):
            publish_date = datetime.strptime(time_tag["datetime"], "%Y-%m-%d")
        return {"url": url, "title": title, "content": content, "publish_date": publish_date}
    except Exception as e:
        print(f"❌ Failed to extract {url}: {e}")
        return None

# 3️⃣ Summarize using GPT
def summarize_article(title, content):
    prompt = (
        f"Summarize this article in 3–4 clear sentences (50–60 words):\n\n"
        f"Title: {title}\n\n{content}\n\n"
        "Ensure the summary reflects the article’s main points and stays aligned with the title."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Summarize error: {e}")
        return "Summary not available."

# 3️⃣a Extract keywords from the summary
def extract_keywords(summary):
    prompt = (
        "Extract 3 marketing-focused keywords or short phrases from this summary, "
        "comma-separated. No extra text.\n\n"
        f"{summary}"
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Keyword extraction error: {e}")
        return ""

# 3️⃣b Evaluate relevance on the summary only
def evaluate_relevance(summary_text): ## Modify the prompt for your specific use case. 
    prompt = (
        "You are an expert content evaluator for a marketing agency focused on running paid ads for app and web subscription businesses.\n\n"
        "The audience is marketing managers, growth leads, marketing analysts, and creative directors. Not engineers or product managers.\n\n"
        "Based only on the TLDR summary, assign a relevance score from 0–100 according to these guidelines:\n"
        "- **80–100**: Core app or web subscription marketing topics (e.g. campaign optimization, subscription monetization strategies, incrementality test).\n"
        "- **60–79**: Strongly related marketing measurement topics (conversion API, media mix modeling, ROAS, SKAN, SKAdNetwork, MMP).\n"
        "- **40–59**: Indirectly related topics or product strategies with marketing implications like churn reduction, LTV maximization, etc.\n"
        "- **0–39**: Primarily engineering or developer-only content with low marketing relevance.\n\n"
        "Return JSON exactly as:\n"
        "{ \"relevance_score\": X, \"comment\": \"...\" }\n\n"
        "Example: “An article about paywall design tests to improve subscription churn” → score 75.\n\n"
        "Example: “An article about apps seeing reduction in revenue after switching to web paywall from app subscription” → score 85.\n\n"
        "Example: “An article about Google introducing new campaign types focusing on AI Overview” → score 85.\n\n"
        "Example: “An article about an app changing targeting for their marketing campaigns to optimize ROAS” → score 80.\n\n"
        "Example: “An article about SDK update on RevenueCat” → score 30.\n\n"
        f"Summary:\n{summary_text}"
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-2025-04-14", ## Use the latest model available. 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return {}

# 4️⃣ Full pipeline
def process_revenuecat_articles(threshold=70):
    links = get_revenuecat_articles()
    print(f"✅ Found {len(links)} articles.\n")
    kept = []
    now = datetime.utcnow()

    for url in links:
        print(f"🔎 Processing: {url}")
        art = extract_revenuecat_article(url)
        if not art or not art["publish_date"]:
            print("⚠️ Missing date/content → skip\n")
            continue
        if now - art["publish_date"] > timedelta(hours=168):
            print("⏩ Older than 168h → skip\n")
            continue
        if len(art["content"]) < 300:
            print("⚠️ Content too short → skip\n")
            continue

        # Summarize
        summary = summarize_article(art["title"], art["content"])
        print(f"🗒 Summary:\n{summary}\n")

        # Extract keywords
        keywords = extract_keywords(summary)
        print(f"🔑 Keywords: {keywords}\n")

        # Evaluate
        eval_res = evaluate_relevance(summary)
        score = eval_res.get("relevance_score", 0)
        comment = eval_res.get("comment", "")
        print(f"📝 Relevance Score: {score}")
        print(f"💬 Eval Comment: {comment}\n")

        # Decide
        if score >= threshold:
            kept.append({
                "url": art["url"],
                "title": art["title"],
                "publish_date": art["publish_date"],
                "summary": summary,
                "keywords": keywords,
                "relevance_score": score,
                "evaluation_comment": comment
            })
            time.sleep(1)  # pause when keeping for rate limits
        else:
            print("⏩ Low score → not adding to Slack\n")

    return kept

if __name__ == "__main__":
    result = process_revenuecat_articles(threshold=70)
    print(f"\n✅ Total passed threshold: {len(result)} articles.\n")

    # Only post to Slack if there's at least one article
    if result:
        webhook_url = "[Slack Webhook URL]"
        blocks = []
        for art in result:
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*<{art['url']}|{art['title']}>* (_{art['publish_date']:%Y-%m-%d}_)\n"
                            f"{art['summary']}\n"
                            f"_Relevance Score: {art['relevance_score']}. Keywords: {art['keywords']}_"
                        )
                    }
                },
                {"type": "divider"}
            ])
        payload = {"blocks": blocks}

        resp = requests.post(webhook_url, json=payload)
        resp.raise_for_status()
        print("✅ Posted to Slack!")
    else:
        print("🚫 No articles passed the threshold — skipping Slack post.")
