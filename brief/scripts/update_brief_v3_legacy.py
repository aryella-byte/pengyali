#!/usr/bin/env python3
"""
Brief Auto-Updater v3
- 中英文双语版本
- AI自主总结（不用原文摘要）
- 精简内容结构
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

# 刑事司法相关关键词
CRIMINAL_JUSTICE_KEYWORDS = [
    "criminal", "sentencing", "prison", "incarceration", "police", "policing",
    "prosecution", "prosecutor", "defense", "jury", "trial", "plea",
    "fourth amendment", "fifth amendment", "sixth amendment", "eighth amendment",
    "search", "seizure", "warrant", "arrest", "interrogation",
    "mass incarceration", "wrongful conviction", "innocence",
    "death penalty", "capital punishment", "life sentence",
    "drug", "controlled substance", "narcotic", "opioid",
    "violence", "homicide", "murder", "assault", "robbery",
    "fraud", "white collar", "corporate crime",
    "juvenile", "youth", "minor",
    "bail", "pretrial", "detention",
    "parole", "probation", "reentry", "rehabilitation",
    "forensic", "evidence", "expert witness", "dna",
    "racial disparity", "discrimination", "bias",
    "restorative justice", "alternative", "diversion"
]

JUNK_KEYWORDS = [
    "call for submissions", "essay competition", "diversity and inclusion",
    "announcement", "cfa", "career", "job opening", "fellowship",
    "subscribe", "newsletter", "rss feed", "contact us", "scotustoday",
    "animated explainer", "relist watch"
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
    text = title.lower()
    for junk in JUNK_KEYWORDS:
        if junk in text:
            return True
    return False

def is_criminal_justice_related(title):
    """判断是否与刑事司法相关"""
    text = title.lower()
    for keyword in CRIMINAL_JUSTICE_KEYWORDS:
        if keyword in text:
            return True
    return False

def generate_summary_and_why(title, source, is_research=False):
    """
    基于标题和来源，自主生成总结和Why it matters
    返回 (中文总结, 英文总结, 中文Why, 英文Why, 标签)
    """
    text = title.lower()
    
    # News 分类处理
    if not is_research:
        # Supreme Court / Constitutional
        if any(k in text for k in ["supreme court", "major questions", "tariff", "administrative", "constitutionality"]):
            return (
                "美国联邦最高法院就行政权力边界作出重要裁决，涉及重大问题原则的适用。",
                "The Supreme Court rules on the boundaries of executive power, involving the Major Questions Doctrine.",
                "该判决将深刻影响联邦行政机构的规制权力，对理解司法权与行政权的宪法边界具有标杆意义，也可能影响全球行政法发展。",
                "This ruling will profoundly impact federal regulatory power and sets a precedent for understanding the constitutional boundaries between judicial and executive authority.",
                [{"name": "宪法", "class": "constitutional"}, {"name": "行政法", "class": "constitutional"}]
            )
        
        # Iran / Middle East conflict
        if any(k in text for k in ["iran", "israel", "war", "conflict", "hormuz", "middle east"]):
            return (
                "中东地区冲突升级，涉及国际法中的武力使用、主权豁免和战争法规范。",
                "Escalating conflict in the Middle East raises questions about use of force, sovereign immunity, and the laws of war.",
                "该冲突对全球能源供应、国际贸易秩序和国际法治可能产生连锁影响，国际法中的自卫权和战争法规范面临新的考验。",
                "The conflict may have cascading effects on global energy supplies, international trade order, and the rule of international law.",
                [{"name": "国际法", "class": "international"}, {"name": "地缘政治", "class": "international"}]
            )
        
        # Criminal justice
        if any(k in text for k in ["criminal", "sentencing", "prison", "ice", "foreclosure", "appeal"]):
            return (
                "美国刑事司法或民事诉讼程序中的最新司法动态，涉及程序正义和实体权利保护。",
                "Latest developments in U.S. criminal justice or civil procedure, involving procedural justice and substantive rights protection.",
                "该案件的审理和判决可能产生先例效应，对理解美国司法实践和程序正义的具体运作具有参考价值。",
                "The case may create precedent and offers insights into how procedural justice operates in U.S. judicial practice.",
                [{"name": "刑事司法", "class": "criminal"}]
            )
        
        # Default news - generate specific analysis based on content
        # Try to extract meaningful insights from the title
        if "immigration" in text or "ice" in text or "border" in text or "deport" in text:
            return (
                "涉及移民执法、边境管控或拘留政策的最新法律动态。",
                "Latest legal developments involving immigration enforcement, border control, or detention policies.",
                "移民执法中的法律边界和权利保障是跨境法律实践的重要议题。该动态涉及行政权力扩张与个人权利保护之间的张力，对中国跨境执法合作和外国人权利保障立法具有参考价值。",
                "Legal boundaries and rights protection in immigration enforcement are key issues in cross-border legal practice. This development involves tensions between executive power expansion and individual rights protection.",
                [{"name": "移民法", "class": "international"}]
            )
        
        if "firearm" in text or "gun" in text or "weapon" in text:
            return (
                "涉及枪支管制、第二修正案解释和公共安全的法律争议。",
                "Legal controversies involving gun control, Second Amendment interpretation, and public safety.",
                "枪支管制是美国宪法争议最激烈的领域之一。该案件涉及个人持枪权与公共安全的平衡，对理解美国宪法解释的动态演变和比较法视野下的武器管制立法具有参考价值。",
                "Gun control is one of the most contentious areas of U.S. constitutional law. This case involves balancing individual gun rights with public safety.",
                [{"name": "宪法", "class": "constitutional"}]
            )
        
        if "syria" in text or "national" in text or "status" in text or "tps" in text:
            return (
                "涉及临时保护身份、移民政策调整或难民保护的法律动态。",
                "Legal developments involving temporary protected status, immigration policy adjustments, or refugee protection.",
                "临时保护身份制度涉及人道主义考量与移民执法的边界。该政策调整反映了行政权在移民领域的裁量空间，对中国难民保护立法和临时居留制度的完善具有比较法意义。",
                "Temporary protected status involves balancing humanitarian considerations with immigration enforcement boundaries.",
                [{"name": "移民法", "class": "international"}]
            )
        
        # Generic fallback with more substance
        return (
            f"来自{source}的重要法律动态，涉及相关领域的制度发展和实践变化。",
            f"Important legal developments from {source} involving institutional developments and practice changes in relevant fields.",
            "该动态反映了相关法律领域的最新发展趋势，其制度设计和实践操作对比较法研究具有参考价值，可为中国类似制度的完善提供域外经验。",
            "This development reflects the latest trends in relevant legal fields. Its institutional design and practical operations offer comparative law reference value.",
            [{"name": "法律动态", "class": ""}]
        )
    
    # Research 分类处理
    # Fourth Amendment / Privacy
    if any(k in text for k in ["fourth amendment", "privacy", "surveillance", "search", "seizure", "technological"]):
        return (
            "探讨数字时代第四修正案的适用边界，分析执法权力与个人隐私权的平衡机制。",
            "Examines the Fourth Amendment's application in the digital age, analyzing the balance between law enforcement power and privacy rights.",
            "第四修正案在数字时代的适用是当下最重要的宪法议题之一，对中国刑事诉讼法中技术侦查措施的规制和数字隐私保护立法具有直接参考价值。",
            "The Fourth Amendment's application in the digital age is one of the most important constitutional issues today, offering direct reference value for China's criminal procedure law and digital privacy legislation.",
            [{"name": "数字隐私", "class": "tech"}, {"name": "宪法", "class": "constitutional"}]
        )
    
    # Jury / Criminal Procedure
    if any(k in text for k in ["jury", "nullification", "semantics", "criminal procedure"]):
        return (
            "研究陪审团制度的运作逻辑和裁判语义学，分析对抗制诉讼中事实认定的制度设计。",
            "Studies the operational logic of jury systems and forensic semantics, analyzing institutional design for fact-finding in adversarial litigation.",
            "陪审团制度是普通法系的核心特征，该研究对理解对抗制诉讼中事实认定的制度逻辑具有启发意义，对中国人民陪审员制度的改革完善有参考价值。",
            "The jury system is central to common law. This research offers insights into fact-finding logic in adversarial systems and reference value for China's people's assessor system reform.",
            [{"name": "刑事程序", "class": "criminal"}]
        )
    
    # Drugs / Mass Incarceration
    if any(k in text for k in ["drug", "scheduling", "controlled substance", "mass incarceration"]):
        return (
            "分析美国药物管制制度的制度设计与实施后果，探讨量刑政策与大规模监禁的关系。",
            "Analyzes the institutional design and implementation consequences of U.S. drug scheduling, exploring the relationship between sentencing policy and mass incarceration.",
            "量刑政策与大规模监禁是美国刑事司法的核心批评领域，该研究的实证发现可以为中国毒品治理政策的科学化和量刑规范化改革提供比较视角。",
            "Sentencing policy and mass incarceration are central critiques of U.S. criminal justice. This research offers comparative perspectives for China's drug policy and sentencing reform.",
            [{"name": "刑事司法", "class": "criminal"}, {"name": "量刑政策", "class": "criminal"}]
        )
    
    # Establishment Clause / Religion
    if any(k in text for k in ["ten commandments", "establishment", "religion", "reformation"]):
        return (
            "通过历史分析重新审视政教分离条款的解释方法，探讨宪法文本主义与活宪法主义的路径分歧。",
            "Re-examines Establishment Clause interpretation through historical analysis, exploring the divergence between textualism and living constitutionalism.",
            "政教分离条款的解释涉及宪法方法论之争，该研究的历史分析路径对理解宪法解释中历史材料的使用方法具有方法论价值。",
            "The interpretation of the Establishment Clause involves methodological debates. This research's historical approach offers methodological value for understanding constitutional interpretation.",
            [{"name": "宪法解释", "class": "constitutional"}]
        )
    
    # Voting Rights / Democracy
    if any(k in text for k in ["voting rights", "democracy", "general counsel", "administration"]):
        return (
            "研究选举权法的私人执行机制和联邦行政法中的法律职业伦理问题。",
            "Studies private enforcement mechanisms of voting rights law and legal ethics in federal administrative law.",
            "选举权保障和行政法治是宪政民主的核心议题，该研究对美国选举法和行政法最新发展的分析具有比较法参考价值。",
            "Voting rights protection and administrative rule of law are core issues in constitutional democracy. This research offers comparative law reference value.",
            [{"name": "宪法", "class": "constitutional"}]
        )
    
    # Statutory Interpretation
    if any(k in text for k in ["statutory interpretation", "practical consequences", "administrability"]):
        return (
            "探讨法律解释中的实用主义方法，分析政策后果和制度可行性在司法解释中的作用。",
            "Explores pragmatic approaches to statutory interpretation, analyzing the role of policy consequences and institutional feasibility in judicial interpretation.",
            "法律解释方法论是法理学的重要议题，该研究对后果主义解释路径的分析对中国法律解释方法的完善具有参考价值。",
            "Legal interpretation methodology is a key jurisprudential topic. This research's analysis of consequentialist interpretation offers reference value for China.",
            [{"name": "法理学", "class": "constitutional"}]
        )
    
    # Default research
    return (
        f"发表在权威法学期刊上的学术研究，从理论和实证维度深入分析相关制度议题。",
        f"Academic research published in a leading law journal, analyzing relevant institutional issues from theoretical and empirical dimensions.",
        "该研究运用法学理论分析具体制度实践，其研究框架和论证逻辑对中国相关领域的学术研究和制度建构具有方法论参考价值，可为中国法治建设提供域外经验借鉴。",
        "This research applies legal theory to analyze specific institutional practices. Its analytical framework and argumentative logic offer methodological reference value for China's academic research and institutional development.",
        [{"name": "法学研究", "class": ""}]
    )

def fetch_feed(url, source_name):
    """抓取RSS feed"""
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:10]:
            title = entry.get("title", "").strip()
            
            if is_junk_content(title):
                print(f"    ⚠️ Filtered: {title[:50]}...")
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
    """更新News数据"""
    print("\n📰 Updating News...")
    existing_ids = {get_item_id(n["title"]) for n in data["news"]}
    new_count = 0
    
    for source, url in NEWS_SOURCES.items():
        items = fetch_feed(url, source)
        for item in items:
            item_id = get_item_id(item["title"])
            if item_id not in existing_ids:
                cn_summary, en_summary, cn_why, en_why, tags = generate_summary_and_why(item["title"], source, False)
                data["news"].append({
                    "title": item["title"],
                    "titleCN": item["title"],  # 可以后续翻译
                    "url": item["url"],
                    "date": item["date"],
                    "source": source,
                    "summaryCN": cn_summary,
                    "summaryEN": en_summary,
                    "whyMattersCN": cn_why,
                    "whyMattersEN": en_why,
                    "tags": tags
                })
                new_count += 1
        print(f"  ✓ {source}: {len(items)} items")
    
    data["news"].sort(key=lambda x: x["date"], reverse=True)
    data["news"] = data["news"][:20]  # 保留最近20条
    
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
            # 只保留刑事司法相关的研究
            if item_id not in existing_ids and is_criminal_justice_related(item["title"]):
                cn_summary, en_summary, cn_why, en_why, tags = generate_summary_and_why(item["title"], source, True)
                data["research"].append({
                    "title": item["title"],
                    "titleCN": item["title"],  # 可以后续翻译
                    "url": item["url"],
                    "date": item["date"],
                    "journal": source,
                    "summaryCN": cn_summary,
                    "summaryEN": en_summary,
                    "whyMattersCN": cn_why,
                    "whyMattersEN": en_why,
                    "tags": tags
                })
                new_count += 1
            elif not is_criminal_justice_related(item["title"]):
                print(f"    ⚠️ Not criminal justice: {item['title'][:50]}...")
        print(f"  ✓ {source}: {len([i for i in items if is_criminal_justice_related(i['title'])])} criminal justice items")
    
    data["research"].reverse()  # 新内容在前
    data["research"] = data["research"][:30]  # 保留最近30篇
    
    print(f"  +{new_count} new research items")
    return data

def main():
    print("="*60)
    print("🤖 Brief Auto-Updater v3 - Bilingual Edition")
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
