#!/usr/bin/env python3
"""
Brief Auto-Updater v5.1 - AI-Powered
使用Kimi API分析RSS内容，生成高质量简报
"""
import json
import feedparser
import re
import os
from datetime import datetime
from pathlib import Path
import hashlib
from anthropic import Anthropic

WORKSPACE = Path("/root/.openclaw/workspace/website/brief")
DATA_FILE = WORKSPACE / "data" / "brief-data.json"

NEWS_SOURCES = {
    "SCOTUSblog": "https://www.scotusblog.com/feed/",
    "Financial Times": "https://www.ft.com/rss/home",
}

RESEARCH_SOURCES = {
    "Harvard Law Review": "https://harvardlawreview.org/feed/",
    "Michigan Law Review": "https://michiganlawreview.org/feed/",
}

JUNK_KEYWORDS = [
    "live blog", "schedule", "calendar", "argument preview",
    "scotustoday", "announcement", "call for submissions"
]

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"news": [], "research": []}

def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_item_id(title):
    return hashlib.md5(title.encode()).hexdigest()[:12]

def is_junk(title):
    return any(j in title.lower() for j in JUNK_KEYWORDS)

def categorize_tag(tag):
    t = tag.lower()
    if any(x in t for x in ["刑事", "criminal", "sentencing", "prison"]):
        return "criminal"
    if any(x in t for x in ["宪法", "constitutional"]):
        return "constitutional"
    if any(x in t for x in ["国际", "immigration", "international"]):
        return "international"
    return ""

def analyze_with_ai(title, source, is_research=False):
    """使用AI分析标题，返回结构化结果"""
    api_key = os.environ.get("ANTHROPIC_API_KEY") or "sk-kimi-QcVnk029GozI0odrOBLibZx3NFaUqzH9KmIM6C3G3IsOmNga3Uq0anBslkcB3L2d"
    base_url = os.environ.get("ANTHROPIC_BASE_URL") or "https://api.kimi.com/coding/"
    
    try:
        client = Anthropic(api_key=api_key, base_url=base_url)
        
        atype = "法学研究" if is_research else "法律新闻"
        prompt = f"分析这篇{atype}：{title}\n\n用JSON输出：{{\"summaryCN\": \"60-100字中文总结\", \"whyMattersCN\": \"60-100字重要性分析，要具体\"}}"
        
        resp = client.messages.create(
            model="kimi-k2-0711-preview",
            max_tokens=600,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = resp.content[0].text.strip()
        text = re.sub(r'^```json\\s*', '', text)
        text = re.sub(r'\\s*```$', '', text)
        
        result = json.loads(text)
        return result.get("summaryCN", ""), result.get("whyMattersCN", "")
    except Exception as e:
        print(f"      AI error: {e}")
        return None, None

def fetch_feed(url, name):
    try:
        feed = feedparser.parse(url)
        items = []
        for e in feed.entries[:12]:
            title = e.get("title", "").strip()
            if title and not is_junk(title):
                items.append({
                    "title": title,
                    "url": e.get("link", ""),
                    "date": e.get("published", datetime.now().strftime("%Y-%m-%d"))[:10]
                })
        return items
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return []

def update_news(data):
    print("\n📰 Updating News...")
    existing = {get_item_id(n["title"]) for n in data["news"]}
    new_items = []
    
    for source, url in NEWS_SOURCES.items():
        items = fetch_feed(url, source)
        print(f"  → {source}: {len(items)} candidates")
        
        for item in items:
            if get_item_id(item["title"]) in existing:
                continue
            
            print(f"    {item['title'][:50]}...")
            summary, why = analyze_with_ai(item["title"], source)
            
            if summary and why:
                new_items.append({
                    "title": item["title"],
                    "titleCN": item["title"],
                    "url": item["url"],
                    "date": item["date"],
                    "source": source,
                    "summaryCN": summary,
                    "summaryEN": "",
                    "whyMattersCN": why,
                    "whyMattersEN": "",
                    "tags": [{"name": "法律动态", "class": ""}],
                    "quality_score": 8
                })
                print(f"      ✓ Added")
            else:
                print(f"      ✗ Skipped")
            
            if len(new_items) >= 5:
                print("  ⏹ Limit reached")
                break
        if len(new_items) >= 5:
            break
    
    data["news"].extend(new_items)
    data["news"].sort(key=lambda x: x["date"], reverse=True)
    data["news"] = data["news"][:15]
    print(f"  +{len(new_items)} new items")
    return data

def main():
    print("="*50)
    print("🤖 Brief Auto-Updater v5.1")
    print("="*50)
    
    data = load_data()
    print(f"\nCurrent: {len(data.get('news', []))} news")
    
    data = update_news(data)
    save_data(data)
    
    print(f"\n✅ Total: {len(data['news'])} news")

if __name__ == "__main__":
    main()
