#!/usr/bin/env python3
"""
Sort brief-data.json by date (newest first)
Handles various date formats and normalizes them
"""

import json
from datetime import datetime
import re

# Month mapping
MONTH_MAP = {
    'Ja': 1, 'Fe': 2, 'Mr': 3, 'Ap': 4, 'Ma': 5, 'Ju': 6,
    'Jl': 7, 'Au': 8, 'Se': 9, 'Oc': 10, 'No': 11, 'De': 12
}

def parse_date(date_str):
    """Parse various date formats to datetime object"""
    if not date_str:
        return datetime(1970, 1, 1)
    
    # Format: "Thu, 26 Fe" or "Sun, 01 Ma"
    pattern = r'\w+,?\s*(\d+)\s*([A-Za-z]{2})'
    match = re.match(pattern, date_str.strip())
    
    if match:
        day = int(match.group(1))
        month_abbr = match.group(2)
        month = MONTH_MAP.get(month_abbr[:2], 1)
        year = 2026  # Assume current year
        return datetime(year, month, day)
    
    return datetime(1970, 1, 1)

def sort_items_by_date(items):
    """Sort items by date, newest first"""
    return sorted(items, key=lambda x: parse_date(x.get('date', '')), reverse=True)

def main():
    # Read the data
    with open('/root/.openclaw/workspace/website/brief/data/brief-data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Sort news and research
    data['news'] = sort_items_by_date(data.get('news', []))
    data['research'] = sort_items_by_date(data.get('research', []))
    
    # Write back
    with open('/root/.openclaw/workspace/website/brief/data/brief-data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("✅ Sorted brief-data.json by date (newest first)")
    print(f"   News items: {len(data['news'])}")
    print(f"   Research items: {len(data['research'])}")
    
    # Show sorted order
    print("\n📰 News order:")
    for item in data['news'][:5]:
        print(f"   {item.get('date', 'N/A')}: {item.get('titleCN', item.get('title', 'N/A'))[:40]}...")
    
    print("\n📄 Research order:")
    for item in data['research']:
        print(f"   {item.get('date', 'N/A')}: {item.get('titleCN', item.get('title', 'N/A'))[:40]}...")

if __name__ == '__main__':
    main()
