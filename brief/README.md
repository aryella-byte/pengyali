# Brief | 法律与学术简报

简洁、学术、每日更新的法律与学术简报网站。

## 网站结构

```
brief/
├── index.html          # 主页面
├── data/
│   └── brief-data.json # 数据文件
├── scripts/
│   └── update_brief.py # 自动更新脚本
└── .github/workflows/
    └── update-brief.yml # GitHub Actions自动更新
```

## 核心功能

### 📰 News 栏目
- **来源**: RSS聚合 (SCOTUSblog, Financial Times, Reuters Legal)
- **排序**: 按时间最新倒序排列
- **内容**: 标题、来源、时间、摘要、Why it matters、标签

### 📄 Research 栏目
- **来源**: 美国T14法学院期刊
- **排序**: 知识库式持续更新，新内容追加
- **内容**: 论文标题、作者、期刊、时间、摘要、Why it matters、标签

## 本地测试

```bash
cd brief
# 使用Python简单HTTP服务器测试
python3 -m http.server 8080
# 访问 http://localhost:8080
```

## 手动更新数据

```bash
cd brief/scripts
python3 update_brief.py
```

## 自动更新

已配置GitHub Actions，每天北京时间6点自动：
1. 抓取最新RSS源
2. 更新brief-data.json
3. 自动提交并推送到GitHub

## 部署到GitHub Pages

1. 在仓库Settings > Pages中启用GitHub Pages
2. Source选择"Deploy from a branch"
3. Branch选择"main"，文件夹选择"/(root)"
4. 访问 https://yourusername.github.io/repo-name/brief/

## 自定义配置

修改 `scripts/update_brief.py` 中的：
- `NEWS_SOURCES`: 新闻RSS源
- `RESEARCH_SOURCES`: 研究RSS源
- `TAG_RULES`: 标签分类规则
