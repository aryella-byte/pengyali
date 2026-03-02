#!/usr/bin/env python3
"""
Brief Auto-Updater
自动更新News和Research数据
- News: 从RSS抓取，按时间倒序
- Research: T14法学期刊，知识库式追加
"""

import json
import feedparser
import re
from datetime import datetime
from pathlib import Path
import hashlib

# 路径配置
WORKSPACE = Path("/root/.openclaw/workspace/website/brief")
DATA_FILE = WORKSPACE / "data" / "brief-data.json"
HISTORY_FILE = WORKSPACE / "data" / "history.json"

# 信源配置
NEWS_SOURCES = {
    "SCOTUSblog": "https://www.scotusblog.com/feed/",
    "Financial Times": "https://www.ft.com/rss/home",
    "Reuters Legal": "https://www.reutersagency.com/feed/?taxonomy=legal"
}

RESEARCH_SOURCES = {
    "Harvard Law Review": "https://harvardlawreview.org/feed/",
    "Michigan Law Review": "https://michiganlawreview.org/feed/",
    "Virginia Law Review": "https://www.virginialawreview.org/feed/",
    "Stanford Law Review": "https://www.stanfordlawreview.org/feed/",
    "Columbia Law Review": "https://columbialawreview.org/feed/",
    "Yale Law Journal": "https://www.yalelawjournal.org/feed/",
    "Berkeley Law Review": "https://www.boalt.org/feed/",
    "Georgetown Law Journal": "https://www.georgetownlawjournal.org/feed/"
}

# 标签分类规则
TAG_RULES = {
    "criminal": ("刑事司法", "criminal"),
    "constitutional": ("宪法", "constitutional"),
    "administrative": ("行政法", "constitutional"),
    "technology": ("科技法", "tech"),
    "ai": ("AI治理", "tech"),
    "privacy": ("隐私权", "tech"),
    "international": ("国际法", "international"),
    "trade": ("贸易法", "international"),
    "procedure": ("程序法", "criminal")
}

def load_data():
    """加载现有数据"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"news": [], "research": []}

def save_data(data):
    """保存数据"""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_item_id(title):
    """生成唯一ID"""
    return hashlib.md5(title.encode()).hexdigest()[:12]

def auto_tag(title, summary):
    """自动打标签"""
    text = f"{title} {summary}".lower()
    tags = []
    for keyword, (name, cls) in TAG_RULES.items():
        if keyword in text:
            tags.append({"name": name, "class": cls})
    return tags[:3] if tags else [{"name": "法律综合", "class": ""}]

def generate_why_matters(title, summary, is_research=False):
    """生成Why it matters"""
    text = f"{title} {summary}".lower()
    
    # 研究类论文
    if is_research:
        if "criminal" in text or "fourth amendment" in text:
            return "该论文对刑事司法程序中的宪法权利保护进行了深入分析，对中国刑事诉讼法改革和数字时代的人权保障具有比较法参考价值。"
        elif "constitutional" in text or "first amendment" in text:
            return "本文提供了宪法解释的重要视角，对于理解基本权利保护的理论基础和实践应用具有启发意义。"
        elif "technology" in text or "ai" in text or "privacy" in text:
            return "在数字技术快速发展的背景下，该研究为算法治理和科技监管提供了重要的理论支撑和实践参考。"
        else:
            return "本文在法学理论研究方面具有学术价值，为相关领域的进一步研究提供了重要的理论基础。"
    
    # 新闻类
    if "court" in text or "supreme" in text or "裁决" in text:
        return "这一司法动态可能影响相关领域的法律实践和学术研究方向，值得持续关注后续发展。"
    elif "international" in text or "iran" in text or "trade" in text:
        return "该事件涉及国际法和国际关系的重要议题，对全球法治秩序和国际经济格局可能产生深远影响。"
    elif "technology" in text or "ai" in text:
        return "这一科技政策动态反映了数字治理的最新趋势，对算法监管和科技法律研究具有重要参考价值。"
    else:
        return "该新闻涉及法律领域的重要发展，对于理解当前法治实践和政策走向具有参考意义。"

def fetch_feed(url, source_name):
    """抓取RSS feed"""
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:5]:
            items.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "summary": re.sub(r'<[^>]+>', '', entry.get("summary", ""))[:300],
                "date": entry.get("published", entry.get("updated", datetime.now().strftime("%Y-%m-%d")))[:10]
            })
        return items
    except Exception as e:
        print(f"  ✗ {source_name}: {e}")
        return []

def update_news(data):
    """更新News数据"""
    print("\n📰 Updating News...")
    existing_ids = {get_item_id(n["title"]) for n in data["news"]}
    new_count = 0
    
    for source, url in NEWS_SOURCES.items():
        items = fetch_feed(url, source)
        for item in items:
            item_id = get_item_id(item["title"])
            if item_id not in existing_ids:
                data["news"].append({
                    **item,
                    "source": source,
                    "whyMatters": generate_why_matters(item["title"], item["summary"], False),
                    "tags": auto_tag(item["title"], item["summary"])
                })
                new_count += 1
        print(f"  ✓ {source}: {len(items)} items")
    
    # 按日期倒序排序
    data["news"].sort(key=lambda x: x["date"], reverse=True)
    # 保留最近50条
    data["news"] = data["news"][:50]
    
    print(f"  +{new_count} new news items")
    return data

def update_research(data):
    """更新Research数据（知识库式追加）"""
    print("\n📄 Updating Research...")
    existing_ids = {get_item_id(r["title"]) for r in data["research"]}
    new_count = 0
    
    for source, url in RESEARCH_SOURCES.items():
        items = fetch_feed(url, source)
        for item in items:
            item_id = get_item_id(item["title"])
            if item_id not in existing_ids:
                data["research"].append({
                    **item,
                    "source": source,
                    "journal": source,
                    "authors": "TBD",  # RSS通常不包含作者信息，需要额外抓取
                    "whyMatters": generate_why_matters(item["title"], item["summary"], True),
                    "tags": auto_tag(item["title"], item["summary"])
                })
                new_count += 1
        print(f"  ✓ {source}: {len(items)} items")
    
    print(f"  +{new_count} new research items")
    return data

def main():
    print("="*60)
    print("🤖 Brief Auto-Updater")
    print("="*60)
    
    # 加载现有数据
    data = load_data()
    print(f"\n📊 Current: {len(data.get('news', []))} news, {len(data.get('research', []))} papers")
    
    # 更新数据
    data = update_news(data)
    data = update_research(data)
    
    # 保存
    save_data(data)
    print(f"\n✅ Saved to {DATA_FILE}")
    print(f"📈 Total: {len(data['news'])} news, {len(data['research'])} papers")

if __name__ == "__main__":
    main()
