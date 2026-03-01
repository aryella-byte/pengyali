#!/usr/bin/env python3
"""
Apify T14 Scraper - 抓取无RSS的T14法学院期刊
- Yale Law Journal
- Berkeley Law Review  
- Georgetown Law Journal
"""

import json
import requests
from datetime import datetime
from pathlib import Path

# Apify配置
APIFY_TOKEN = ""  # 需要填写
APIFY_BASE_URL = "https://api.apify.com/v2"

# 需要爬取的T14期刊（无RSS）
T14_SCRAPE_TARGETS = {
    "Yale Law Journal": {
        "url": "https://www.yalelawjournal.org/",
        "start_urls": [{"url": "https://www.yalelawjournal.org/"}],
        "link_selector": "a[href*='/article/']",
        "article_selector": "article, .article, .post"
    },
    "Berkeley Law Review": {
        "url": "https://www.boalt.org/",
        "start_urls": [{"url": "https://www.boalt.org/"}],
        "link_selector": "a[href*='/article/']",
        "article_selector": "article, .article-content"
    },
    "Georgetown Law Journal": {
        "url": "https://www.georgetownlawjournal.org/",
        "start_urls": [{"url": "https://www.georgetownlawjournal.org/"}],
        "link_selector": "a[href*='/article/']",
        "article_selector": "article, .article"
    }
}

def run_apify_actor(actor_id, input_data):
    """运行Apify Actor"""
    url = f"{APIFY_BASE_URL}/acts/{actor_id}/runs"
    headers = {
        "Authorization": f"Bearer {APIFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=input_data)
    if response.status_code == 201:
        return response.json()["data"]["id"]
    else:
        print(f"  ✗ Failed to start actor: {response.text}")
        return None

def get_run_results(run_id):
    """获取运行结果"""
    url = f"{APIFY_BASE_URL}/actor-runs/{run_id}/dataset/items"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def scrape_with_website_content_crawler(target_name, target_config):
    """使用apify/website-content-crawler抓取"""
    print(f"  Scraping {target_name}...")
    
    input_data = {
        "startUrls": target_config["start_urls"],
        "maxCrawlPages": 10,
        "maxConcurrency": 5,
        "maxDepth": 2,
        "linkSelector": target_config["link_selector"],
        "pageFunction": """
        async function pageFunction(context) {
            const { page, request } = context;
            const title = await page.title();
            const content = await page.$eval('article, .article, .post, .article-content', 
                el => el.innerText).catch(() => '');
            return {
                url: request.url,
                title: title,
                content: content.substring(0, 1000),
                source: 'TARGET_NAME'
            };
        }
        """.replace('TARGET_NAME', target_name)
    }
    
    run_id = run_apify_actor("apify/website-content-crawler", input_data)
    if run_id:
        print(f"    Started run: {run_id}")
        # 等待完成（简化版，实际需要轮询状态）
        import time
        time.sleep(30)  # 等待30秒
        results = get_run_results(run_id)
        return results
    return []

def main():
    print("="*60)
    print("🔍 Apify T14 Scraper")
    print("="*60)
    
    if not APIFY_TOKEN:
        print("\n⚠️  请先在 https://console.apify.com/account/integrations 获取API token")
        print("   然后填入 APIFY_TOKEN 变量")
        return
    
    all_articles = []
    for name, config in T14_SCRAPE_TARGETS.items():
        articles = scrape_with_website_content_crawler(name, config)
        print(f"  ✓ {name}: {len(articles)} articles")
        all_articles.extend(articles)
    
    # 保存结果
    output_file = Path("/root/.openclaw/workspace/website/brief/content/apify-t14-results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "date": datetime.now().isoformat(),
            "articles": all_articles
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Saved {len(all_articles)} articles to {output_file}")

if __name__ == "__main__":
    main()
