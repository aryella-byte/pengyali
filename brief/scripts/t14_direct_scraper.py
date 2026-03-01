#!/usr/bin/env python3
"""
T14 Direct Scraper - 直接抓取无RSS的T14期刊
备用方案：当Apify不可用时使用requests+BeautifulSoup
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import json
import hashlib

# 目标期刊
TARGETS = {
    "Yale Law Journal": {
        "url": "https://www.yalelawjournal.org/",
        "article_selector": "article.post, .article-preview, a[href*='/article/']",
        "title_selector": "h1, h2, .article-title",
        "base_url": "https://www.yalelawjournal.org"
    },
    "Berkeley Law Review": {
        "url": "https://www.law.berkeley.edu/research/boalt-law-review/",
        "article_selector": ".article, .post, a[href*='/article/']", 
        "title_selector": "h1, h2, .entry-title",
        "base_url": "https://www.law.berkeley.edu"
    },
    "Georgetown Law Journal": {
        "url": "https://www.georgetownlawjournal.org/",
        "article_selector": "article, .article-card, a[href*='/article/']",
        "title_selector": "h1, h2, .article-title",
        "base_url": "https://www.georgetownlawjournal.org"
    }
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def fetch_page(url):
    """抓取页面"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"    ✗ Error fetching {url}: {e}")
        return None

def parse_yale_law_journal(html):
    """解析Yale Law Journal"""
    soup = BeautifulSoup(html, 'html.parser')
    articles = []
    
    # Yale Law Journal的文章通常在article标签或特定class中
    for article in soup.find_all(['article', 'div'], class_=lambda x: x and ('post' in x or 'article' in x)):
        title_elem = article.find(['h1', 'h2', 'h3', 'a'])
        link_elem = article.find('a', href=True)
        
        if title_elem and link_elem:
            title = title_elem.get_text(strip=True)
            link = link_elem['href']
            if link.startswith('/'):
                link = f"https://www.yalelawjournal.org{link}"
            
            # 排除非文章链接
            if '/article/' in link or '/essay/' in link:
                articles.append({
                    'title': title,
                    'link': link,
                    'source': 'Yale Law Journal',
                    'type': 'research'
                })
    
    return articles[:5]  # 只取前5篇

def parse_berkeley_law_review(html):
    """解析Berkeley Law Review"""
    soup = BeautifulSoup(html, 'html.parser')
    articles = []
    
    # Berkeley Law Review的文章结构
    for article in soup.find_all(['article', 'div'], class_=lambda x: x and ('article' in x or 'entry' in x or 'post' in x)):
        title_elem = article.find(['h1', 'h2', 'h3'])
        link_elem = article.find('a', href=True)
        
        if title_elem:
            title = title_elem.get_text(strip=True)
            link = link_elem['href'] if link_elem else ''
            if link.startswith('/'):
                link = f"https://www.boalt.org{link}"
            
            if title and len(title) > 20:  # 过滤掉短标题
                articles.append({
                    'title': title,
                    'link': link,
                    'source': 'Berkeley Law Review',
                    'type': 'research'
                })
    
    return articles[:5]

def parse_georgetown_law_journal(html):
    """解析Georgetown Law Journal"""
    soup = BeautifulSoup(html, 'html.parser')
    articles = []
    
    # Georgetown Law Journal的文章
    for article in soup.find_all(['article', 'div'], class_=lambda x: x and ('article' in x or 'post' in x)):
        title_elem = article.find(['h1', 'h2', 'h3'])
        link_elem = article.find('a', href=True)
        
        if title_elem:
            title = title_elem.get_text(strip=True)
            link = link_elem['href'] if link_elem else ''
            if link.startswith('/'):
                link = f"https://www.georgetownlawjournal.org{link}"
            
            if title and len(title) > 20:
                articles.append({
                    'title': title,
                    'link': link,
                    'source': 'Georgetown Law Journal',
                    'type': 'research'
                })
    
    return articles[:5]

def main():
    print("="*60)
    print("🔍 T14 Direct Scraper (Backup)")
    print("="*60)
    
    all_articles = []
    
    # Yale Law Journal
    print("\n📄 Fetching Yale Law Journal...")
    html = fetch_page(TARGETS["Yale Law Journal"]["url"])
    if html:
        articles = parse_yale_law_journal(html)
        print(f"  ✓ Found {len(articles)} articles")
        all_articles.extend(articles)
    
    # Berkeley Law Review
    print("\n📄 Fetching Berkeley Law Review...")
    html = fetch_page(TARGETS["Berkeley Law Review"]["url"])
    if html:
        articles = parse_berkeley_law_review(html)
        print(f"  ✓ Found {len(articles)} articles")
        all_articles.extend(articles)
    
    # Georgetown Law Journal
    print("\n📄 Fetching Georgetown Law Journal...")
    html = fetch_page(TARGETS["Georgetown Law Journal"]["url"])
    if html:
        articles = parse_georgetown_law_journal(html)
        print(f"  ✓ Found {len(articles)} articles")
        all_articles.extend(articles)
    
    # 保存结果
    output = {
        "date": datetime.now().isoformat(),
        "total": len(all_articles),
        "articles": all_articles
    }
    
    output_file = Path("/root/.openclaw/workspace/website/brief/content/t14-scrape-results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Saved {len(all_articles)} articles to {output_file}")
    print("\nArticles found:")
    for article in all_articles:
        print(f"  - {article['source']}: {article['title'][:60]}...")

if __name__ == "__main__":
    main()
