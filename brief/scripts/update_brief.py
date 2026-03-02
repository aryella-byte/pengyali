#!/usr/bin/env python3
"""
Brief Auto-Updater - 改进版
- 严格筛选高质量内容
- 针对性生成 Why it matters
- 过滤垃圾内容（征文、公告等）
"""

import json
import feedparser
import re
from datetime import datetime
from pathlib import Path
import hashlib

WORKSPACE = Path("/root/.openclaw/workspace/website/brief")
DATA_FILE = WORKSPACE / "data" / "brief-data.json"

NEWS_SOURCES = {
    "SCOTUSblog": "https://www.scotusblog.com/feed/",
    "Financial Times": "https://www.ft.com/rss/home",
    "Reuters Legal": "https://www.reutersagency.com/feed/?taxonomy=legal"
}

RESEARCH_SOURCES = {
    "Harvard Law Review": "https://harvardlawreview.org/feed/",
    "Michigan Law Review": "https://michiganlawreview.org/feed/",
    "Virginia Law Review": "https://www.virginialawreview.org/feed/"
}

# 垃圾内容关键词（需要过滤）
JUNK_KEYWORDS = [
    "call for submissions", "essay competition", "diversity and inclusion",
    "announcement", "cfa", "career", "job opening", "fellowship",
    "subscribe", "newsletter", "rss feed", "contact us"
]

# 高质量内容关键词（优先保留）
QUALITY_KEYWORDS = [
    "criminal", "constitutional", "fourth amendment", "fifth amendment",
    "sentencing", "mass incarceration", "policing", "jury",
    "administrative law", "regulatory", "technology", "privacy",
    "surveillance", "ai", "algorithm", "procedure"
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

def is_junk_content(title, summary):
    """判断是否为垃圾内容"""
    text = f"{title} {summary}".lower()
    for junk in JUNK_KEYWORDS:
        if junk in text:
            return True
    return False

def score_content(title, summary):
    """评分内容质量"""
    text = f"{title} {summary}".lower()
    score = 0
    for keyword in QUALITY_KEYWORDS:
        if keyword in text:
            score += 2
    # 有具体案例、实证研究加分
    if any(word in text for word in ["empirical", "study", "data", "analysis", "case"]):
        score += 3
    # 长度适中加分
    if len(summary) > 100:
        score += 1
    return score

def generate_why_matters(title, summary, source, is_research=False):
    """针对性生成 Why it matters - 非模板化"""
    text = f"{title} {summary}".lower()
    
    # 研究类 - 针对性分析
    if is_research:
        if any(k in text for k in ["fourth amendment", "search", "seizure", "warrant"]):
            return "第四修正案在数字时代的适用是当下最重要的宪法议题之一。该研究提出的分析框架对理解执法权力与隐私权的边界具有直接参考价值，尤其对中国刑事诉讼法中技术侦查措施的规制有借鉴意义。"
        
        if any(k in text for k in ["sentencing", "mass incarceration", "prison"]):
            return "量刑政策与大规模监禁是美国刑事司法的核心批评领域。该研究的实证发现可以为中国的量刑规范化改革提供比较视角，避免重蹈美国过度监禁的覆辙。"
        
        if any(k in text for k in ["jury", "nullification", "verdict"]):
            return "陪审团制度是普通法系的核心特征。该研究对陪审团裁判逻辑的深入分析，有助于理解对抗制诉讼中事实认定的制度设计，对中国人民陪审员制度的改革有启发意义。"
        
        if any(k in text for k in ["content moderation", "platform", "social media", "first amendment"]):
            return "平台内容治理是中美两国共同面临的法律挑战。该研究提出的宪法分析框架，对中国网络信息内容生态治理的法治化路径具有参考价值。"
        
        if any(k in text for k in ["drug", "opioid", "controlled substance", "scheduling"]):
            return "毒品政策涉及公共卫生、刑事司法和个人自由的多重张力。该研究对美国药物管制制度的制度分析，对中国毒品治理政策的科学化和人道化改革有参考意义。"
        
        if "establishment clause" in text or "ten commandments" in text:
            return "政教分离条款的解释涉及宪法文本主义与活宪法主义的方法论之争。该研究的历史分析路径，对理解宪法解释中历史材料的使用方法具有方法论价值。"
        
        if any(k in text for k in ["administrative", "agency", "regulation", "chevron"]):
            return "行政国家与司法审查的关系是现代行政法的核心议题。该研究对美国行政法最新发展的追踪，对中国行政诉讼制度和规范性文件审查制度的完善有借鉴意义。"
        
        if "crypto" in text or "bitcoin" in text or "digital asset" in text:
            return "加密货币的监管涉及证券法、反洗钱和投资者保护的多重法律问题。该研究对数字资产法律属性的分析，对中国虚拟货币监管政策的完善具有参考价值。"
        
        # 默认研究类
        if any(k in text for k in ["empirical", "empirical study", "data"]):
            return "该研究采用实证方法分析法律实践，其研究设计和数据处理方法对中国的实证法律研究具有方法论参考价值。研究发现可以为相关政策的制定提供经验依据。"
        
        return f"该论文发表在{source}上，探讨了法学领域的重要理论问题。对中国相关领域的学术研究和制度完善具有比较法参考价值。"
    
    # 新闻类 - 针对性分析
    if any(k in text for k in ["supreme court", "scotus", "justices", "opinion"]):
        if "major questions" in text or "tariff" in text or "administrative" in text:
            return "最高法院对重大问题的司法审查强化，将深刻影响联邦行政机构的规制权力。这一判例对理解司法权与行政权的边界具有重要意义，也可能影响全球行政法的理论发展。"
        return "最高法院的动态直接塑造美国法律实践走向。该案件的审理和判决可能产生先例效应，值得持续追踪其对相关领域法律实践的影响。"
    
    if any(k in text for k in ["iran", "israel", "war", "conflict", "military"]):
        return "中东局势的升级涉及国际法中的武力使用、自卫权和战争法规范。该冲突对全球能源供应、国际贸易秩序和国际法治都可能产生连锁影响，需要密切关注事态发展。"
    
    if any(k in text for k in ["trade", "tariff", "wto", "sanctions"]):
        return "国际贸易政策的变化直接影响全球经济格局和法律秩序。该动态涉及贸易法、制裁法和全球经济治理等多个法律领域，对跨国企业和国际投资有直接影响。"
    
    if any(k in text for k in ["ai", "artificial intelligence", "algorithm", "tech regulation"]):
        return "AI监管政策正在全球范围内快速演进。该动态反映的政策取向和监管思路，对算法治理、数据保护和数字法治建设具有直接参考价值。"
    
    if any(k in text for k in ["privacy", "surveillance", "data protection", "gdpr"]):
        return "数据隐私和监控规制是数字时代的核心法律议题。该发展对理解全球数据治理趋势、完善个人信息保护制度具有参考价值。"
    
    # 默认新闻类
    return f"该新闻来自{source}，反映了当前法律和政策领域的重要动态。对于理解相关领域的发展趋势和实务走向具有参考价值。"

def auto_tag(title, summary):
    """精准打标签"""
    text = f"{title} {summary}".lower()
    tags = []
    
    # 刑事司法
    if any(k in text for k in ["criminal", "sentencing", "prison", "incarceration", "police", "prosecution", "jury", "fourth amendment", "fifth amendment", "sixth amendment"]):
        tags.append({"name": "刑事司法", "class": "criminal"})
    
    # 宪法
    if any(k in text for k in ["constitutional", "first amendment", "establishment", "due process", "equal protection", "administrative", "chevron"]):
        tags.append({"name": "宪法与行政法", "class": "constitutional"})
    
    # 科技与隐私
    if any(k in text for k in ["technology", "ai", "artificial intelligence", "algorithm", "privacy", "surveillance", "data", "platform", "social media", "crypto", "digital"]):
        tags.append({"name": "科技与隐私", "class": "tech"})
    
    # 国际法
    if any(k in text for k in ["international", "trade", "war", "conflict", "iran", "israel", "sanctions", "wto", "treaty"]):
        tags.append({"name": "国际法", "class": "international"})
    
    if not tags:
        tags.append({"name": "法律综合", "class": ""})
    
    return tags[:3]

def fetch_feed(url, source_name):
    """抓取RSS feed"""
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:8]:  # 多取一些以便筛选
            title = entry.get("title", "").strip()
            summary = re.sub(r'<[^>]+>', '', entry.get("summary", ""))[:400]
            
            # 过滤垃圾内容
            if is_junk_content(title, summary):
                print(f"    ⚠️ Filtered: {title[:50]}...")
                continue
            
            items.append({
                "title": title,
                "url": entry.get("link", ""),
                "summary": summary,
                "date": entry.get("published", entry.get("updated", datetime.now().strftime("%Y-%m-%d")))[:10],
                "score": score_content(title, summary)
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
            if item_id not in existing_ids and item["score"] >= 2:  # 质量门槛
                data["news"].append({
                    "title": item["title"],
                    "url": item["url"],
                    "summary": item["summary"],
                    "date": item["date"],
                    "source": source,
                    "whyMatters": generate_why_matters(item["title"], item["summary"], source, False),
                    "tags": auto_tag(item["title"], item["summary"])
                })
                new_count += 1
        print(f"  ✓ {source}: {len([i for i in items if i['score'] >= 2])} quality items")
    
    # 按日期倒序排序
    data["news"].sort(key=lambda x: x["date"], reverse=True)
    data["news"] = data["news"][:30]  # 保留最近30条
    
    print(f"  +{new_count} new news items")
    return data

def update_research(data):
    """更新Research数据"""
    print("\n📄 Updating Research...")
    existing_ids = {get_item_id(r["title"]) for r in data["research"]}
    new_count = 0
    
    for source, url in RESEARCH_SOURCES.items():
        items = fetch_feed(url, source)
        for item in items:
            item_id = get_item_id(item["title"])
            if item_id not in existing_ids and item["score"] >= 3:  # 研究类质量门槛更高
                data["research"].append({
                    "title": item["title"],
                    "url": item["url"],
                    "summary": item["summary"],
                    "date": item["date"],
                    "journal": source,
                    "whyMatters": generate_why_matters(item["title"], item["summary"], source, True),
                    "tags": auto_tag(item["title"], item["summary"])
                })
                new_count += 1
        print(f"  ✓ {source}: {len([i for i in items if i['score'] >= 3])} quality items")
    
    # 新内容在前（知识库式）
    data["research"].reverse()
    data["research"] = data["research"][:50]  # 保留最近50篇
    
    print(f"  +{new_count} new research items")
    return data

def main():
    print("="*60)
    print("🤖 Brief Auto-Updater v2")
    print("="*60)
    
    data = load_data()
    print(f"\n📊 Current: {len(data.get('news', []))} news, {len(data.get('research', []))} papers")
    
    data = update_news(data)
    data = update_research(data)
    
    save_data(data)
    print(f"\n✅ Saved")
    print(f"📈 Total: {len(data['news'])} news, {len(data['research'])} papers")

if __name__ == "__main__":
    main()
