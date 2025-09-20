# AI驱动的每日新闻汇总器

一个基于AI的智能内容聚合系统，能够自动从多个推荐网站抓取最新内容并生成统一的日报文档。

## 🌟 核心特性

- **AI智能提取**: 使用OpenAI GPT-4o-mini理解网页语义，自动提取推荐内容
- **零配置扩展**: 添加新网站只需在配置文件中添加URL，无需编写代码
- **Python差异检测**: 高效的内容对比算法，只处理新增项目
- **GitHub Actions自动化**: 定时运行，自动生成并提交更新
- **RSS友好**: 生成的Markdown文件适合RSS订阅

## 🏗️ 工作原理

```
网站URL → requests获取 → AI提取内容 → JSON结构化 → Python差异检测 → Markdown生成
```

### 技术栈
- **网页获取**: requests + 重试机制
- **内容理解**: OpenAI GPT-4o-mini
- **差异检测**: Python hashlib
- **输出格式**: Markdown
- **自动化**: GitHub Actions

## 📁 项目结构

```
daily-news-aggregator/
├── .github/workflows/
│   └── generate_daily_digest.yml    # GitHub Actions工作流
├── scripts/
│   ├── daily_aggregator.py          # 主聚合器
│   ├── ai_content_extractor.py      # AI内容提取器
│   ├── test_real_workflow.py        # 测试脚本
│   ├── prompt_templates/
│   │   └── content_extraction.txt   # AI提取prompt模板
│   └── utils/
│       ├── content_differ.py        # 差异检测器
│       └── digest_generator.py      # Markdown生成器
├── config/
│   └── sources.json                 # 网站配置
├── data/
│   ├── daily-digest/               # 每日汇总输出
│   └── state/                      # 状态文件
└── requirements.txt                # Python依赖
```

## 🚀 快速开始

### 1. 环境配置

在GitHub仓库的Settings > Secrets中添加：
```
OPENAI_API_KEY: 你的OpenAI API密钥
OPENAI_BASE_URL: 自定义OpenAI API地址（可选）
```

**OPENAI_BASE_URL说明**：
- 可选配置，如果不设置则使用官方API
- 支持自建代理或第三方兼容服务
- 示例：`https://api.openai-proxy.com/v1`

### 2. 添加新网站

编辑 `config/sources.json`：
```json
{
  "sources": [
    {
      "name": "example",
      "display_name": "示例网站",
      "base_url": "https://example.com/archives/",
      "url_pattern": "{year}{month:02d}-recommendations.html",
      "icon": "🔥",
      "enabled": true
    }
  ]
}
```

**URL模式说明**：
- `{year}`: 当前年份 (如: 2025)
- `{month}`: 当前月份 (如: 9)
- `{month:02d}`: 补零的月份 (如: 09)

**示例**：
- 海阔世界: `{year}nian{month}yuetuijian` → `2025nian9yuetuijian`
- 爱优不错: `{year}{month:02d}.html` → `202509.html`

### 3. 运行方式

#### GitHub Actions自动运行
- 每6小时自动检查更新
- 手动触发：在Actions页面点击"Run workflow"

#### 本地测试
```bash
cd daily-news-aggregator
pip install -r requirements.txt
python scripts/test_real_workflow.py
```

## 📊 输出格式

生成文件格式：`daily-digest-YYYY-MM-DD.md`

```markdown
# 每日发现汇总 - 2024-09-20

> 本文档汇总了今日各大推荐网站的新增内容

## 📱 海阔世界 (haikuoshijie)

### [项目名称](链接)
项目描述内容

### [另一个项目](链接)
项目描述内容

---
**更新时间**: 2024-09-20 15:00:00
**数据源**: 1个网站
**新增项目**: 2个
```

## 🎯 关键优势

1. **真正的零配置扩展**
   - 新增网站只需修改JSON配置
   - AI自动适应不同网站结构
   - 无需编写解析代码

2. **智能内容理解**
   - AI理解页面语义，不依赖HTML结构
   - 自动过滤无关内容（导航、广告等）
   - 提取置信度评分

3. **高效差异检测**
   - 基于内容hash的快速对比
   - 智能识别新增vs更新内容
   - 支持日期和置信度过滤

4. **完全自动化**
   - GitHub Actions定时执行
   - 自动提交新内容到Git
   - 支持手动触发

## 🔧 配置选项

### AI配置
```json
{
  "ai_config": {
    "model": "gpt-4o-mini",          // OpenAI模型名称
    "max_tokens": 3000,              // 最大响应长度
    "temperature": 0.1,              // 创造性参数(0-1)
    "min_confidence": 0.7            // 最低置信度阈值
  }
}
```

**支持的模型**：
- `gpt-4o-mini`: 经济高效，适合大批量处理
- `gpt-4o`: 更强性能，成本较高
- `gpt-3.5-turbo`: 经济选择
- 其他OpenAI兼容模型

## 📈 监控和日志

- GitHub Actions提供详细的执行日志
- 每次运行显示提取统计信息
- 错误处理和重试机制
- 状态文件记录历史数据

## 🔒 安全性

- 不保存敏感信息到代码仓库
- API密钥通过GitHub Secrets管理
- 请求头模拟真实浏览器
- 包含重试和错误处理机制

## 🎉 RSS订阅

生成的文件可通过GitHub RSSHub订阅：
- 订阅路径：`/github/file/用户名/仓库名/daily-news-aggregator/data/daily-digest`
- 文件格式：标准Markdown，包含完整链接
- 更新频率：每6小时检查

## 📄 许可证

基于原项目的MIT许可证开源。