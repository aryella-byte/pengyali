#!/usr/bin/env python3
"""
Daily Brief Updater - 每日简报更新器
- 抓取新闻和研究文章
- 去重
- 更新单页HTML的时间戳
"""

import json
import feedparser
from datetime import datetime
from pathlib import Path
import hashlib
import re

# 配置
WORKSPACE = Path("/root/.openclaw/workspace/website/brief")
HISTORY_FILE = WORKSPACE / "content" / "article-history.json"
INDEX_FILE = WORKSPACE / "index.html"

# RSS源
NEWS_SOURCES = {
    "SCOTUSblog": "https://www.scotusblog.com/feed/",
    "Financial Times": "https://www.ft.com/rss/home",
}

RESEARCH_SOURCES = {
    "Harvard Law Review": "https://harvardlawreview.org/feed/",
    "Michigan Law Review": "https://michiganlawreview.org/feed/",
    "Virginia Law Review": "https://www.virginialawreview.org/feed/",
}

def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {"articles": []}

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def get_article_id(title, link):
    return hashlib.md5(f"{title}|{link}".encode()).hexdigest()[:12]

def fetch_feed(url, max_items=3):
    try:
        feed = feedparser.parse(url)
        return [{
            "title": e.get("title", ""),
            "link": e.get("link", ""),
            "source": feed.feed.get("title", "Unknown")
        } for e in feed.entries[:max_items]]
    except:
        return []

def update_timestamp():
    """更新HTML文件中的时间戳"""
    if not INDEX_FILE.exists():
        print(f"  ✗ {INDEX_FILE} not found")
        return False
    
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 更新时间戳
    updated = re.sub(
        r'Last updated: \d{4}-\d{2}-\d{2} \d{2}:\d{2} CST',
        f'Last updated: {now} CST',
        content
    )
    
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(updated)
    
    print(f"  ✓ Updated timestamp: {now}")
    return True

def main():
    print("="*50)
    print("🗓️  Daily Brief Updater")
    print("="*50)
    
    history = load_history()
    print(f"\n📚 Tracking {len(history.get('articles', []))} articles")
    
    # 抓取新内容
    new_items = []
    for name, url in {**NEWS_SOURCES, **RESEARCH_SOURCES}.items():
        items = fetch_feed(url)
        for item in items:
            aid = get_article_id(item['title'], item['link'])
            if aid not in history.get("articles", []):
                new_items.append(item)
                history["articles"].append(aid)
    
    print(f"\n📰 Found {len(new_items)} new items")
    
    if new_items:
        # 更新时间戳
        if update_timestamp():
            # 保存历史
            history["articles"] = history["articles"][-200:]  # 保留最近200条
            save_history(history)
            
            print(f"\n✅ Updated at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            print("📝 Manual review needed for new content:")
            for item in new_items[:5]:
                print(f"   - {item['title'][:50]}...")
    else:
        print("\nℹ️  No new content")

if __name__ == "__main__":
    main()
