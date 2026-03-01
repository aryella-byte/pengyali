#!/usr/bin/env python3
"""
T14 Law Review Monitor
监控美国顶级14所法学院期刊的最新文章
"""
import json
import feedparser
import requests
from datetime import datetime, timedelta
from pathlib import Path

# T14 Law Reviews - RSS feeds and URLs
T14_REVIEWS = {
    "Yale Law Journal": {
        "url": "https://www.yalelawjournal.org/",
        "rss": None,  # 需要爬取网页
        "type": "law"
    },
    "Stanford Law Review": {
        "url": "https://www.stanfordlawreview.org/",
        "rss": None,
        "type": "law"
    },
    "Harvard Law Review": {
        "url": "https://harvardlawreview.org/",
        "rss": "https://harvardlawreview.org/feed/",
        "type": "law"
    },
    "Columbia Law Review": {
        "url": "https://columbialawreview.org/",
        "rss": "https://columbialawreview.org/feed/",
        "type": "law"
    },
    "Chicago Law Review": {
        "url": "https://lawreview.uchicago.edu/",
        "rss": None,
        "type": "law"
    },
    "NYU Law Review": {
        "url": "https://www.nyulawreview.org/",
        "rss": None,
        "type": "law"
    },
    "Penn Law Review": {
        "url": "https://www.pennlawreview.com/",
        "rss": None,
        "type": "law"
    },
    "Virginia Law Review": {
        "url": "https://www.virginialawreview.org/",
        "rss": "https://www.virginialawreview.org/feed/",
        "type": "law"
    },
    "Berkeley Law Review": {
        "url": "https://www.boalt.org/",
        "rss": None,
        "type": "law"
    },
    "Michigan Law Review": {
        "url": "https://michiganlawreview.org/",
        "rss": "https://michiganlawreview.org/feed/",
        "type": "law"
    },
    "Duke Law Journal": {
        "url": "https://law.duke.edu/dlj/",
        "rss": None,
        "type": "law"
    },
    "Northwestern Law Review": {
        "url": "https://scholarlycommons.law.northwestern.edu/nulr/",
        "rss": None,
        "type": "law"
    },
    "Cornell Law Review": {
        "url": "https://www.cornelllawreview.org/",
        "rss": None,
        "type": "law"
    },
    "Georgetown Law Journal": {
        "url": "https://www.georgetownlawjournal.org/",
        "rss": None,
        "type": "law"
    }
}

# 关键词筛选
KEYWORDS = [
    "criminal", "sentencing", "constitutional", "administrative", "regulation",
    "corporate", "securities", "antitrust", "international", "human rights",
    "technology", "AI", "algorithm", "privacy", "data",
    "empirical", "economics", "law and economics",
    "procedure", "evidence", "jurisdiction",
    "race", "gender", "inequality", "social justice"
]

def fetch_rss(name, rss_url):
    """抓取RSS feed"""
    if not rss_url:
        return []
    try:
        feed = feedparser.parse(rss_url)
        articles = []
        for entry in feed.entries[:5]:  # 最近5篇
            articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", "")[:300],
                "source": name
            })
        return articles
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return []

def score_relevance(article):
    """计算文章相关性"""
    text = f"{article['title']} {article.get('summary', '')}".lower()
    score = 0
    for keyword in KEYWORDS:
        if keyword in text:
            score += 1
    return score

def fetch_all_reviews():
    """抓取所有T14期刊"""
    all_articles = []
    
    for name, info in T14_REVIEWS.items():
        print(f"Fetching {name}...")
        articles = fetch_rss(name, info.get("rss"))
        for article in articles:
            article["relevance_score"] = score_relevance(article)
        all_articles.extend(articles)
        print(f"  → {len(articles)} articles")
    
    # 按相关性排序
    all_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
    return all_articles

def save_results(articles, date_str):
    """保存结果"""
    output_dir = Path("/root/.openclaw/workspace/website/brief/content")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "total_articles": len(articles),
        "articles": articles[:10]  # 保存前10篇
    }
    
    output_file = output_dir / f"t14-research-{date_str}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved to {output_file}")
    print(f"Top 5 articles by relevance:")
    for i, article in enumerate(articles[:5], 1):
        print(f"  {i}. [{article['relevance_score']}] {article['title'][:60]}... ({article['source']})")

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[{today}] Monitoring T14 Law Reviews...\n")
    
    articles = fetch_all_reviews()
    save_results(articles, today)

if __name__ == "__main__":
    main()
