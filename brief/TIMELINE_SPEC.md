# Brief Timeline Feature

## Overview
Add a chronological timeline view that groups content by date, showing what was updated each day.

## Implementation

### 1. Add Timeline Navigation Tab

In the nav-tabs section, add:
```html
<button onclick="switchTab('timeline')">Timeline</button>
```

### 2. Add Timeline Section HTML

```html
<!-- Timeline Section -->
<div id="timeline" class="section">
    <div class="section-header">
        <h2 data-zh="📅 时间轴" data-en="📅 Timeline">📅 时间轴</h2>
        <p data-zh="按日期查看每日更新 | View updates by date" data-en="View updates chronologically | 按日期查看每日更新">按日期查看每日更新 | View updates by date</p>
    </div>
    <div id="timeline-content"></div>
</div>
```

### 3. Add Timeline Styles

```css
/* Timeline Styles */
.timeline-date {
    margin-bottom: 30px;
    padding-left: 20px;
    border-left: 3px solid var(--accent);
}

.timeline-date-header {
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--accent);
    margin-bottom: 15px;
    padding: 8px 0;
}

.timeline-items {
    padding-left: 15px;
}

.timeline-item {
    margin-bottom: 20px;
    padding: 15px;
    background: var(--card);
    border-radius: 8px;
    border: 1px solid var(--border);
}

.timeline-item-type {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--secondary);
    text-transform: uppercase;
    margin-bottom: 8px;
}

.timeline-item-type.news { color: #8B0000; }
.timeline-item-type.research { color: #0066cc; }
```

### 4. Add JavaScript Function

```javascript
// Group items by date
function groupByDate(items, type) {
    const grouped = {};
    items.forEach(item => {
        const date = item.date || 'Unknown';
        if (!grouped[date]) {
            grouped[date] = [];
        }
        grouped[date].push({...item, type});
    });
    return grouped;
}

// Render Timeline
function renderTimeline() {
    const container = document.getElementById('timeline-content');
    
    // Group all items by date
    const newsByDate = groupByDate(briefData.news || [], 'news');
    const researchByDate = groupByDate(briefData.research || [], 'research');
    
    // Merge and sort dates
    const allDates = [...new Set([...Object.keys(newsByDate), ...Object.keys(researchByDate)])];
    allDates.sort((a, b) => parseDate(b) - parseDate(a)); // Newest first
    
    if (allDates.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>暂无更新 | No updates</p></div>';
        return;
    }
    
    container.innerHTML = allDates.map(date => {
        const newsItems = newsByDate[date] || [];
        const researchItems = researchByDate[date] || [];
        const allItems = [...newsItems, ...researchItems];
        
        const itemsHtml = allItems.map(item => {
            const title = currentLang === 'zh' ? (item.titleCN || item.title) : item.title;
            const typeLabel = item.type === 'news' 
                ? (currentLang === 'zh' ? '📰 新闻' : '📰 News')
                : (currentLang === 'zh' ? '📚 研究' : '📚 Research');
            
            return `
                <div class="timeline-item">
                    <div class="timeline-item-type ${item.type}">${typeLabel}</div>
                    <h4 class="item-title" style="font-size: 1rem; margin-bottom: 8px;">
                        <a href="${item.url}" target="_blank">${title}</a>
                    </h4>
                    <div class="item-meta">
                        <span>${item.source || item.journal}</span>
                    </div>
                </div>
            `;
        }).join('');
        
        return `
            <div class="timeline-date">
                <div class="timeline-date-header">${date}</div>
                <div class="timeline-items">
                    ${itemsHtml}
                </div>
            </div>
        `;
    }).join('');
}
```

### 5. Update renderContent function

```javascript
function renderContent() {
    renderNews();
    renderResearch();
    renderTimeline();
}
```

## Date Format to Handle
- "Sun, 01 Ma" → March 1
- "Thu, 26 Fe" → February 26
- "Wed, 11 Fe" → February 11

## View Toggle Options
1. **List View** (current): Chronological list with full content
2. **Timeline View** (new): Grouped by date, compact display
3. **Research View**: Separate research papers section

## Benefits
- Quick scan of daily updates
- See what's new at a glance
- Track content addition patterns
