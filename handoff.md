# MailPilot Pro - Project Handoff Document

## Overview

**Project Name:** MailPilot Pro (AI Foreign Trade Email Workbench)
**Version:** v3.0
**Deploy URL:** https://ai-agent-demo-1.onrender.com
**GitHub Repo:** https://github.com/cl18603255-glitch/ai-agent-demo

One-liner: Input product and customer inquiry, generate professional English emails, Chinese versions, WhatsApp scripts, and quotations instantly. Supports user registration, login, recharge, and auto-deduction.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend Framework | Flask (Python 3.11+) |
| AI Service | OpenAI API (gpt-4o-mini) / DeepSeek API |
| Database | SQLite (mailpilot.db) |
| Auth | JWT Token (custom session tokens) |
| Frontend | Vanilla HTML/CSS/JavaScript |
| Deployment | Render (Free tier) |
| Web Server | Gunicorn |

---

## File Structure

`
ai-agent-demo/
├── app.py                    # Main Flask app + API routes + billing logic
├── auth.py                   # User auth module (register/login/password hash/JWT)
├── user_api.py               # User-related APIs (profile/recharge/orders/usage stats)
├── products.csv              # Sample product catalog data
├── mailpilot.db              # SQLite database (auto-generated at runtime)
├── requirements.txt          # Python dependencies
├── gunicorn.conf.py          # Gunicorn config (reads PORT env var)
├── Dockerfile                # Docker build file
├── render.yaml               # Render deployment config
├── README.md                 # Project documentation
├── templates/
│   └── index.html            # Frontend page (user system UI + tab switching)
└── handoff.md                # This handoff document
`

---

## Core Features

### 1. AI Email Generation
- **Path**: / (Homepage Tab 1)
- **Function**: Input product + customer background, AI generates English email + Chinese version + WhatsApp script
- **Styles**: Formal / Friendly / Concise
- **Cost**: 2 RMB per generation

### 2. Inquiry Analysis
- **Path**: /api/analyze
- **Function**: Auto-detect customer intent, priority, key requirements, reply strategy
- **Cost**: 0.5 RMB per analysis

### 3. Quotation Generation
- **Path**: /api/quotation
- **Function**: Generate professional English quotation (with quote number, product table, payment terms, etc.)
- **Cost**: 1.5 RMB per quotation

### 4. Product Library Management
- **Path**: /api/products
- **Function**: View product list, add new products via POST API
- **Format**: CSV file (products.csv)

### 5. User System
- **Register**: POST /api/user/register — New users get 100 RMB free credit
- **Login**: POST /api/user/login — Returns JWT token
- **Profile**: GET/PUT /api/user/profile
- **Change Password**: POST /api/user/change-password

### 6. Recharge System
- **Plans List**: GET /api/user/plans
  - Basic: Pay 50 → Get 55
  - Standard: Pay 100 → Get 115 (Popular)
  - Pro: Pay 300 → Get 360
  - Enterprise: Pay 1000 → Get 1300
- **Create Order**: POST /api/user/order/create
- **Payment Callback**: POST /api/user/order/callback (simulated WeChat/Alipay QR scan)
- **Query Status**: GET /api/user/order/status/<transaction_id>

### 7. Usage Statistics
- **Path**: GET /api/user/usage
- **Data**: Total requests, today/monthly count, cumulative cost, recent usage history

---

## Environment Variables (Render Dashboard)

Add these in Render's Environment tab:

| Variable | Value | Required |
|----------|-------|----------|
| OPENAI_API_KEY | Your OpenAI API Key | Yes |
| AI_MODEL | gpt-4o-mini | No (default) |
| PORT | 10000 | Yes |

WARNING: Never commit API keys to Git! Render encrypts environment variables automatically.

---

## Deployment Steps

### Local Development
`ash
cd ai-agent-demo
pip install -r requirements.txt
python app.py
# Visit http://localhost:10000
`

### Render Deployment
1. GitHub Repo: cl18603255-glitch/ai-agent-demo
2. Branch: main
3. Build Command: (empty)
4. Start Command: gunicorn -c gunicorn.conf.py app:app
5. Runtime: Python 3
6. Instance Type: Free

After deployment, visit: https://ai-agent-demo-1.onrender.com

---

## Security Notes

1. API Key stored in Render environment variables, NOT in code
2. Password hashing: PBKDF2-SHA256 with salt, 100k iterations
3. Session tokens expire after 24 hours
4. SQL injection protected via parameterized queries
5. Rate limiting removed (caused issues previously)

---

## Known Issues & Lessons Learned

### Fixed
1. onclick events missing quotes -> buttons unclickable (fixed v3.0)
2. render.yaml contained API Key -> GitHub security scan blocked push (fixed)
3. inspect.py filename conflict -> collided with Python stdlib inspect module (fixed)
4. @billable decorator missing functools.wraps -> Flask route conflict 400 error
5. Flask debug reloader state management -> removed rate_limit decorator
6. Render using python app.py instead of gunicorn -> fixed gunicorn.conf.py

### To Do
1. No RAG implementation yet
2. Real WeChat/Alipay payment integration pending
3. No WebSocket for real-time notifications
4. No CAPTCHA protection
5. Free instance spins down after 15min idle -> 50s cold start delay

---

## Business Model

| Revenue Source | Pricing | Notes |
|---------------|---------|-------|
| Pay-per-use | Email 2RMB / Inquiry 0.5RMB / Quotation 1.5RMB | Deducted from user balance |
| Recharge packages | 5% to 30% bonus | Improves retention |
| Enterprise custom | 5000-50000 RMB/project | Private deployment + custom features |
| SaaS subscription | 99-299 RMB/month | Unlimited usage + dedicated support |

---

## Contact

- **Email**: cl18603255@gmail.com
- **GitHub**: https://github.com/cl18603255-glitch
- **Demo**: https://ai-agent-demo-1.onrender.com

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-07-16 | v1.0 | Initial version: Foreign trade email generator (Flask + DeepSeek) |
| 2026-07-17 | v2.0 | Added product matching, multi-style emails, quotation generation |
| 2026-07-17 | v3.0 | USER SYSTEM LAUNCHED: Registration/login/recharge/billing/usage stats |

---

Last Updated: 2026-07-22
