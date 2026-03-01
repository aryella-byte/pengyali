#!/usr/bin/env python3
"""
Auto Brief Generator - 全自动简报生成器
- 自动抓取新闻和研究文章
- AI筛选和摘要
- 自动生成Why this matters
- 更新单页HTML
- 自动提交GitHub
"""

import json
import feedparser
import re
from datetime import datetime
from pathlib import Path
import hashlib
import subprocess

# 路径配置
WORKSPACE = Path("/root/.openclaw/workspace/website/brief")
HISTORY_FILE = WORKSPACE / "content" / "article-history.json"
INDEX_FILE = WORKSPACE / "index.html"
TEMPLATE_FILE = WORKSPACE / "templates" / "brief-template.html"

# 精选信源
SOURCES = {
    # 新闻
    "SCOTUSblog": {
        "url": "https://www.scotusblog.com/feed/",
        "type": "news",
        "priority": ["supreme court", "constitutional", "criminal"]
    },
    "Financial Times": {
        "url": "https://www.ft.com/rss/home",
        "type": "news",
        "priority": ["trade", "china", "technology", "regulation"]
    },
    "Reuters Legal": {
        "url": "https://www.reutersagency.com/feed/?taxonomy=legal&post_type=reuters-best",
        "type": "news",
        "priority": ["legal", "court", "litigation"]
    },
    # 研究
    "Harvard Law Review": {
        "url": "https://harvardlawreview.org/feed/",
        "type": "research",
        "focus": ["criminal", "constitutional", "procedure"]
    },
    "Michigan Law Review": {
        "url": "https://michiganlawreview.org/feed/",
        "type": "research",
        "focus": ["criminal", "empirical", "procedure"]
    },
    "Virginia Law Review": {
        "url": "https://www.virginialawreview.org/feed/",
        "type": "research",
        "focus": ["criminal", "constitutional", "technology"]
    },
    "Stanford Law Review": {
        "url": "https://www.stanfordlawreview.org/feed/",
        "type": "research",
        "focus": ["technology", "privacy", "criminal"]
    },
    "Columbia Law Review": {
        "url": "https://columbialawreview.org/feed/",
        "type": "research",
        "focus": ["constitutional", "criminal", "human rights"]
    }
}

# 关键词权重
KEYWORDS = {
    # 刑事司法 (最高优先级)
    "criminal": 10, "criminal justice": 10, "sentencing": 10,
    "prison": 10, "incarceration": 10, "policing": 9,
    "prosecution": 8, "jury": 8, "fourth amendment": 8,
    "fifth amendment": 8, "sixth amendment": 8, "eighth amendment": 8,
    "mass incarceration": 10, "criminal procedure": 9,
    "wrongful conviction": 9, "drug policy": 8,
    
    # 宪法/权利
    "constitutional": 6, "civil rights": 6, "civil liberties": 6,
    "first amendment": 6, "due process": 7, "equal protection": 7,
    "establishment clause": 6, "free speech": 5,
    
    # 科技/隐私
    "technology": 4, "AI": 5, "artificial intelligence": 5,
    "privacy": 5, "surveillance": 5, "data protection": 4,
    "algorithm": 4, "cybersecurity": 4,
    
    # 国际/政治
    "international": 3, "human rights": 4, "trade": 3,
    "regulation": 3, "administrative": 3
}

def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {"articles": [], "last_updated": ""}

def save_history(history):
    history["last_updated"] = datetime.now().isoformat()
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def get_article_id(title, link):
    return hashlib.md5(f"{title}|{link}".encode()).hexdigest()[:12]

def fetch_feed(name, config):
    """抓取RSS feed"""
    try:
        feed = feedparser.parse(config["url"])
        items = []
        for entry in feed.entries[:5]:  # 取最近5篇
            items.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": re.sub(r'<[^>]+>', '', entry.get("summary", "")[:500]),
                "published": entry.get("published", entry.get("updated", "")),
                "source": name,
                "type": config["type"]
            })
        return items
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return []

def score_article(article):
    """计算文章相关分数"""
    text = f"{article['title']} {article.get('summary', '')}".lower()
    score = 0
    for keyword, weight in KEYWORDS.items():
        if keyword in text:
            score += weight
    return score

def categorize_article(article):
    """分类文章"""
    text = f"{article['title']} {article.get('summary', '')}".lower()
    
    categories = []
    if any(k in text for k in ["criminal", "sentencing", "prison", "police", "jury"]):
        categories.append("Criminal Justice")
    if any(k in text for k in ["constitutional", "first amendment", "due process", "civil rights"]):
        categories.append("Constitutional Law")
    if any(k in text for k in ["technology", "ai", "privacy", "surveillance"]):
        categories.append("Technology & Privacy")
    if any(k in text for k in ["international", "trade", "human rights"]):
        categories.append("International")
    
    return categories[0] if categories else "Legal Theory"

def generate_why_matters(article):
    """生成Why this matters (简化规则)"""
    title = article['title'].lower()
    summary = article.get('summary', '').lower()
    category = categorize_article(article)
    
    templates = {
        "Criminal Justice": [
            "This directly addresses systemic issues in criminal justice, examining how legal doctrine shapes real-world outcomes for defendants and communities.",
            "A critical examination of criminal procedure that challenges conventional assumptions about justice and punishment."
        ],
        "Constitutional Law": [
            "This analysis illuminates evolving constitutional doctrine with significant implications for individual rights and governmental power.",
            "An important contribution to constitutional interpretation that may influence future judicial decisions."
        ],
        "Technology & Privacy": [
            "As technology outpaces legal frameworks, this work offers essential guidance for balancing innovation with fundamental rights.",
            "This addresses urgent questions about privacy and surveillance in an increasingly digital society."
        ],
        "International": [
            "This development carries significant implications for international law, diplomacy, and global governance.",
            "A critical analysis of cross-border legal issues with far-reaching consequences."
        ],
        "Legal Theory": [
            "This scholarly work advances our understanding of fundamental legal principles and their practical application.",
            "An important theoretical contribution with potential to reshape how we think about this area of law."
        ]
    }
    
    import random
    return random.choice(templates.get(category, templates["Legal Theory"]))

def generate_news_html(items):
    """生成新闻HTML"""
    html = ""
    for i, item in enumerate(items[:3], 1):
        category = categorize_article(item)
        why = generate_why_matters(item)
        
        # 简化摘要
        summary = item.get('summary', '')[:200] + "..." if len(item.get('summary', '')) > 200 else item.get('summary', '')
        
        html += f'''
                <article class="item">
                    <span class="item-number">{i:02d}</span>
                    <div class="priority-badge">{category}</div>
                    <h2 class="item-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h2>
                    <p class="item-authors">{item['source']} | {item.get('published', '')[:10]}</p>
                    <div class="item-meta">📰 {item['source']} | 🏷️ {category}</div>
                    <div class="why-matters">
                        <div class="why-label">Why this matters</div>
                        <p>{why}</p>
                    </div>
                    <p class="item-summary">{summary}</p>
                    <a href="{item['link']}" class="source-link" target="_blank">Read on {item['source']} →</a>
                </article>
        '''
    return html

def generate_research_html(items):
    """生成研究HTML"""
    html = ""
    for i, item in enumerate(items[:3], 1):
        category = categorize_article(item)
        why = generate_why_matters(item)
        summary = item.get('summary', '')[:250] + "..." if len(item.get('summary', '')) > 250 else item.get('summary', '')
        
        html += f'''
                <article class="item">
                    <span class="item-number">{i:02d}</span>
                    <div class="category-badge">{category}</div>
                    <h2 class="item-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h2>
                    <p class="item-authors">{item['source']}</p>
                    <div class="item-meta">📄 {item['source']} | 🔑 {category}</div>
                    <div class="why-matters">
                        <div class="why-label">Why this matters</div>
                        <p>{why}</p>
                    </div>
                    <p class="item-summary">{summary}</p>
                    <a href="{item['link']}" class="source-link" target="_blank">Read on {item['source']} →</a>
                </article>
        '''
    return html

def build_full_html(news_items, research_items):
    """构建完整HTML页面"""
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 读取模板或构建新页面
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brief | 简报 - Yali Peng</title>
    <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Source+Sans+Pro:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{ --text: #1a1a1a; --accent: #8B0000; --bg: #fafafa; --card: #fff; --border: #e0e0e0; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Source Sans Pro', sans-serif; background: var(--bg); color: var(--text); line-height: 1.8; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
        header {{ text-align: center; padding: 40px 0; border-bottom: 2px solid var(--accent); margin-bottom: 30px; }}
        .nav-back {{ position: absolute; top: 20px; left: 20px; }}
        .nav-back a {{ color: #666; text-decoration: none; font-size: 0.9rem; }}
        h1 {{ font-family: 'Libre Baskerville', serif; font-size: 2rem; margin-bottom: 10px; }}
        .subtitle {{ color: #666; font-size: 0.95rem; }}
        .last-updated {{ color: var(--accent); font-weight: 600; margin-top: 15px; font-size: 0.9rem; }}
        .controls {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 15px; margin: 20px 0 30px; }}
        .controls button {{ background: none; border: 1px solid #ddd; padding: 8px 16px; cursor: pointer; font-size: 0.9rem; transition: all 0.3s; }}
        .controls button.active {{ background: var(--accent); color: white; border-color: var(--accent); }}
        .section-content, .lang-content {{ display: none; }}
        .section-content.active, .lang-content.active {{ display: block; }}
        .item {{ background: var(--card); border-radius: 8px; padding: 30px; margin-bottom: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
        .item-number {{ display: inline-block; background: var(--accent); color: white; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 50%; font-weight: 700; font-size: 0.85rem; margin-bottom: 15px; }}
        .item-title {{ font-family: 'Libre Baskerville', serif; font-size: 1.15rem; font-weight: 700; margin-bottom: 10px; line-height: 1.5; }}
        .item-title a {{ color: var(--text); text-decoration: none; border-bottom: 2px solid transparent; transition: border-color 0.2s; }}
        .item-title a:hover {{ border-bottom-color: var(--accent); }}
        .item-authors {{ font-size: 0.9rem; color: #666; margin-bottom: 8px; font-style: italic; }}
        .item-meta {{ font-size: 0.85rem; color: #666; margin-bottom: 15px; }}
        .why-matters {{ background: #f8f9fa; padding: 15px 20px; border-radius: 6px; margin: 15px 0; border-left: 3px solid var(--accent); }}
        .why-label {{ font-weight: 700; color: var(--accent); font-size: 0.8rem; text-transform: uppercase; margin-bottom: 8px; }}
        .item-summary {{ font-size: 0.95rem; line-height: 1.8; margin-top: 15px; }}
        .source-link {{ display: inline-block; margin-top: 12px; color: var(--accent); font-size: 0.85rem; text-decoration: none; }}
        .methodology {{ background: var(--card); padding: 20px; border-radius: 8px; margin-bottom: 30px; font-size: 0.9rem; color: #666; border-left: 3px solid var(--accent); }}
        .category-badge {{ display: inline-block; background: #1a1a2e; color: white; padding: 3px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-bottom: 10px; }}
        .priority-badge {{ display: inline-block; background: #8B0000; color: white; padding: 3px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-bottom: 10px; margin-right: 5px; }}
        footer {{ text-align: center; padding: 40px 0; color: #666; font-size: 0.85rem; border-top: 1px solid #ddd; margin-top: 40px; }}
        footer a {{ color: var(--accent); text-decoration: none; }}
        @media (max-width: 600px) {{ h1 {{ font-size: 1.5rem; }} .item {{ padding: 20px; }} .nav-back {{ position: static; margin-bottom: 20px; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-back"><a href="../">← Back to Homepage</a></div>
        
        <header>
            <h1>Brief | 简报</h1>
            <p class="subtitle">News & Research | 新闻与学术</p>
            <p class="last-updated">Last updated: {now} CST | 最后更新</p>
        </header>
        
        <div class="controls">
            <div class="section-switch">
                <button class="active" onclick="switchSection('news')">📰 NEWS</button>
                <button onclick="switchSection('research')">📄 RESEARCH</button>
            </div>
            <div class="lang-switch">
                <button class="active" onclick="switchLang('en')">EN</button>
                <button onclick="switchLang('zh')">中文</button>
            </div>
        </div>
        
        <div id="section-news" class="section-content active">
            <div class="lang-content en active">
                <div class="methodology"><strong>Today's focus:</strong> Law, International Relations, Technology Policy</div>
                {generate_news_html(news_items)}
            </div>
            <div class="lang-content zh">
                <div class="methodology"><strong>今日聚焦：</strong>法律、国际关系、科技政策</div>
                {generate_news_html(news_items).replace('Why this matters', '为什么重要').replace('Read on', '在').replace('→', '阅读 →')}
            </div>
        </div>
        
        <div id="section-research" class="section-content">
            <div class="lang-content en active">
                <div class="methodology"><strong>Focus:</strong> Criminal Justice, Constitutional Law, Procedure</div>
                {generate_research_html(research_items)}
            </div>
            <div class="lang-content zh">
                <div class="methodology"><strong>重点：</strong>刑事司法、宪法、程序法</div>
                {generate_research_html(research_items).replace('Why this matters', '为什么重要').replace('Read on', '在').replace('→', '阅读 →')}
            </div>
        </div>
        
        <footer>
            <p>Brief | 简报</p>
            <p>Curated by <a href="../">Yali Peng</a></p>
            <p style="margin-top: 10px; font-size: 0.8rem;">Daily updates on law, politics, and research | 每日法律、政治与学术更新</p>
        </footer>
    </div>
    
    <script>
        function switchSection(section) {{
            document.querySelectorAll('.section-content').forEach(el => el.classList.remove('active'));
            document.getElementById('section-' + section).classList.add('active');
            document.querySelectorAll('.section-switch button').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }}
        function switchLang(lang) {{
            document.querySelectorAll('.lang-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.section-content.active .lang-content.' + lang).forEach(el => el.classList.add('active'));
            document.querySelectorAll('.lang-switch button').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>'''
    
    return html

def git_commit_and_push():
    """提交到GitHub"""
    try:
        subprocess.run(["git", "add", "-A"], cwd=WORKSPACE.parent, check=True)
        subprocess.run([
            "git", "commit", "-m", 
            f"Auto-update brief - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ], cwd=WORKSPACE.parent, check=True)
        subprocess.run(["git", "push"], cwd=WORKSPACE.parent, check=True)
        print("  ✓ Committed and pushed to GitHub")
        return True
    except Exception as e:
        print(f"  ✗ Git error: {e}")
        return False

def main():
    print("="*60)
    print("🤖 Auto Brief Generator")
    print("="*60)
    
    history = load_history()
    tracked = set(history.get("articles", []))
    print(f"\n📚 Tracking {len(tracked)} articles")
    
    # 抓取所有源
    all_news = []
    all_research = []
    new_ids = []
    
    for name, config in SOURCES.items():
        items = fetch_feed(name, config)
        for item in items:
            aid = get_article_id(item['title'], item['link'])
            if aid not in tracked:
                item['id'] = aid
                item['score'] = score_article(item)
                new_ids.append(aid)
                if config['type'] == 'news':
                    all_news.append(item)
                else:
                    all_research.append(item)
        print(f"  ✓ {name}: {len([i for i in items if get_article_id(i['title'], i['link']) not in tracked])} new")
    
    # 排序并取前3
    all_news.sort(key=lambda x: x['score'], reverse=True)
    all_research.sort(key=lambda x: x['score'], reverse=True)
    
    selected_news = all_news[:3]
    selected_research = all_research[:3]
    
    print(f"\n📰 Selected {len(selected_news)} news items")
    print(f"📄 Selected {len(selected_research)} research items")
    
    if selected_news or selected_research:
        # 生成HTML
        html = build_full_html(selected_news, selected_research)
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n✅ Generated: {INDEX_FILE}")
        
        # 更新历史
        tracked.update(new_ids)
        history["articles"] = list(tracked)[-300:]  # 保留最近300条
        save_history(history)
        
        # 提交
        if git_commit_and_push():
            print("\n🎉 Auto-update completed successfully!")
        else:
            print("\n⚠️  Content updated but git push failed")
    else:
        print("\nℹ️  No new content found")

if __name__ == "__main__":
    main()
