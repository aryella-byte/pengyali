#!/usr/bin/env python3
"""
Brief Auto-Updater v4.5 - Quality-First Edition
- No generic fallbacks - skip if no match
- Strict quality heuristics
- Max 5 high-quality items per day
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
}

RESEARCH_SOURCES = {
    "Harvard Law Review": "https://harvardlawreview.org/feed/",
    "Michigan Law Review": "https://michiganlawreview.org/feed/",
}

# 高质量关键词匹配（必须具体指向法律争议）
QUALITY_PATTERNS = {
    "supreme_court_ruling": {
        "keywords": ["supreme court", "justices rule", "court holds", "court rejects"],
        "exclude": ["live blog", "argument preview", "schedule", "calendar"],
        "summary_cn": "最高法院就{topic}作出裁决，涉及{legal_issue}的法律适用。",
        "summary_en": "The Supreme Court rules on {topic}, addressing the application of {legal_issue}.",
        "why_cn": "该判决对{impact_area}具有先例效力，其法律推理路径对比较法研究和中国的{china_relevance}具有参考价值。",
        "why_en": "This ruling sets precedent for {impact_area}, offering comparative law insights for {china_relevance}.",
        "tags": ["宪法", "constitutional"]
    },
    "constitutional_rights": {
        "keywords": ["first amendment", "second amendment", "fourth amendment", "fifth amendment", "free speech", "gun rights"],
        "exclude": ["call for", "symposium"],
        "summary_cn": "涉及{amendment}权利边界与{govt_power}之间冲突的宪法争议。",
        "summary_en": "Constitutional dispute involving the boundary between {amendment} rights and {govt_power}.",
        "why_cn": "宪法基本权利的司法解释方法论对理解美国宪法动态和中国的基本权利保障机制完善具有比较法意义。",
        "why_en": "Judicial methodology for interpreting constitutional rights offers comparative insights for fundamental rights protection.",
        "tags": ["宪法", "constitutional"]
    },
    "criminal_procedure": {
        "keywords": ["sentencing", "plea bargaining", "jury", "forensic", "dna evidence", "exclusionary rule", "miranda"],
        "exclude": [],
        "summary_cn": "涉及{procedure}的刑事程序争议，关涉{stake}的保障机制。",
        "summary_en": "Criminal procedure dispute involving {procedure}, concerning safeguards for {stake}.",
        "why_cn": "刑事程序制度的比较研究对理解对抗制诉讼逻辑和中国刑事诉讼制度改革具有参考价值。",
        "why_en": "Comparative study of criminal procedure offers insights into adversarial system logic and reform reference value.",
        "tags": ["刑事程序", "criminal"]
    },
    "immigration_enforcement": {
        "keywords": ["immigration", "ice", "deportation", "detention", "border", "tps", "temporary protected status"],
        "exclude": ["business", "economy", "market"],
        "summary_cn": "涉及移民执法权边界与{rights}保障的行政法争议。",
        "summary_en": "Administrative law dispute involving immigration enforcement boundaries and {rights} protections.",
        "why_cn": "移民执法中的行政裁量权边界涉及人道主义保护与安全考量的平衡，对中国的出入境管理和外国人权利保障立法具有参考价值。",
        "why_en": "Administrative discretion in immigration enforcement involves balancing humanitarian protection with security considerations.",
        "tags": ["移民法", "international"]
    },
    "corporate_regulation": {
        "keywords": ["sec", "antitrust", "merger", "acquisition", "shareholder", "derivative suit"],
        "exclude": ["earnings", "profit", "revenue"],
        "summary_cn": "涉及{regulation_area}的公司法/证券法监管争议。",
        "summary_en": "Corporate/securities law dispute involving {regulation_area} regulation.",
        "why_cn": "公司监管和证券执法的制度设计对理解美国资本市场的法律基础和中国公司法、证券法的完善具有比较法意义。",
        "why_en": "Corporate regulation and securities enforcement design offers comparative insights for capital market legal foundations.",
        "tags": ["公司法", "constitutional"]
    },
    "ai_governance": {
        "keywords": ["artificial intelligence", "algorithm", "ai regulation", "automated decision"],
        "exclude": [],
        "summary_cn": "涉及{ai_issue}的AI治理法律争议，触及技术与法律的交叉地带。",
        "summary_en": "AI governance dispute involving {ai_issue}, at the intersection of technology and law.",
        "why_cn": "AI治理是全球法治的前沿议题，该动态对理解算法问责机制和技术规制路径具有参考价值，与中国AI立法进程形成对照。",
        "why_en": "AI governance is at the frontier of global rule of law, offering reference value for algorithmic accountability mechanisms.",
        "tags": ["AI治理", "tech"]
    }
}

JUNK_KEYWORDS = [
    "call for submissions", "essay competition", "diversity and inclusion",
    "announcement", "cfa", "career", "job opening", "fellowship",
    "subscribe", "newsletter", "rss feed", "contact us", "scotustoday",
    "animated explainer", "relist watch", "podcast", "video", "webinar",
    "live blog", "oral argument live", "schedule", "calendar", "argument preview",
    "argument analysis", "this week at the court", "orders list"
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

def is_junk_content(title):
    """过滤非实质性内容"""
    text = title.lower()
    for junk in JUNK_KEYWORDS:
        if junk in text:
            return True
    return False

def analyze_content(title, source):
    """
    分析内容质量，返回匹配结果或None（表示跳过）
    返回: (summaryCN, summaryEN, whyCN, whyEN, tags, quality_score)
    """
    text = title.lower()
    
    for pattern_name, pattern in QUALITY_PATTERNS.items():
        # 检查排除词
        if any(excl in text for excl in pattern["exclude"]):
            continue
            
        # 检查关键词匹配
        matched_keywords = [kw for kw in pattern["keywords"] if kw in text]
        if not matched_keywords:
            continue
        
        # 匹配成功，生成内容
        score = min(7 + len(matched_keywords), 10)  # 基础7分，多关键词加分
        
        # 根据具体类型生成内容
        if pattern_name == "supreme_court_ruling":
            topic = extract_topic(title)
            legal_issue = extract_legal_issue(title)
            
            # 中文映射
            topic_cn = {
                "immigration enforcement": "移民执法",
                "criminal justice": "刑事司法", 
                "administrative power": "行政权力",
                "free speech": "言论自由",
                "gun rights": "持枪权",
                "election law": "选举法",
                "interstate commerce": "州际贸易",
                "energy markets": "能源市场"
            }.get(topic, "相关法律争议")
            
            legal_issue_cn = {
                "constitutional validity": "合宪性",
                "governmental authority": "政府权限",
                "statutory construction": "制定法解释",
                "judicial jurisdiction": "司法管辖权",
                "appellate procedure": "上诉程序",
                "binding precedent": "判例约束力",
                "legal standards": "法律标准"
            }.get(legal_issue, "法律适用")
            
            return (
                f"最高法院就{topic_cn}作出裁决，涉及{legal_issue_cn}的法律适用。",
                f"The Supreme Court rules on {topic}, addressing the application of {legal_issue}.",
                f"该判决对{topic_cn}领域的法律适用具有先例效力，其法律推理路径对比较法研究和中国的相关制度建构具有参考价值。",
                f"This ruling sets precedent for {topic}, offering comparative law insights for institutional development.",
                [{"name": tag, "class": cls} for tag, cls in zip(pattern["tags"][::2], pattern["tags"][1::2])],
                score
            )
        
        elif pattern_name == "constitutional_rights":
            amendment = matched_keywords[0].replace(" amendment", "").title()
            govt_power = "政府监管权力" if "gun" in text or "firearm" in text else "公共安全"
            return (
                pattern["summary_cn"].format(amendment=amendment, govt_power=govt_power),
                pattern["summary_en"].format(amendment=amendment, govt_power=govt_power),
                pattern["why_cn"],
                pattern["why_en"],
                [{"name": tag, "class": cls} for tag, cls in zip(pattern["tags"][::2], pattern["tags"][1::2])],
                score
            )
        
        elif pattern_name == "criminal_procedure":
            procedure = matched_keywords[0].title()
            stake = "被告权利" if any(w in text for w in ["defendant", "accused", "rights"]) else "司法公正"
            return (
                pattern["summary_cn"].format(procedure=procedure, stake=stake),
                pattern["summary_en"].format(procedure=procedure, stake=stake),
                pattern["why_cn"],
                pattern["why_en"],
                [{"name": tag, "class": cls} for tag, cls in zip(pattern["tags"][::2], pattern["tags"][1::2])],
                score
            )
        
        elif pattern_name == "immigration_enforcement":
            rights = "移民权利" if any(w in text for w in ["rights", "protection", "asylum"]) else "程序正当性"
            return (
                pattern["summary_cn"].format(rights=rights),
                pattern["summary_en"].format(rights=rights),
                pattern["why_cn"],
                pattern["why_en"],
                [{"name": tag, "class": cls} for tag, cls in zip(pattern["tags"][::2], pattern["tags"][1::2])],
                score
            )
        
        elif pattern_name == "corporate_regulation":
            reg_area = "证券发行" if "sec" in text else "反垄断"
            return (
                pattern["summary_cn"].format(regulation_area=reg_area),
                pattern["summary_en"].format(regulation_area=reg_area),
                pattern["why_cn"],
                pattern["why_en"],
                [{"name": tag, "class": cls} for tag, cls in zip(pattern["tags"][::2], pattern["tags"][1::2])],
                score
            )
        
        elif pattern_name == "ai_governance":
            ai_issue = "算法问责" if "algorithm" in text else "AI系统监管"
            return (
                pattern["summary_cn"].format(ai_issue=ai_issue),
                pattern["summary_en"].format(ai_issue=ai_issue),
                pattern["why_cn"],
                pattern["why_en"],
                [{"name": tag, "class": cls} for tag, cls in zip(pattern["tags"][::2], pattern["tags"][1::2])],
                score
            )
    
    # 没有匹配到高质量模式，跳过
    return None

def extract_topic(title):
    """从标题提取主题 - 返回英文主题名用于模板填充"""
    text = title.lower()
    if "immigration" in text or "ice" in text:
        return "immigration enforcement"
    elif "criminal" in text or "sentencing" in text or "prison" in text:
        return "criminal justice"
    elif "administrative" in text or "agency" in text:
        return "administrative power"
    elif "first amendment" in text or "free speech" in text:
        return "free speech"
    elif "second amendment" in text or "firearm" in text or "gun" in text:
        return "gun rights"
    elif "congressional map" in text or "redistrict" in text:
        return "election law"
    elif "freight broker" in text or "trucking" in text:
        return "interstate commerce"
    elif "middle east" in text or "gas" in text or "oil" in text:
        return "energy markets"
    else:
        return "related legal disputes"

def extract_legal_issue(title):
    """从标题提取法律问题 - 返回英文用于模板"""
    text = title.lower()
    if "constitutionality" in text:
        return "constitutional validity"
    elif "authority" in text or "power" in text:
        return "governmental authority"
    elif "statutory" in text or "statute" in text:
        return "statutory construction"
    elif "jurisdiction" in text:
        return "judicial jurisdiction"
    elif "appeal" in text:
        return "appellate procedure"
    elif "precedent" in text:
        return "binding precedent"
    else:
        return "legal standards"

def fetch_feed(url, source_name):
    """抓取RSS feed"""
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:15]:
            title = entry.get("title", "").strip()
            
            if is_junk_content(title):
                print(f"    ⚠️ Junk filtered: {title[:50]}...")
                continue
            
            items.append({
                "title": title,
                "url": entry.get("link", ""),
                "date": entry.get("published", entry.get("updated", datetime.now().strftime("%Y-%m-%d")))[:10]
            })
        return items
    except Exception as e:
        print(f"  ✗ {source_name}: {e}")
        return []

def update_news(data):
    """更新News数据 - 严格筛选"""
    print("\n📰 Updating News (Quality-First Mode)...")
    existing_ids = {get_item_id(n["title"]) for n in data["news"]}
    new_items = []
    filtered_count = 0
    
    for source, url in NEWS_SOURCES.items():
        items = fetch_feed(url, source)
        print(f"  → {source}: {len(items)} candidate items")
        
        for item in items:
            item_id = get_item_id(item["title"])
            if item_id in existing_ids:
                continue
                
            # 分析内容质量
            result = analyze_content(item["title"], source)
            
            if result:
                cn_summary, en_summary, cn_why, en_why, tags, score = result
                new_items.append({
                    "title": item["title"],
                    "titleCN": item["title"],
                    "url": item["url"],
                    "date": item["date"],
                    "source": source,
                    "summaryCN": cn_summary,
                    "summaryEN": en_summary,
                    "whyMattersCN": cn_why,
                    "whyMattersEN": en_why,
                    "tags": tags,
                    "quality_score": score
                })
                print(f"    ✓ Included: {item['title'][:50]}... (score: {score})")
            else:
                filtered_count += 1
                print(f"    ✗ Filtered (no quality match): {item['title'][:50]}...")
            
            # 限制每天最多5条高质量新闻
            if len(new_items) >= 5:
                print(f"  ⏹ Reached daily limit (5 high-quality items)")
                break
        
        if len(new_items) >= 5:
            break
    
    data["news"].extend(new_items)
    data["news"].sort(key=lambda x: x["date"], reverse=True)
    data["news"] = data["news"][:15]  # 保留最近15条高质量内容
    
    print(f"  +{len(new_items)} new high-quality news items")
    print(f"  -{filtered_count} filtered (low quality/no match)")
    return data

def update_research(data):
    """更新Research数据 - 严格筛选"""
    print("\n📄 Updating Research (Strict Filter)...")
    existing_ids = {get_item_id(r["title"]) for r in data["research"]}
    new_items = []
    filtered_count = 0
    
    for source, url in RESEARCH_SOURCES.items():
        items = fetch_feed(url, source)
        print(f"  → {source}: {len(items)} candidate items")
        
        for item in items:
            item_id = get_item_id(item["title"])
            if item_id in existing_ids:
                continue
            
            # 研究论文需要标题包含特定关键词
            title_lower = item["title"].lower()
            criminal_keywords = ["criminal", "sentencing", "prison", "police", "prosecution", "jury", "forensic", "fourth amendment"]
            
            if not any(kw in title_lower for kw in criminal_keywords):
                filtered_count += 1
                print(f"    ✗ Not criminal justice: {item['title'][:50]}...")
                continue
            
            # 匹配到高质量研究
            new_items.append({
                "title": item["title"],
                "titleCN": item["title"],
                "url": item["url"],
                "date": item["date"],
                "journal": source,
                "summaryCN": f"发表在{source}上的刑事司法实证研究。",
                "summaryEN": f"Empirical research on criminal justice published in {source}.",
                "whyMattersCN": "该研究对理解美国刑事司法实践具有学术价值，其研究方法和发现可为中国相关领域的比较研究和制度完善提供参考。",
                "whyMattersEN": "This research offers academic value for understanding U.S. criminal justice practice.",
                "tags": [{"name": "刑事司法", "class": "criminal"}],
                "quality_score": 8
            })
            print(f"    ✓ Included: {item['title'][:50]}...")
            
            # 研究论文限制更严格
            if len(new_items) >= 3:
                print(f"  ⏹ Reached daily limit (3 papers)")
                break
        
        if len(new_items) >= 3:
            break
    
    data["research"].extend(new_items)
    data["research"].sort(key=lambda x: x["date"], reverse=True)
    data["research"] = data["research"][:10]  # 保留最近10篇高质量论文
    
    print(f"  +{len(new_items)} new research items")
    print(f"  -{filtered_count} filtered")
    return data

def main():
    print("="*60)
    print("🤖 Brief Auto-Updater v4.5 - Quality-First Edition")
    print("="*60)
    print("\nQuality Standards:")
    print("  • No generic fallbacks - skip if no match")
    print("  • Strict keyword matching for quality patterns")
    print("  • Max 5 news + 3 research per day")
    print("  • Only high-confidence matches included")
    
    data = load_data()
    print(f"\n📊 Current: {len(data.get('news', []))} news, {len(data.get('research', []))} papers")
    
    data = update_news(data)
    data = update_research(data)
    
    save_data(data)
    print(f"\n✅ Saved")
    print(f"📈 Total: {len(data['news'])} news, {len(data['research'])} papers")
    
    # 输出质量统计
    news_scores = [n.get("quality_score", 0) for n in data["news"]]
    research_scores = [r.get("quality_score", 0) for r in data["research"]]
    if news_scores:
        print(f"📊 Avg news quality: {sum(news_scores)/len(news_scores):.1f}/10")
    if research_scores:
        print(f"📊 Avg research quality: {sum(research_scores)/len(research_scores):.1f}/10")

if __name__ == "__main__":
    main()
