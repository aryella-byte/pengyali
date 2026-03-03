#!/usr/bin/env python3
"""
Research Daily Update - 每日3篇精选法学论文
强制推送，即使质量不完美也要选最好的3篇
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

RESEARCH_SOURCES = {
    "Harvard Law Review": "https://harvardlawreview.org/feed/",
    "Michigan Law Review": "https://michiganlawreview.org/feed/",
}

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

def is_criminal_justice(title):
    """检查是否与刑事司法相关"""
    t = title.lower()
    keywords = [
        "criminal", "sentencing", "prison", "police", "prosecution",
        "jury", "forensic", "evidence", "fourth amendment", "fifth amendment",
        "miranda", "plea", "bail", "incarceration", "mass incarceration",
        "death penalty", "wrongful conviction", "dna"
    ]
    return any(k in t for k in keywords)

def analyze_with_ai(title, source):
    """使用AI分析论文"""
    api_key = os.environ.get("ANTHROPIC_API_KEY") or "sk-kimi-QcVnk029GozI0odrOBLibZx3NFaUqzH9KmIM6C3G3IsOmNga3Uq0anBslkcB3L2d"
    base_url = os.environ.get("ANTHROPIC_BASE_URL") or "https://api.kimi.com/coding/"
    
    try:
        client = Anthropic(api_key=api_key, base_url=base_url)
        
        prompt = f"""分析这篇法学论文标题：{title}

来源：{source}

请生成：
1. 60-80字中文总结（核心研究问题/方法）
2. 60-80字重要性分析（学术贡献、对刑事司法实践的潜在影响）

用JSON格式：
{{"summary": "...", "significance": "..."}}"""
        
        resp = client.messages.create(
            model="kimi-k2-0711-preview",
            max_tokens=500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = resp.content[0].text.strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        
        result = json.loads(text)
        return result.get("summary", ""), result.get("significance", "")
    except Exception as e:
        print(f"    AI error: {e}")
        return None, None

def fetch_feed(url, name):
    try:
        feed = feedparser.parse(url)
        items = []
        for e in feed.entries[:10]:
            title = e.get("title", "").strip()
            if title and is_criminal_justice(title):
                items.append({
                    "title": title,
                    "url": e.get("link", ""),
                    "date": e.get("published", datetime.now().strftime("%Y-%m-%d"))[:10]
                })
        return items
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return []

def update_research(data):
    print("\n📚 Updating Research (Daily 3)...")
    existing = {get_item_id(r["title"]) for r in data["research"]}
    
    # 收集所有候选
    candidates = []
    for source, url in RESEARCH_SOURCES.items():
        items = fetch_feed(url, source)
        print(f"  → {source}: {len(items)} criminal justice items")
        
        for item in items:
            if get_item_id(item["title"]) not in existing:
                candidates.append({**item, "source": source})
    
    if not candidates:
        print("  ⚠️ No new candidates found")
        # 如果没有新内容，从历史中挑选3篇最好的
        return data, []
    
    print(f"\n  Analyzing {len(candidates)} candidates with AI...")
    
    # AI分析所有候选
    analyzed = []
    for item in candidates:
        print(f"    {item['title'][:50]}...")
        summary, significance = analyze_with_ai(item["title"], item["source"])
        
        if summary and significance:
            analyzed.append({
                **item,
                "summaryCN": summary,
                "whyMattersCN": significance,
                "quality_score": 8
            })
            print(f"      ✓ Analyzed")
        else:
            # 即使AI失败也保留，用基础模板
            analyzed.append({
                **item,
                "summaryCN": f"发表在{item['source']}上的刑事司法研究。",
                "whyMattersCN": "该研究对理解美国刑事司法制度具有参考价值。",
                "quality_score": 6
            })
            print(f"      ⚠️ Using fallback")
    
    # 按质量排序，选前3
    analyzed.sort(key=lambda x: x["quality_score"], reverse=True)
    selected = analyzed[:3]
    
    print(f"\n  ✅ Selected {len(selected)} papers:")
    for i, item in enumerate(selected, 1):
        print(f"    {i}. {item['title'][:45]}...")
    
    # 添加到数据
    for item in selected:
        data["research"].append({
            "title": item["title"],
            "titleCN": item["title"],
            "url": item["url"],
            "date": item["date"],
            "journal": item["source"],
            "summaryCN": item["summaryCN"],
            "summaryEN": "",
            "whyMattersCN": item["whyMattersCN"],
            "whyMattersEN": "",
            "tags": [{"name": "刑事司法", "class": "criminal"}],
            "quality_score": item["quality_score"]
        })
    
    # 保持最近15篇
    data["research"].sort(key=lambda x: x["date"], reverse=True)
    data["research"] = data["research"][:15]
    
    return data, selected

def main():
    print("="*50)
    print("📚 Research Daily - 3精选论文")
    print("="*50)
    
    data = load_data()
    print(f"\nCurrent: {len(data.get('research', []))} papers")
    
    data, selected = update_research(data)
    save_data(data)
    
    print(f"\n✅ Total: {len(data['research'])} papers")
    
    # 输出报告
    print("\n📋 Today's Selection:")
    for i, item in enumerate(selected, 1):
        print(f"\n{i}. {item['title']}")
        print(f"   Source: {item['source']}")
        print(f"   Summary: {item['summaryCN'][:60]}...")

if __name__ == "__main__":
    main()
