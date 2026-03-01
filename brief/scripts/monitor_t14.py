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

# T14 Law Reviews - RSS feeds and URLs (Updated with verified RSS links)
T14_REVIEWS = {
    # 有RSS的期刊
    "Harvard Law Review": {
        "url": "https://harvardlawreview.org/",
        "rss": "https://harvardlawreview.org/feed/",
        "type": "law"
    },
    "Stanford Law Review": {
        "url": "https://www.stanfordlawreview.org/",
        "rss": "https://www.stanfordlawreview.org/feed/",
        "type": "law"
    },
    "Columbia Law Review": {
        "url": "https://columbialawreview.org/",
        "rss": "https://columbialawreview.org/feed/",
        "type": "law"
    },
    "Chicago Law Review": {
        "url": "https://lawreview.uchicago.edu/",
        "rss": "https://lawreview.uchicago.edu/rss.xml",
        "type": "law"
    },
    "NYU Law Review": {
        "url": "https://www.nyulawreview.org/",
        "rss": "https://www.nyulawreview.org/feed/",
        "type": "law"
    },
    "Penn Law Review": {
        "url": "https://www.pennlawreview.com/",
        "rss": "https://www.pennlawreview.com/feed/",
        "type": "law"
    },
    "Virginia Law Review": {
        "url": "https://www.virginialawreview.org/",
        "rss": "https://www.virginialawreview.org/feed/",
        "type": "law"
    },
    "Michigan Law Review": {
        "url": "https://michiganlawreview.org/",
        "rss": "https://michiganlawreview.org/feed/",
        "type": "law"
    },
    "Duke Law Journal": {
        "url": "https://law.duke.edu/dlj/",
        "rss": "https://www.law.duke.edu/dlj/feed/",
        "type": "law"
    },
    "Cornell Law Review": {
        "url": "https://www.cornelllawreview.org/",
        "rss": "https://www.cornelllawreview.org/feed/",
        "type": "law"
    },
    "Northwestern Law Review": {
        "url": "https://scholarlycommons.law.northwestern.edu/nulr/",
        "rss": "https://scholarlycommons.law.northwestern.edu/nulr/recent.rss",
        "type": "law"
    },
    
    # 无RSS需要爬取的期刊
    "Yale Law Journal": {
        "url": "https://www.yalelawjournal.org/",
        "rss": None,  # 无公开RSS
        "type": "law",
        "note": "No RSS - needs web scraping"
    },
    "Berkeley Law Review": {
        "url": "https://www.boalt.org/",
        "rss": None,  # Law Review本身无RSS，只有法学院新闻RSS
        "type": "law",
        "note": "No Law Review specific RSS - needs web scraping"
    },
    "Georgetown Law Journal": {
        "url": "https://www.georgetownlawjournal.org/",
        "rss": None,  # Feed exists but empty/hello world
        "type": "law",
        "note": "Feed exists but empty - needs web scraping"
    }
}

# 关键词筛选 - CRIMINAL JUSTICE 最高优先级
KEYWORDS = {
    # 最高优先级 - Criminal Justice
    "criminal": 10,
    "criminal justice": 10,
    "sentencing": 10,
    "punishment": 10,
    "prison": 10,
    "incarceration": 10,
    "death penalty": 10,
    "homicide": 10,
    "violent crime": 10,
    "drug crime": 9,
    "white collar crime": 9,
    "fraud": 8,
    "policing": 8,
    "prosecution": 8,
    "defense": 8,
    "jury": 8,
    "nullification": 8,
    "due process": 8,
    "police": 8,
    "search and seizure": 8,
    "fourth amendment": 8,
    "fifth amendment": 8,
    "sixth amendment": 8,
    "eighth amendment": 8,
    "mass incarceration": 10,
    "criminal procedure": 9,
    "wrongful conviction": 9,
    "recidivism": 8,
    "rehabilitation": 7,
    "restorative justice": 8,
    
    # 高优先级 - Constitutional/Individual Rights
    "constitutional": 6,
    "civil rights": 6,
    "civil liberties": 6,
    "rights": 5,
    
    # 中优先级 - Other areas
    "administrative": 3,
    "regulation": 3,
    "corporate": 3,
    "securities": 3,
    "antitrust": 3,
    "international": 3,
    "human rights": 4,
    "technology": 4,
    "AI": 4,
    "algorithm": 4,
    "privacy": 5,
    "data": 3,
    "empirical": 4,
    "economics": 3,
    "law and economics": 3,
    "procedure": 4,
    "evidence": 5,
    "jurisdiction": 3,
    "race": 5,
    "gender": 4,
    "inequality": 4,
    "social justice": 5
}

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
    """计算文章相关性 - Criminal Justice 优先"""
    text = f"{article['title']} {article.get('summary', '')}".lower()
    score = 0
    for keyword, weight in KEYWORDS.items():
        if keyword in text:
            score += weight
    return score

def fetch_all_reviews():
    """抓取所有T14期刊"""
    all_articles = []
    rss_count = 0
    no_rss = []
    
    for name, info in T14_REVIEWS.items():
        print(f"Fetching {name}...")
        if info.get("rss"):
            articles = fetch_rss(name, info["rss"])
            for article in articles:
                article["relevance_score"] = score_relevance(article)
            all_articles.extend(articles)
            print(f"  ✓ {len(articles)} articles (RSS)")
            rss_count += 1
        else:
            no_rss.append(name)
            print(f"  ✗ No RSS - {info.get('note', 'Needs manual scraping')}")
    
    # 按相关性排序
    all_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    print(f"\n{'='*50}")
    print(f"RSS Coverage: {rss_count}/14 journals")
    if no_rss:
        print(f"No RSS (need scraping): {', '.join(no_rss)}")
    
    return all_articles

def save_results(articles, date_str):
    """保存结果"""
    output_dir = Path("/root/.openclaw/workspace/website/brief/content")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 按类别分类
    criminal_justice = [a for a in articles if any(k in a.get('title','').lower() for k in ['criminal', 'sentencing', 'punishment', 'prison', 'fourth amendment', 'police', 'jury'])]
    constitutional = [a for a in articles if 'constitutional' in a.get('title','').lower() and a not in criminal_justice]
    other = [a for a in articles if a not in criminal_justice and a not in constitutional]
    
    result = {
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "total_articles": len(articles),
        "by_category": {
            "criminal_justice": criminal_justice[:5],
            "constitutional": constitutional[:5],
            "other": other[:5]
        },
        "articles": articles[:15]  # 保存前15篇
    }
    
    output_file = output_dir / f"t14-research-{date_str}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Saved to {output_file}")
    print(f"\nCriminal Justice articles: {len(criminal_justice)}")
    print(f"Constitutional Law articles: {len(constitutional)}")
    print(f"Other articles: {len(other)}")
    print(f"\nTop 5 by relevance:")
    for i, article in enumerate(articles[:5], 1):
        badge = "🔥" if article['relevance_score'] >= 8 else "📄"
        print(f"  {badge} [{article['relevance_score']:2d}] {article['title'][:50]}... ({article['source']})")

def main():
    """主函数"""
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[{today}] Monitoring T14 Law Reviews...")
    print(f"{'='*50}\n")
    
    articles = fetch_all_reviews()
    save_results(articles, today)

if __name__ == "__main__":
    main()
