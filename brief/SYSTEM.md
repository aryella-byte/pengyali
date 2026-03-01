# Auto Brief System - 全自动简报系统

## 🎯 设计原则

**完全自动化** - 无需人工干预，每天自动生成、更新、发布

## 📁 系统组件

```
/brief/
├── index.html                    # 主页面 (自动生成)
├── content/
│   └── article-history.json      # 文章去重历史
├── scripts/
│   ├── auto_brief.py            # 主自动化脚本 ⭐
│   ├── monitor_t14.py           # T14监控 (备用)
│   └── update_brief.py          # 更新脚本 (旧版)
└── SYSTEM.md                    # 本文档
```

## 🤖 自动流程

### 每天 06:00 CST 执行：

1. **抓取信源**
   - News: SCOTUSblog, Financial Times, Reuters Legal
   - Research: Harvard, Michigan, Virginia, Stanford, Columbia Law Reviews

2. **智能筛选**
   - 去重检查 (article-history.json)
   - 关键词评分 (Criminal Justice 最高优先级)
   - 选取得分最高的3篇news + 3篇research

3. **内容生成**
   - 自动提取摘要
   - 分类标签 (Criminal Justice / Constitutional / Tech / International)
   - 自动生成 "Why this matters"

4. **页面构建**
   - 生成完整HTML (NEWS + RESEARCH 双板块)
   - 中英双语支持
   - 更新时间戳

5. **自动发布**
   - git add → commit → push
   - 推送至 GitHub Pages

## 🔧 配置参数

### 关键词权重
```python
# 刑事司法 (最高优先级 10)
"criminal": 10, "sentencing": 10, "prison": 10
"incarceration": 10, "mass incarceration": 10
"policing": 9, "jury": 8, "fourth amendment": 8

# 宪法/权利 (6-7)
"constitutional": 6, "civil rights": 6, "due process": 7

# 科技/隐私 (4-5)
"technology": 4, "AI": 5, "privacy": 5
```

### 信源配置
```python
SOURCES = {
    "SCOTUSblog": {"type": "news", "priority": ["supreme court", "constitutional"]},
    "Harvard Law Review": {"type": "research", "focus": ["criminal", "constitutional"]},
    # ...
}
```

## 📝 "Why this matters" 生成规则

根据分类自动选择模板：

| 分类 | 模板示例 |
|------|---------|
| Criminal Justice | "This directly addresses systemic issues in criminal justice..." |
| Constitutional | "This analysis illuminates evolving constitutional doctrine..." |
| Technology | "As technology outpaces legal frameworks..." |
| International | "This development carries significant implications for international law..." |

## ⏰ 定时任务

```
名称: auto-brief-daily
时间: 每天 06:00 (Asia/Shanghai)
命令: python3 auto_brief.py
状态: ✅ 已激活
```

## 🔄 手动执行

```bash
cd /root/.openclaw/workspace/website/brief/scripts
python3 auto_brief.py
```

## 📊 输出示例

```
==================================================
🤖 Auto Brief Generator
==================================================

📚 Tracking 156 articles
  ✓ SCOTUSblog: 2 new
  ✓ Financial Times: 1 new
  ✓ Harvard Law Review: 2 new
  ✓ Michigan Law Review: 1 new
  ...

📰 Selected 3 news items
📄 Selected 3 research items

✅ Generated: /brief/index.html
  ✓ Committed and pushed to GitHub

🎉 Auto-update completed successfully!
```

## 🔍 故障排查

### RSS源失败
- 检查网络连接
- 验证RSS URL是否有效
- 查看脚本输出中的错误信息

### Git推送失败
- 检查GitHub token是否过期
- 验证仓库权限
- 手动运行 `git push` 查看详细错误

### 内容质量问题
- 调整KEYWORDS权重
- 修改模板文本
- 添加/移除信源

## 📈 未来优化

- [ ] 添加更多T14期刊 (Yale, Berkeley需爬取)
- [ ] 接入翻译API生成中文内容
- [ ] 添加文章图片自动提取
- [ ] 集成更多新闻源 (WaPo, NYT Law)

---

*系统版本: 1.0*
*创建时间: 2026-03-02*
