# MailPilot Pro — AI 外贸邮件工作台

> 输入产品与客户询盘，一键生成专业英文邮件、中文版本、WhatsApp 话术、报价单。

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Features

- **📧 智能邮件生成** — 支持正式/亲切/简洁三种风格，一键输出英文邮件 + 中文对照 + WhatsApp 话术
- **🔍 询盘分析** — AI 自动分析客户意图、优先级、关键需求，给出回复策略建议
- **📋 报价单生成** — 自动生成专业英文报价单，含产品明细、价格条款、付款方式
- **📦 产品库匹配** — 内置产品数据库，AI 根据询盘自动推荐最匹配的产品
- **🔌 REST API** — 所有功能均提供独立 API 端点，方便集成到第三方系统

## Quick Start

### 本地运行

`ash
# 1. 克隆仓库
git clone https://github.com/cl18603255-glitch/ai-agent-demo.git
cd ai-agent-demo

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key（编辑 .env 文件）
#    OPENAI_API_KEY=sk-xxxxx
#    或
#    DEEPSEEK_API_KEY=sk-xxxxx

# 4. 启动服务
python app.py

# 5. 访问 http://localhost:10000
`

### 一键部署到 Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

点击上方按钮，连接你的 GitHub 仓库即可自动部署。

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | 服务健康检查 |
| POST | /api/analyze | 分析客户询盘 |
| POST | /api/match-products | 匹配推荐产品 |
| POST | /api/generate | 生成全套邮件方案 |
| POST | /api/quotation | 生成报价单 |
| GET | /api/products | 获取产品库列表 |
| POST | /api/products | 添加新产品 |

### API 示例

`ash
# 分析询盘
curl -X POST http://localhost:10000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"inquiry": "We need 500 solar garden lights for UK store. Custom packaging with logo."}'

# 生成邮件方案
curl -X POST http://localhost:10000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"inquiry": "...", "style": "formal"}'
`

## Tech Stack

- **Backend**: Flask + OpenAI API / DeepSeek API
- **Frontend**: Vanilla HTML/CSS/JS
- **Database**: CSV file (可替换为 SQLite/PostgreSQL)
- **Deployment**: Render / Docker

## Product Library

产品库文件位于 products.csv，支持通过 API 动态添加：

| 字段 | 说明 | 示例 |
|------|------|------|
| name | 产品名称 | Solar Garden Light A1 |
| category | 产品类别 | LED照明 |
| price | 价格 | 8.50 |
| moq | 最小起订量 | 100 pcs |
| lead_time | 交货期 | 25 days |
| features | 产品特点 | IP65防水;自动光控 |
| hs_code | HS编码 | 9405.42 |

## License

MIT License
