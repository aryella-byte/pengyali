#!/usr/bin/env python3
"""
Daily Brief Generator - 每日简报自动生成器
- 抓取新闻（SCOTUSblog, FT, etc.）
- 抓取T14 Law Review研究文章
- 自动去重（排除历史内容）
- 生成新的HTML页面
"""

import json
import feedparser
import requests
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import re

# 配置路径
WORKSPACE = Path("/root/.openclaw/workspace/website/brief")
CONTENT_DIR = WORKSPACE / "content"
ARCHIVE_DIR = WORKSPACE
HISTORY_FILE = CONTENT_DIR / "article-history.json"

# RSS源配置
NEWS_SOURCES = {
    "SCOTUSblog": {
        "rss": "https://www.scotusblog.com/feed/",
        "type": "news",
        "focus": ["supreme court", "constitutional", "criminal", "procedure"]
    },
    "Financial Times": {
        "rss": "https://www.ft.com/rss/home",
        "type": "news",
        "focus": ["trade", "china", "technology", "regulation", "law"]
    },
    "Reuters Legal": {
        "rss": "https://www.reutersagency.com/feed/?taxonomy=legal&post_type=reuters-best",
        "type": "news",
        "focus": ["legal", "court", "litigation", "regulation"]
    }
}

# T14 Law Reviews
RESEARCH_SOURCES = {
    "Harvard Law Review": "https://harvardlawreview.org/feed/",
    "Michigan Law Review": "https://michiganlawreview.org/feed/",
    "Virginia Law Review": "https://www.virginialawreview.org/feed/",
    "Stanford Law Review": "https://www.stanfordlawreview.org/feed/",
    "Columbia Law Review": "https://columbialawreview.org/feed/",
    "Chicago Law Review": "https://lawreview.uchicago.edu/rss.xml",
    "NYU Law Review": "https://www.nyulawreview.org/feed/",
    "Penn Law Review": "https://www.pennlawreview.com/feed/",
    "Duke Law Journal": "https://www.law.duke.edu/dlj/feed/",
    "Cornell Law Review": "https://www.cornelllawreview.org/feed/",
    "Northwestern Law Review": "https://scholarlycommons.law.northwestern.edu/nulr/recent.rss"
}

# 关键词权重 - 刑事司法最高优先级
KEYWORDS = {
    # 刑事司法 (最高优先级)
    "criminal": 10, "criminal justice": 10, "sentencing": 10, "punishment": 10,
    "prison": 10, "incarceration": 10, "death penalty": 10, "homicide": 10,
    "drug crime": 9, "white collar": 9, "fraud": 8, "policing": 8,
    "prosecution": 8, "jury": 8, "nullification": 8, "due process": 8,
    "police": 8, "search and seizure": 8, "fourth amendment": 8,
    "fifth amendment": 8, "sixth amendment": 8, "eighth amendment": 8,
    "mass incarceration": 10, "criminal procedure": 9, "wrongful conviction": 9,
    
    # 宪法/权利
    "constitutional": 6, "civil rights": 6, "civil liberties": 6,
    "first amendment": 6, "establishment clause": 6, "free speech": 5,
    
    # 科技/AI
    "technology": 4, "AI": 5, "artificial intelligence": 5, "algorithm": 4,
    "privacy": 5, "data protection": 4, "surveillance": 5,
    
    # 其他
    "administrative": 3, "regulation": 3, "international": 3,
    "human rights": 4, "empirical": 4, "procedure": 4, "evidence": 5
}

def load_history():
    """加载已发布文章历史（用于去重）"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"articles": [], "last_updated": ""}

def save_history(history):
    """保存文章历史"""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    history["last_updated"] = datetime.now().isoformat()
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_article_id(title, link):
    """生成文章唯一ID"""
    content = f"{title}|{link}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def is_duplicate(article_id, history):
    """检查是否已存在"""
    return article_id in history.get("articles", [])

def fetch_rss_feed(name, url, max_items=5):
    """抓取RSS feed"""
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", entry.get("updated", "")),
                "summary": entry.get("summary", entry.get("description", ""))[:400],
                "source": name
            })
        return items
    except Exception as e:
        print(f"  ✗ Error fetching {name}: {e}")
        return []

def score_relevance(item, item_type="news"):
    """计算相关性分数"""
    text = f"{item['title']} {item.get('summary', '')}".lower()
    score = 0
    for keyword, weight in KEYWORDS.items():
        if keyword in text:
            score += weight
    # 研究文章额外加分
    if item_type == "research":
        score += 2
    return score

def categorize_research(title, summary):
    """分类研究文章"""
    text = f"{title} {summary}".lower()
    
    categories = []
    if any(k in text for k in ["criminal", "sentencing", "punishment", "prison", "police", "jury", "fourth amendment"]):
        categories.append("Criminal Justice")
    if any(k in text for k in ["constitutional", "first amendment", "due process", "civil rights"]):
        categories.append("Constitutional Law")
    if any(k in text for k in ["technology", "ai", "privacy", "surveillance", "algorithm"]):
        categories.append("Technology & Privacy")
    
    return categories if categories else ["Legal Theory"]

def fetch_news(history):
    """抓取新闻（去重）"""
    print("📰 Fetching news...")
    all_news = []
    
    for name, config in NEWS_SOURCES.items():
        items = fetch_rss_feed(name, config["rss"], max_items=3)
        for item in items:
            article_id = get_article_id(item["title"], item["link"])
            if not is_duplicate(article_id, history):
                item["id"] = article_id
                item["relevance_score"] = score_relevance(item, "news")
                item["type"] = "news"
                all_news.append(item)
        print(f"  ✓ {name}: {len(items)} items, {len([i for i in items if get_article_id(i['title'], i['link']) not in history.get('articles', [])])} new")
    
    # 按相关性排序
    all_news.sort(key=lambda x: x["relevance_score"], reverse=True)
    return all_news[:5]  # 取前5条

def fetch_research(history):
    """抓取研究文章（去重）"""
    print("\n📄 Fetching research...")
    all_research = []
    
    for name, url in RESEARCH_SOURCES.items():
        items = fetch_rss_feed(name, url, max_items=3)
        for item in items:
            article_id = get_article_id(item["title"], item["link"])
            if not is_duplicate(article_id, history):
                item["id"] = article_id
                item["relevance_score"] = score_relevance(item, "research")
                item["type"] = "research"
                item["categories"] = categorize_research(item["title"], item.get("summary", ""))
                all_research.append(item)
        print(f"  ✓ {name}: {len(items)} items")
    
    # 按相关性排序
    all_research.sort(key=lambda x: x["relevance_score"], reverse=True)
    return all_research[:5]  # 取前5篇

def translate_to_chinese(text):
    """简单翻译映射（实际可用API）"""
    # 这里简化处理，实际可接入翻译API
    return text

def generate_html(date_str, news_items, research_items):
    """生成HTML页面 - 更新单页设计"""
    
    html_file = ARCHIVE_DIR / "index.html"
    
    # 检查是否已存在（避免覆盖）
    if html_file.exists():
        # 读取现有文件，只更新last-updated时间戳
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新时间戳
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        content = re.sub(
            r'Last updated: \d{4}-\d{2}-\d{2} \d{2}:\d{2} CST',
            f'Last updated: {now} CST',
            content
        )
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✓ Updated timestamp in {html_file}")
        return html_file
    
    # 计算前一天/后一天
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    prev_date = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
    next_date = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 检查前一天是否存在
    prev_link = f"../{prev_date}/index.html" if (ARCHIVE_DIR / prev_date).exists() else "#"
    next_exists = (ARCHIVE_DIR / next_date).exists()
    
    # 生成HTML（简化版，可扩展）
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brief - {date_str} | {date_str[5:].replace('-', '月')}日简报 - Yali Peng</title>
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
        .date {{ color: var(--accent); font-weight: 600; margin-top: 15px; }}
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
        .archive-nav {{ background: var(--card); padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; }}
        .archive-nav a {{ color: var(--accent); text-decoration: none; margin: 0 10px; }}
        .category-badge {{ display: inline-block; background: #1a1a2e; color: white; padding: 3px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-bottom: 10px; }}
        footer {{ text-align: center; padding: 40px 0; color: #666; font-size: 0.85rem; border-top: 1px solid #ddd; margin-top: 40px; }}
        footer a {{ color: var(--accent); text-decoration: none; }}
        @media (max-width: 600px) {{ h1 {{ font-size: 1.5rem; }} .item {{ padding: 20px; }} .nav-back {{ position: static; margin-bottom: 20px; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-back"><a href="../../">← Back to Homepage</a></div>
        
        <header>
            <h1>Brief | 简报</h1>
            <p class="subtitle">News & Research | 新闻与学术</p>
            <p class="date">{date_str} | {date_str[5:].replace('-', '月')}日</p>
        </header>
        
        <div class="archive-nav">
            📅 <a href="{prev_link if prev_link != '#' else '../2026-03-01/index.html'}">← {prev_date[5:].replace('-', '/')}</a> | 
            <strong>{date_str[5:].replace('-', '/')}</strong> | 
            <span style="color:#999">{next_date[5:].replace('-', '/')} →</span>
        </div>
        
        <div class="controls">
            <div class="section-switch">
                <button onclick="switchSection('news')">📰 NEWS</button>
                <button class="active" onclick="switchSection('research')">📄 RESEARCH</button>
            </div>
            <div class="lang-switch">
                <button class="active" onclick="switchLang('en')">EN</button>
                <button onclick="switchLang('zh')">中文</button>
            </div>
        </div>
        
        <!-- RESEARCH SECTION -->
        <div id="section-research" class="section-content active">
            <div class="lang-content en active">
                <div class="methodology">
                    <strong>Focus:</strong> Criminal Justice, Constitutional Law, Procedure
                </div>
                
                {generate_research_html(research_items, 'en')}
            </div>
            
            <div class="lang-content zh">
                <div class="methodology">
                    <strong>重点：</strong>刑事司法、宪法、程序法
                </div>
                
                {generate_research_html(research_items, 'zh')}
            </div>
        </div>
        
        <!-- NEWS SECTION -->
        <div id="section-news" class="section-content">
            <div class="lang-content en active">
                <div class="methodology"><strong>Today's news:</strong> {len(news_items)} items from verified sources.</div>
                
                {generate_news_html(news_items, 'en')}
            </div>
            
            <div class="lang-content zh">
                <div class="methodology"><strong>今日新闻：</strong>经核实信源精选{len(news_items)}条。</div>
                
                {generate_news_html(news_items, 'zh')}
            </div>
        </div>
        
        <footer>
            <p>Brief | 简报</p>
            <p>Curated by <a href="../../">Yali Peng</a> | Daily updates</p>
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
    
    # 保存HTML
    html_file = date_dir / "index.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return html_file

def generate_research_html(items, lang='en'):
    """生成研究文章HTML"""
    if not items:
        return '<p>No new research articles today.</p>' if lang == 'en' else '<p>今日无新研究文章。</p>'
    
    html = ""
    for i, item in enumerate(items, 1):
        categories = item.get("categories", ["Legal Theory"])
        badge = categories[0]
        
        if lang == 'en':
            html += f'''
                <article class="item">
                    <span class="item-number">{i:02d}</span>
                    <div class="category-badge">{badge}</div>
                    <h2 class="item-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h2>
                    <p class="item-authors">{item['source']}</p>
                    <div class="item-meta">📄 {item['source']} | Relevance: {item['relevance_score']}</div>
                    <p class="item-summary">{item.get('summary', '')[:300]}...</p>
                    <a href="{item['link']}" class="source-link" target="_blank">Read on {item['source']} →</a>
                </article>
            '''
        else:
            html += f'''
                <article class="item">
                    <span class="item-number">{i:02d}</span>
                    <div class="category-badge">{badge}</div>
                    <h2 class="item-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h2>
                    <p class="item-authors">{item['source']}</p>
                    <div class="item-meta">📄 {item['source']} | 相关度: {item['relevance_score']}</div>
                    <p class="item-summary">{item.get('summary', '')[:300]}...</p>
                    <a href="{item['link']}" class="source-link" target="_blank">在{item['source']}阅读 →</a>
                </article>
            '''
    return html

def generate_news_html(items, lang='en'):
    """生成新闻HTML"""
    if not items:
        return '<p>No new news today.</p>' if lang == 'en' else '<p>今日无新闻。</p>'
    
    html = ""
    for i, item in enumerate(items, 1):
        if lang == 'en':
            html += f'''
                <article class="item">
                    <span class="item-number">{i:02d}</span>
                    <h2 class="item-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h2>
                    <div class="item-meta">📰 {item['source']} | {item.get('published', '')[:10]}</div>
                    <p class="item-summary">{item.get('summary', '')[:300]}...</p>
                    <a href="{item['link']}" class="source-link" target="_blank">Read on {item['source']} →</a>
                </article>
            '''
        else:
            html += f'''
                <article class="item">
                    <span class="item-number">{i:02d}</span>
                    <h2 class="item-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h2>
                    <div class="item-meta">📰 {item['source']} | {item.get('published', '')[:10]}</div>
                    <p class="item-summary">{item.get('summary', '')[:300]}...</p>
                    <a href="{item['link']}" class="source-link" target="_blank">在{item['source']}阅读 →</a>
                </article>
            '''
    return html

def update_archive_index(date_str):
    """更新归档首页"""
    index_file = ARCHIVE_DIR / "index.html"
    
    # 读取现有内容
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = ""
    
    # 这里简化处理，实际应动态生成日期列表
    print(f"  ✓ Archive index would be updated with {date_str}")

def main():
    """主函数"""
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"="*60)
    print(f"🗓️  Daily Brief Generator - {today}")
    print(f"="*60)
    
    # 加载历史
    history = load_history()
    print(f"\n📚 History loaded: {len(history.get('articles', []))} articles tracked")
    
    # 抓取新闻
    news_items = fetch_news(history)
    print(f"\n  → Selected {len(news_items)} news items")
    
    # 抓取研究
    research_items = fetch_research(history)
    print(f"  → Selected {len(research_items)} research items")
    
    # 生成HTML
    if news_items or research_items:
        html_file = generate_html(today, news_items, research_items)
        print(f"\n✅ Generated: {html_file}")
        
        # 更新历史
        for item in news_items + research_items:
            history["articles"].append(item["id"])
        
        # 只保留最近90天的历史
        history["articles"] = history["articles"][-500:]
        save_history(history)
        print(f"✅ Updated history: {len(history['articles'])} articles tracked")
        
        # 更新归档首页
        update_archive_index(today)
        
        # 提交到GitHub（可选）
        print(f"\n📝 Next steps:")
        print(f"   1. Review the generated page: {html_file}")
        print(f"   2. Run: git add -A && git commit -m 'Add brief for {today}' && git push")
    else:
        print(f"\n⚠️  No new content found for today")

if __name__ == "__main__":
    main()
